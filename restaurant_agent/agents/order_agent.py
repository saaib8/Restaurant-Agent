"""
Order Agent - Takes orders from customers
"""
import logging
from typing import Annotated
from pydantic import Field
from livekit.agents.llm import function_tool
from .base_agent import BaseAgent, RunContext_T
from ..services.database import MongoDB
from ..services.menu_service import MenuService
from datetime import datetime

logger = logging.getLogger("restaurant-agent")


class OrderAgent(BaseAgent):
    """Order taking agent - handles customer orders"""
    
    def __init__(self, menu_text: str) -> None:
        super().__init__(
            instructions=(
                "You are an experienced order taker at a multi-cuisine restaurant.\n\n"
                f"{menu_text}\n\n"
                "CRITICAL RULES:\n"
                "1. When customer asks about Pakistani/Chinese/Continental/Fast Food, "
                "YOU MUST use the show_category_items tool immediately.\n"
                "2. NEVER list items from memory - ALWAYS call show_category_items tool first.\n"
                "3. Example: Customer says 'Chinese food' → Call show_category_items(category='chinese_main')\n\n"
                "ORDERING FLOW:\n"
                "1. Ask for customer's name and phone number\n"
                "2. Ask: 'We have Pakistani, Chinese, Continental, and Fast Food. Which would you like?'\n"
                "3. When they choose, use show_category_items tool to display options\n"
                "4. After main items, ask: 'Would you like any drinks?' → Use show_category_items(category='drinks')\n"
                "5. After drinks, ask: 'Any dessert?' → Use show_category_items(category='desserts')\n"
                "6. Summarize and confirm order\n\n"
                "VOICE FORMATTING:\n"
                "- This is a VOICE conversation, NOT text\n"
                "- NEVER use markdown formatting like **bold** or *italic*\n"
                "- NEVER use special characters: *, #, _, etc.\n"
                "- Speak naturally, as if talking to someone in person\n"
                "- Say 'rupees' not 'R S' or 'Rs'\n"
                "- Example: Say '1040 rupees' NOT '**1040 rupees**'"
            ),
        )
        self.menu_text = menu_text
        self.menu_service = MenuService()
    
    @function_tool()
    async def show_category_items(
        self,
        category: Annotated[str, Field(description="Category name: biryani, karahi, bbq, curry, fried_rice, noodles, chinese_main, pasta, steaks, pizza, burgers, fast_food, bread, drinks, desserts")],
        context: RunContext_T,
    ) -> str:
        """
        Show items from a specific category to the customer.
        ALWAYS use this tool when customer asks about:
        - Pakistani food → Use: biryani, karahi, bbq, or curry
        - Chinese food → Use: fried_rice, noodles, or chinese_main
        - Continental food → Use: pasta, steaks, or pizza
        - Fast Food → Use: burgers or fast_food
        - Drinks → Use: drinks
        - Desserts → Use: desserts
        
        This will return the complete list with prices.
        """
        logger.info(f"📋 Showing category: {category}")
        category_items = self.menu_service.get_category_description(category)
        
        if "not available" in category_items.lower():
            # Try to find related categories
            if "chinese" in category.lower():
                return "Let me show you our Chinese options:\n\n" + \
                       self.menu_service.get_category_description("chinese_main")
            elif "continental" in category.lower():
                return "Let me show you our Continental options:\n\n" + \
                       self.menu_service.get_category_description("pasta")
            elif "pakistani" in category.lower():
                return "Let me show you our Pakistani options:\n\n" + \
                       self.menu_service.get_category_description("biryani")
        
        return category_items
    
    @function_tool()
    async def update_customer_name(
        self,
        name: Annotated[str, Field(description="Customer's name")],
        context: RunContext_T,
    ) -> str:
        """
        Update customer's name.
        Call this when customer provides their name.
        """
        userdata = context.userdata
        userdata.customer_name = name
        logger.info(f"📝 Customer name: {name}")
        return f"Thank you, {name}! Your name has been recorded."
    
    @function_tool()
    async def update_customer_phone(
        self,
        phone: Annotated[str, Field(description="Customer's phone number")],
        context: RunContext_T,
    ) -> str:
        """
        Update customer's phone number.
        Call this when customer provides their phone number.
        Confirm the number before calling this function.
        """
        userdata = context.userdata
        userdata.customer_phone = phone
        logger.info(f"📞 Customer phone: {phone}")
        
        # Check if returning customer
        customer_data = await MongoDB.get_customer_by_phone(phone)
        if customer_data:
            name = customer_data.get("name", "")
            total_orders = customer_data.get("total_orders", 0)
            return f"Welcome back! We have you on record. You've ordered {total_orders} times before. Great to have you again!"
        
        return f"Phone number {phone} recorded. This is your first order with us!"
    
    @function_tool()
    async def add_item_to_order(
        self,
        context: RunContext_T,
        item_name: Annotated[str, Field(description="Name of the menu item")],
        quantity: Annotated[int, Field(description="Quantity")] = 1,
        special_instructions: Annotated[str, Field(description="Special instructions (optional)")] = "",
    ) -> str:
        """
        Add an item to the customer's order.
        Call this after confirming the item and quantity with the customer.
        """
        userdata = context.userdata
        
        logger.info(f"🔍 Searching for item: '{item_name}' (quantity: {quantity})")
        
        # Search for item in menu
        items = self.menu_service.search_items(item_name)
        if not items:
            logger.warning(f"❌ Item not found: '{item_name}'")
            return f"Sorry, I couldn't find '{item_name}' on our menu. Could you please choose from the available items?"
        
        item = items[0]  # Take first match
        logger.info(f"✅ Found item: {item.name} (ID: {item.id}, Price: Rs. {item.price})")
        
        # Add to order
        order_item = {
            "item_id": item.id,
            "item_name": item.name,
            "quantity": quantity,
            "price": item.price,
            "special_instructions": special_instructions or None,
            "subtotal": item.price * quantity
        }
        
        userdata.order_items.append(order_item)
        userdata.total_amount += order_item["subtotal"]
        
        logger.info(f"➕ Added {quantity}x {item.name} to order")
        
        return (
            f"Added {quantity}x {item.name} ({item.price:.0f} rupees each) to your order. "
            f"Subtotal: {order_item['subtotal']:.0f} rupees. "
            f"Current total: {userdata.total_amount:.0f} rupees"
        )
    
    @function_tool()
    async def remove_item_from_order(
        self,
        item_name: Annotated[str, Field(description="Name of the item to remove")],
        context: RunContext_T,
    ) -> str:
        """
        Remove an item from the order.
        Call this when customer wants to remove something.
        """
        userdata = context.userdata
        
        # Find and remove item
        for i, order_item in enumerate(userdata.order_items):
            if item_name.lower() in order_item["item_name"].lower():
                removed = userdata.order_items.pop(i)
                userdata.total_amount -= removed["subtotal"]
                logger.info(f"➖ Removed {removed['item_name']} from order")
                return f"Removed {removed['item_name']} from your order. New total: {userdata.total_amount:.0f} rupees"
        
        return f"I couldn't find '{item_name}' in your current order."
    
    @function_tool()
    async def show_current_order(self, context: RunContext_T) -> str:
        """
        Show the customer their current order summary.
        Call this when customer asks 'what did I order' or wants to review.
        """
        userdata = context.userdata
        
        if not userdata.order_items:
            return "Your order is currently empty. What would you like to add?"
        
        summary = "Here's your current order:\n\n"
        for item in userdata.order_items:
            summary += f"{item['quantity']}x {item['item_name']} - {item['subtotal']:.0f} rupees\n"
            if item.get('special_instructions'):
                summary += f"  Note: {item['special_instructions']}\n"
        
        summary += f"\nTotal: {userdata.total_amount:.0f} rupees"
        
        return summary
    
    @function_tool()
    async def confirm_order(self, context: RunContext_T) -> str:
        """
        Confirm and save the order to database.
        Call this ONLY after customer explicitly confirms they're done ordering.
        """
        userdata = context.userdata
        
        if not userdata.customer_phone:
            return "I need your phone number before confirming the order. What's your phone number?"
        
        if not userdata.order_items:
            return "Your order is empty. Please add some items first."
        
        # Save to database
        order_data = {
            "phone": userdata.customer_phone,
            "customer_name": userdata.customer_name,
            "items": userdata.order_items,
            "total_amount": userdata.total_amount,
            "status": "confirmed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        saved = await MongoDB.save_order(order_data)
        
        if saved:
            logger.info(f"✅ Order confirmed for {userdata.customer_phone}")
            return (
                f"Your order has been confirmed! "
                f"Total: {userdata.total_amount:.0f} rupees. "
                f"We'll prepare it right away. Thank you for your order!"
            )
        else:
            logger.warning(f"⚠️  Order saved locally but not in database")
            return (
                f"Your order is confirmed! Total: {userdata.total_amount:.0f} rupees. "
                f"Thank you!"
            )
    
    @function_tool()
    async def to_greeter(self, context: RunContext_T) -> tuple:
        """
        Transfer back to greeter agent.
        Call this if customer wants to start over or asks unrelated questions.
        """
        return await self._transfer_to_agent("greeter", context)

