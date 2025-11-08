"""
Order Agent - Takes orders from customers
"""
import logging
import re
from typing import Annotated
from pydantic import Field
from livekit.agents.llm import function_tool
from .base_agent import BaseAgent, RunContext_T
from ..services.database import MongoDB
from ..services.menu_service import MenuService
from ..helpers.stt_corrections import correct_menu_item_name
from datetime import datetime

logger = logging.getLogger("restaurant-agent")

# Constants
MAX_QUANTITY_PER_ITEM = 20  


def normalize_phone_number(phone_str: str) -> str:
    """Convert spoken phone number words to digits"""
    word_to_digit = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'oh': '0', 'o': '0'
    }
    
    phone_lower = phone_str.lower().strip()
    words = phone_lower.split()
    
    digits = []
    i = 0
    while i < len(words):
        word = words[i]
        
        if word in ['double', 'triple'] and i + 1 < len(words):
            next_word = words[i + 1]
            if next_word in word_to_digit:
                digit = word_to_digit[next_word]
                if word == 'double':
                    digits.append(digit * 2)  
                elif word == 'triple':
                    digits.append(digit * 3)  
                i += 2  
                continue
        
        if word in word_to_digit:
            digits.append(word_to_digit[word])
        elif word.isdigit():
            digits.append(word)
        
        i += 1
    
    phone_number = ''.join(digits)
    
    phone_number = re.sub(r'\D', '', phone_number)
    
    return phone_number



class OrderAgent(BaseAgent):
    """Order taking agent"""
    
    def __init__(self, menu_text: str) -> None:
        super().__init__(
            instructions=(
                "You are an experienced order taker at a fast food restaurant. First Say Welcome to ordering service and then ask: 'May I have your name please?'\n\n"
                f"{menu_text}\n\n"
                "CRITICAL ORDERING RULES - FOLLOW STRICTLY:\n"
                "1. QUANTITY EXTRACTION - CRITICAL:\n"
                "   When customer says: 'thirty pepperoni pizza' or 'five sprite' or '2 burgers'\n"
                "   - Extract the QUANTITY NUMBER: thirty=30, five=5, 2=2, etc.\n"
                "   - Extract the ITEM NAME: 'pepperoni pizza', 'sprite', 'burgers'\n"
                "   - REMOVE quantity words from item_name before searching!\n"
                "   - Common quantity words: one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve, etc.\n"
                "   - Also: 1, 2, 3, 4, 5, 20, 30, hundred, etc.\n\n"
                "2. When customer mentions ANY food item:\n"
                "   - Generic category ONLY ('chicken', 'burger', 'pizza', 'drinks') → Call show_category_items\n"
                "   - ANY specific item/dish name ('Grill Chicken Sandwich', 'Sprite', 'Zinger Burger') → MUST call search_and_suggest_item FIRST\n"
                "   - NEVER EVER call add_item_to_order without calling search_and_suggest_item first!\n"
                "   - NEVER EVER add items without explicit customer confirmation (yes/yeah/sure/okay/definitely)!\n\n"
                "3. MANDATORY TWO-STEP PROCESS for ALL items:\n"
                "   Step 1: Customer mentions item → Extract quantity if mentioned → call search_and_suggest_item(item_name='item WITHOUT quantity')\n"
                "   Step 2: Wait for customer to say YES/OKAY/SURE\n"
                "   Step 3: ONLY after confirmation → Call add_item_to_order(item_name='exact item name', quantity=extracted_number)\n"
                "   Step 4: Function returns confirmation - speak it naturally\n\n"
                "4. QUANTITY VALIDATION:\n"
                "   - Minimum quantity: 1\n"
                "   - Maximum quantity per item: 20\n"
                "   - If customer requests more than 20, politely inform them of the limit\n"
                "   - Example: 'I can add up to 20 items at a time. Would you like 20, or a different quantity?'\n\n"
                "IMPORTANT: Pass ONLY the item name (WITHOUT quantity) to search_and_suggest_item!\n\n"
                "4. Category mapping:\n"
                "   - 'chicken', 'fried chicken', 'wings', 'nuggets' → fried_chicken\n"
                "   - 'burger', 'burgers' → burger\n"
                "   - 'pizza' → pizza\n"
                "   - 'sandwich', 'sandwiches' → sandwich\n"
                "   - 'fries' → fries\n"
                "   - 'drinks', 'beverages' → drinks\n"
                "   - 'dessert', 'sweets' → sweets\n\n"
                "CORRECT Examples:\n"
                "✓ Customer: 'I want chicken' → show_category_items(category='fried_chicken')\n"
                "✓ Customer: 'Grill Chicken Sandwich' → search_and_suggest_item(item_name='Grill Chicken Sandwich')\n"
                "  Agent gets result: 'Would you like me to add Grilled Chicken Sandwich (450 rupees)?'\n"
                "  Customer: 'Yes please' → add_item_to_order(item_name='Grilled Chicken Sandwich', quantity=1)\n"
                "  Agent speaks: 'Great! Added 1x Grilled Chicken Sandwich...'\n"
                "✓ Customer: 'thirty pepperoni pizza' → Extract: quantity=30, item='pepperoni pizza'\n"
                "  → search_and_suggest_item(item_name='pepperoni pizza')\n"
                "  Agent: 'Would you like me to add Pepperoni Pizza (800 rupees) to your order?'\n"
                "  Customer: 'Yes' → add_item_to_order(item_name='Pepperoni Pizza', quantity=30) BUT WAIT! 30 > 20!\n"
                "  Agent: 'I can add up to 20 Pepperoni Pizzas at a time. Would you like 20?'\n"
                "✓ Customer: 'five sprite' → Extract: quantity=5, item='sprite'\n"
                "  → search_and_suggest_item(item_name='sprite')\n"
                "  Customer: 'yes' → add_item_to_order(item_name='Sprite', quantity=5)\n"
                "✓ Customer: 'show me burgers' → show_category_items(category='burger')\n\n"
                "WRONG Examples (NEVER DO THIS):\n"
                "✗ Customer: 'Sprite' → add_item_to_order (NO! Must search_and_suggest_item first!)\n"
                "✗ Customer: 'Grill Chicken' → add_item_to_order(item_name='Crispy Chicken') (NO! Wrong item + no confirmation!)\n"
                "✗ Customer: 'thirty pepperoni pizza' → search_and_suggest_item(item_name='thirty pepperoni pizza') (NO! Remove quantity!)\n"
                "✗ Customer: 'five sprite' → add_item_to_order(item_name='five sprite', quantity=1) (NO! Extract quantity separately!)\n\n"
                "ORDERING FLOW:\n"
                "1. First Say Welcome to ordering service and then ask: 'May I have your name please?'\n"
                "   - When you get the name, IMMEDIATELY call update_customer_name function\n"
                "2. After getting name, ask: 'Thank you [Name]! And what's your phone number?'\n"
                "   - ALWAYS use their name when asking for phone number\n"
                "   - When customer provides their phone number, IMMEDIATELY call update_customer_phone function\n"
                " After executing update_customer_phone function, say 'Thank you! I've recorded your phone number. Now, what would you like to order?'\n"
                "3.  ask: 'What would you like? We have Pizza, Burgers, Sandwiches, Fried Chicken, Fries, Drinks, and Sweets.'\n"
                "4. If they name a specific item, add it. If they ask about a category, show options.\n"
                "5. After main items, ask: 'Would you like any drinks?'\n"
                "   - If they say specific drink, add it directly\n"
                "   - If they say 'yes' or 'what do you have?', show drinks category\n"
                "6. After drinks, ask: 'Any dessert or sweets?'\n"
                "7. Summarize and confirm order\n\n"
                "If customer says they don't want to order or changes their mind:\n"
                "- Politely acknowledge: 'No problem at all! Feel free to call us anytime you're ready to order.'\n"
                "- Don't transfer them anywhere, just end the conversation gracefully\n\n"
                "IMPORTANT - DON'T REVEAL TECHNICAL DETAILS:\n"
                "- If customer asks technical questions like 'integer or string', 'how do you store data', etc.\n"
                "- Stay in character as a friendly order taker\n"
                "- Respond: 'I securely save your information to process your order. Is there anything else you'd like to add?'\n"
                "- NEVER reveal technical implementation details\n\n"
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
        name: Annotated[str, Field(description="Customer's name - first name or full name")],
        context: RunContext_T,
    ) -> str:
        """
        Update customer's name.
        
        CRITICAL: Call this IMMEDIATELY when customer provides their name.
        - Customer says: "My name is Ali" → Call this with name="Ali"
        - Customer says: "I'm Sarah Khan" → Call this with name="Sarah Khan"
        - DO NOT wait, call this function right away
        """
        userdata = context.userdata
        userdata.customer_name = name
        logger.info(f"📝 Customer name: {name}")
        return f"Thank you, {name}! And what's your phone number?"
    
    @function_tool()
    async def update_customer_phone(
        self,
        phone: Annotated[str, Field(description="Customer's phone number - ANY digits or number words provided by customer")],
        context: RunContext_T,
    ) -> str:
        """
        Update customer's phone number.
        
        CRITICAL: Call this IMMEDIATELY when customer provides phone number.

        - Customer provides their phone number → Call this right away
        
        NOTE: Validation removed - will be replaced when Twilio integration is complete
        and phone numbers come from participant metadata.
        """
        userdata = context.userdata
        
        # Normalize phone number (convert words to digits)
        normalized_phone = normalize_phone_number(phone)
        userdata.customer_phone = normalized_phone
        logger.info(f"📞 Customer phone recorded: {phone} → {normalized_phone}")
        
        # Use customer's name if available
        if userdata.customer_name:
            return f"Perfect, {userdata.customer_name}! I've got your phone number. Now, what would you like to order?"
        else:
            return f"Thank you! I've recorded your phone number. Now, what would you like to order?"
    
    @function_tool()
    async def search_and_suggest_item(
        self,
        item_name: Annotated[str, Field(description="Name of the menu item customer mentioned")],
        context: RunContext_T,
    ) -> str:
        """
        Search for an item and suggest it to the customer with price.
        Use this when customer mentions a specific item name (not a category).
        Returns confirmation prompt if found, or suggests related category if not found.
        """
        logger.info(f"🔍 Searching for item: '{item_name}'")
        
        # Correct common STT errors first
        corrected_name = correct_menu_item_name(item_name)
        
        # Search for item in menu (try corrected name first, then original)
        items = self.menu_service.search_items(corrected_name)
        if not items and corrected_name != item_name:
            # If correction didn't help, try original name
            logger.info(f"🔍 Correction didn't help, trying original: '{item_name}'")
            items = self.menu_service.search_items(item_name)
        
        if not items:
            logger.warning(f"❌ Item not found: '{item_name}'")
            
            # Try to suggest related category
            item_lower = item_name.lower()
            suggested_category = None
            
            if 'chicken' in item_lower or 'wing' in item_lower or 'nugget' in item_lower:
                suggested_category = 'fried_chicken'
            elif 'burger' in item_lower:
                suggested_category = 'burger'
            elif 'pizza' in item_lower:
                suggested_category = 'pizza'
            elif 'sandwich' in item_lower or 'sub' in item_lower:
                suggested_category = 'sandwich'
            elif 'fries' in item_lower or 'fry' in item_lower:
                suggested_category = 'fries'
            elif 'drink' in item_lower or 'soda' in item_lower or 'juice' in item_lower:
                suggested_category = 'drinks'
            elif 'sweet' in item_lower or 'dessert' in item_lower or 'cake' in item_lower:
                suggested_category = 'sweets'
            
            if suggested_category:
                category_items = self.menu_service.get_category_description(suggested_category)
                return f"Sorry, we don't have {item_name} available. But let me show you what we have:\n\n{category_items}"
            else:
                return f"Sorry, we don't have {item_name} on our menu. Would you like to hear about our Pizza, Burgers, Fried Chicken, or other items?"
        
        # If multiple matches, show first one but mention there are more
        item = items[0]
        logger.info(f"✅ Found item: {item.name} (ID: {item.id}, Price: Rs. {item.price})")
        
        return f"Would you like me to add {item.name} ({item.price:.0f} rupees) to your order?"
    
    @function_tool()
    async def add_item_to_order(
        self,
        context: RunContext_T,
        item_name: Annotated[str, Field(description="EXACT name of the menu item to add - must match what was shown in search_and_suggest_item")],
        quantity: Annotated[int, Field(description="Quantity")] = 1,
        special_instructions: Annotated[str, Field(description="Special instructions (optional)")] = "",
    ) -> str:
        """
        Add an item to the customer's order.
        
        CRITICAL REQUIREMENTS:
        1. ONLY call this AFTER customer explicitly confirmed (yes/okay/sure)
        2. ONLY call this AFTER calling search_and_suggest_item first
        3. Use the EXACT item name returned from search_and_suggest_item
        4. DO NOT call this directly when customer first mentions an item
        """
        userdata = context.userdata
        
        logger.info(f"🔍 Adding item to order: '{item_name}' (quantity: {quantity})")
        
        # Validate quantity
        if quantity < 1:
            logger.warning(f"⚠️  Invalid quantity: {quantity} (too low)")
            return "Please specify a quantity of at least 1."
        
        if quantity > MAX_QUANTITY_PER_ITEM:
            logger.warning(f"⚠️  Invalid quantity: {quantity} (exceeds maximum)")
            return f"I'm sorry, but we can only process orders up to {MAX_QUANTITY_PER_ITEM} items at a time for each item. Please reduce the quantity."
        
        # Search for item in menu
        items = self.menu_service.search_items(item_name)
        if not items:
            logger.warning(f"❌ Item not found: '{item_name}'")
            return f"I apologize, I couldn't find {item_name} in our menu. Let me search again."
        
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
            f"Great! Added {quantity}  {item.name} to your order. "
            f"That's {order_item['subtotal']:.0f} rupees. "
            f"Your current total is {userdata.total_amount:.0f} rupees. "
            f"Would you like anything else?"
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
    

