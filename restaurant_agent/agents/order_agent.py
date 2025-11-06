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
                "You are an experienced order taker at a fast food restaurant.\n\n"
                f"{menu_text}\n\n"
                "CRITICAL RULES:\n"
                "1. If customer mentions a SPECIFIC ITEM (like 'Sprite', 'Pepperoni Pizza', 'Zinger Burger'), "
                "ADD IT DIRECTLY to their order using add_item_to_order.\n"
                "2. If customer mentions a CATEGORY (like 'drinks', 'pizza', 'burgers'), "
                "show them options using show_category_items.\n"
                "3. If customer says they're unsure, show category items.\n\n"
                "Examples:\n"
                "- Customer: 'I want Sprite' → Call add_item_to_order(item_name='Sprite', quantity=1)\n"
                "- Customer: 'Show me drinks' → Call show_category_items(category='drinks')\n"
                "- Customer: 'What pizza do you have?' → Call show_category_items(category='pizza')\n"
                "- Customer: 'Pepperoni Pizza' → Call add_item_to_order(item_name='Pepperoni Pizza', quantity=1)\n\n"
                "ORDERING FLOW:\n"
                "1. Ask for customer's name and phone number\n"
                "2. Ask: 'What would you like? We have Pizza, Burgers, Sandwiches, Fried Chicken, Fries, Drinks, and Sweets.'\n"
                "3. If they name a specific item, add it. If they ask about a category, show options.\n"
                "4. After main items, ask: 'Would you like any drinks?'\n"
                "   - If they say specific drink, add it directly\n"
                "   - If they say 'yes' or 'what do you have?', show drinks category\n"
                "5. After drinks, ask: 'Any dessert or sweets?'\n"
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
        category: Annotated[str, Field(description="Category name: pizza, burger, sandwich, fried_chicken, fries, drinks, sweets")],
        context: RunContext_T,
    ) -> str:
        """
        Show items from a specific category to the customer.
        ALWAYS use this tool when customer asks about:
        - Pizza → Use: pizza
        - Burgers → Use: burger
        - Sandwiches → Use: sandwich
        - Fried Chicken (wings, nuggets, strips, buckets) → Use: fried_chicken
        - Fries (regular, loaded, wedges, onion rings) → Use: fries
        - Drinks → Use: drinks
        - Sweets/Desserts → Use: sweets
        
        This will return the complete list with prices.
        """
        logger.info(f"📋 Showing category: {category}")
        category_items = self.menu_service.get_category_description(category)
        
        if "not available" in category_items.lower():
            # Try to find related categories
            if "chicken" in category.lower():
                return "Let me show you our Fried Chicken options:\n\n" + \
                       self.menu_service.get_category_description("fried_chicken")
            elif "burger" in category.lower():
                return "Let me show you our Burgers:\n\n" + \
                       self.menu_service.get_category_description("burger")
            elif "dessert" in category.lower() or "sweet" in category.lower():
                return "Let me show you our Sweets:\n\n" + \
                       self.menu_service.get_category_description("sweets")
        
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

        
        return f"Phone number {phone} recorded."
    
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
            return f"I apologize, but we don't have {item_name} on our menu currently. Would you like me to show you what we have available?"
        
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
        
        return f"I don't see {item_name} in your current order. Would you like me to review what's in your order?"
    
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

