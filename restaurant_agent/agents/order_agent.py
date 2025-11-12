"""
Order Agent - Takes orders from customers
"""
import logging
import re
from typing import Annotated, List
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
                "CRITICAL RULE FOR ALL FUNCTION CALLS:\n"
                "- Every function returns a message\n"
                "- After calling ANY function, your NEXT response MUST be EXACTLY what the function returned\n"
                "- Do NOT add extra words, do NOT paraphrase, just repeat the function's return value word-for-word\n"
                "- Example: Function returns 'Thank you, Ali! And what's your phone number?' → You say 'Thank you, Ali! And what's your phone number?'\n\n"
                f"{menu_text}\n\n"
                "CRITICAL ORDERING RULES - FOLLOW STRICTLY:\n\n"
                "1. MULTIPLE ITEMS vs SINGLE ITEM:\n"
                "    Customer lists MULTIPLE items in ONE sentence:\n"
                "      'I want a margherita pizza, two sprites, and loaded fries'\n"
                "      → Use process_multiple_items with ALL items at once\n"
                "      → Extract each item with its quantity\n"
                "      → Never say 'let me search' or 'let me check'\n"
                "      → Process silently and respond with complete summary\n"
                "   \n"
                "    Customer mentions ONE item at a time:\n"
                "      'I want a margherita pizza' (waits) 'Also add sprite'\n"
                "      → Use search_and_suggest_item for single item\n"
                "      → Wait for confirmation before adding\n\n"
                "2. BULK ORDER PROCESS (for multiple items):\n"
                "   Step 1: Customer lists multiple items → Extract ALL items with quantities\n"
                "   Step 2: Call process_multiple_items([{name: 'item1', quantity: 1}, {name: 'item2', quantity: 2}])\n"
                "   Step 3: Function returns summary with available/unavailable items and total price\n"
                "   Step 4: Customer confirms (yes/okay/sure) → Call confirm_bulk_order()\n"
                "   Step 5: All items added at once\n"
                "   \n"
                "   CRITICAL: NEVER say 'let me search for X' or 'let me check Y' - just do it silently!\n\n"
                "3. QUANTITY EXTRACTION:\n"
                "   When customer says: 'three sprites' or 'one pizza' or '2 burgers'\n"
                "   - Extract QUANTITY: three=3, one=1, 2=2\n"
                "   - Extract ITEM NAME: 'sprite', 'pizza', 'burger' (WITHOUT quantity words)\n"
                "   - Pass to function as separate quantity parameter\n\n"
                "4. QUANTITY VALIDATION:\n"
                "   - Minimum: 1\n"
                "   - Maximum per item: 20\n"
                "   - If customer requests more, inform them of the limit\n\n"
                "5. Category mapping (for show_category_items):\n"
                "   - 'chicken', 'fried chicken', 'wings', 'nuggets' → fried_chicken\n"
                "   - 'burger', 'burgers' → burger\n"
                "   - 'pizza' → pizza\n"
                "   - 'sandwich', 'sandwiches' → sandwich\n"
                "   - 'fries' → fries\n"
                "   - 'drinks', 'beverages' → drinks\n"
                "   - 'dessert', 'sweets' → sweets\n\n"
                "CORRECT BULK ORDER Examples:\n"
                "✓ Customer: 'I want margherita pizza, two sprites, and loaded fries'\n"
                "  Agent: → process_multiple_items(item1_name='margherita pizza', item1_quantity=1, item2_name='sprite', item2_quantity=2, item3_name='loaded fries', item3_quantity=1)\n"
                "  Agent speaks: 'Great! Here's what I can add to your order: 1x Margherita Pizza - 899 rupees, 2x Sprite - 198 rupees, 1x Loaded Fries - 349 rupees. Total: 1446 rupees. Would you like me to add these?'\n"
                "  Customer: 'Yes'\n"
                "  Agent: → confirm_bulk_order()\n"
                "  Agent speaks: 'Perfect! I've added 1x Margherita Pizza, 2x Sprite, 1x Loaded Fries...'\n\n"
                "✓ Customer: 'Give me one pepperoni pizza, one zinger burger, five fries, and three cokes'\n"
                "  Agent: → process_multiple_items(item1_name='pepperoni pizza', item1_quantity=1, item2_name='zinger burger', item2_quantity=1, item3_name='fries', item3_quantity=5, item4_name='coke', item4_quantity=3)\n"
                "  (NO searching messages - silent processing)\n"
                "  Agent speaks: 'Great! Here's what I can add...' (with full summary)\n\n"
                "WRONG Examples (NEVER DO THIS):\n"
                "✗ Customer lists multiple items → Agent says 'Let me search for margherita pizza first' (NO! Process all at once!)\n"
                "✗ Customer lists multiple items → Agent calls search_and_suggest_item for each item separately (NO! Use process_multiple_items!)\n"
                "✗ Agent: 'I'll check the margherita pizza, one moment' (NO! Never say you're checking!)\n\n"
                "ORDERING FLOW:\n"
                "1. First of All Say Welcome to ordering service and then ask the customer to say their name\n"
                "   - When you get the name, IMMEDIATELY call update_customer_name function\n"
                "   - The function returns a message - SAY THAT MESSAGE EXACTLY as your response\n"
                "2. When customer provides their phone number:\n"
                "   - IMMEDIATELY call update_customer_phone function\n"
                "   - The function returns a message - SAY THAT MESSAGE EXACTLY as your response\n"
                "   - Example: Function returns 'Perfect, Ali! I've got your phone number. Now, what would you like to order?' → You say exactly that\n"
                "3. Take their order (use bulk processing for multiple items, single for one item)\n"
                "4. After main items, ask: 'Would you like any drinks?'\n"
                "5. After drinks, ask: 'Any dessert or sweets?'\n"
                "6. Summarize and confirm order and also ask if they want to add anything else if they say no. Politely ask if they want to confirm the order\n\n"
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
        
        AFTER calling this function, you MUST say the EXACT message it returns.
        The function will tell you what to say next - use that exact message.
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
        
        AFTER calling this function, you MUST say the EXACT message it returns.
        The function will tell you what to say next - use that exact message.
        Do NOT add anything extra, just speak what the function returns.
        """
        userdata = context.userdata
        
        # Normalize phone number (convert words to digits)
        normalized_phone = normalize_phone_number(phone)
        
        # Validate: phone number should contain only digits after normalization
        if not normalized_phone or not normalized_phone.isdigit():
            logger.warning(f"📞 Invalid phone number provided: {phone} → {normalized_phone}")
            # Ask user to provide a valid phone number again
            if userdata.customer_name:
                return f"I'm sorry {userdata.customer_name}, I didn't catch that correctly. Could you please tell me your phone number again? Please say all the digits clearly."
            else:
                return f"I'm sorry, I didn't catch that correctly. Could you please tell me your phone number again? Please say all the digits clearly."
        
        # Validate: phone number should be reasonable length (10-11 digits for Pakistan)

        # Valid phone number - save it
        userdata.customer_phone = normalized_phone
        logger.info(f"📞 Customer phone recorded: {phone} → {normalized_phone}")
        
        # Use customer's name if available
        if userdata.customer_name:
            return f"Perfect, {userdata.customer_name}! I've got your phone number. Now, what would you like to order?"
        else:
            return f"Thank you! I've recorded your phone number. Now, what would you like to order?"
    
    @function_tool()
    async def process_multiple_items(
        self,
        context: RunContext_T,
        item1_name: Annotated[str, Field(description="First item name")],
        item1_quantity: Annotated[int, Field(description="First item quantity")] = 1,
        item2_name: Annotated[str, Field(description="Second item name (optional)")] = "",
        item2_quantity: Annotated[int, Field(description="Second item quantity")] = 1,
        item3_name: Annotated[str, Field(description="Third item name (optional)")] = "",
        item3_quantity: Annotated[int, Field(description="Third item quantity")] = 1,
        item4_name: Annotated[str, Field(description="Fourth item name (optional)")] = "",
        item4_quantity: Annotated[int, Field(description="Fourth item quantity")] = 1,
        item5_name: Annotated[str, Field(description="Fifth item name (optional)")] = "",
        item5_quantity: Annotated[int, Field(description="Fifth item quantity")] = 1,
        item6_name: Annotated[str, Field(description="Sixth item name (optional)")] = "",
        item6_quantity: Annotated[int, Field(description="Sixth item quantity")] = 1,
    ) -> str:
        """
        Process multiple items at once - search for all, report availability, and ask for confirmation.
        
        This function:
        1. Searches for all items mentioned
        2. Groups them into: available items and unavailable items
        3. Returns a summary with total price for available items
        4. Asks customer to confirm the available items
        
        Use this when customer lists multiple items in one sentence.
        Fill in item1_name first, then item2_name if there's a second item, etc.
        Leave item names empty if not needed.
        """
        # Collect all items into a list
        items = []
        if item1_name:
            items.append({"name": item1_name, "quantity": item1_quantity})
        if item2_name:
            items.append({"name": item2_name, "quantity": item2_quantity})
        if item3_name:
            items.append({"name": item3_name, "quantity": item3_quantity})
        if item4_name:
            items.append({"name": item4_name, "quantity": item4_quantity})
        if item5_name:
            items.append({"name": item5_name, "quantity": item5_quantity})
        if item6_name:
            items.append({"name": item6_name, "quantity": item6_quantity})
        
        logger.info(f"🛒 Processing bulk order: {len(items)} items")
        
        available_items = []
        unavailable_items = []
        total_price = 0
        
        # Process each item
        for item_request in items:
            item_name = item_request.get('name', '')
            quantity = item_request.get('quantity', 1)
            
            # Validate quantity
            if quantity > MAX_QUANTITY_PER_ITEM:
                unavailable_items.append({
                    'name': item_name,
                    'reason': f"quantity exceeds maximum of {MAX_QUANTITY_PER_ITEM}"
                })
                continue
            
            # Correct common STT errors
            corrected_name = correct_menu_item_name(item_name)
            
            # Search for item
            found_items = self.menu_service.search_items(corrected_name)
            if not found_items and corrected_name != item_name:
                found_items = self.menu_service.search_items(item_name)
            
            if found_items:
                menu_item = found_items[0]
                item_total = menu_item.price * quantity
                available_items.append({
                    'menu_item': menu_item,
                    'quantity': quantity,
                    'subtotal': item_total
                })
                total_price += item_total
                logger.info(f"✅ Found: {menu_item.name} x{quantity} = Rs. {item_total}")
            else:
                unavailable_items.append({
                    'name': item_name,
                    'reason': 'not found on menu'
                })
                logger.warning(f"❌ Not found: {item_name}")
        
        # Build response
        if not available_items and not unavailable_items:
            return "I didn't catch any items. Could you please repeat your order?"
        
        # Store available items in context for confirmation
        context.userdata.pending_bulk_order = available_items
        
        response_parts = []
        
        # List available items
        if available_items:
            response_parts.append("Great! Here's what I can add to your order:")
            for item_info in available_items:
                menu_item = item_info['menu_item']
                qty = item_info['quantity']
                subtotal = item_info['subtotal']
                response_parts.append(f"• {qty}x {menu_item.name} - {subtotal:.0f} rupees")
            
            response_parts.append(f"\nTotal for these items: {total_price:.0f} rupees")
        
        # List unavailable items
        if unavailable_items:
            response_parts.append("\nUnfortunately, these items are not available:")
            for unavail in unavailable_items:
                response_parts.append(f"• {unavail['name']} ({unavail['reason']})")
        
        # Ask for confirmation if we have available items
        if available_items:
            response_parts.append("\nWould you like me to add these items to your order?")
        else:
            response_parts.append("\nWould you like to try something else from our menu?")
        
        return "\n".join(response_parts)
    
    @function_tool()
    async def confirm_bulk_order(
        self,
        context: RunContext_T,
    ) -> str:
        """
        Confirm and add all items from pending bulk order to the customer's cart.
        Only call this after customer confirms the bulk order (says yes/okay/sure).
        """
        userdata = context.userdata
        
        if not hasattr(userdata, 'pending_bulk_order') or not userdata.pending_bulk_order:
            return "There are no pending items to add. What would you like to order?"
        
        pending_items = userdata.pending_bulk_order
        logger.info(f"✅ Confirming bulk order: {len(pending_items)} items")
        
        added_items = []
        total_added = 0
        
        # Add all pending items to the order
        for item_info in pending_items:
            menu_item = item_info['menu_item']
            quantity = item_info['quantity']
            subtotal = item_info['subtotal']
            
            # Create order item
            order_item = {
                "item_id": menu_item.id,
                "name": menu_item.name,
                "quantity": quantity,
                "price": menu_item.price,
                "subtotal": subtotal,
                "special_instructions": ""
            }
            
            userdata.order_items.append(order_item)
            userdata.total_amount += subtotal
            added_items.append(f"{quantity}x {menu_item.name}")
            total_added += subtotal
            
            logger.info(f"✅ Added: {quantity}x {menu_item.name} (Rs. {subtotal})")
        
        # Clear pending order
        userdata.pending_bulk_order = []
        
        # Build confirmation response
        items_summary = ", ".join(added_items)
        response = (
            f"Perfect! I've added {items_summary} to your order. "
            f"That's {total_added:.0f} rupees. "
            f"Your current total is {userdata.total_amount:.0f} rupees. "
            f"Would you like anything else?"
        )
        
        return response
    
    @function_tool()
    async def search_and_suggest_item(
        self,
        item_name: Annotated[str, Field(description="Name of the menu item customer mentioned")],
        context: RunContext_T,
    ) -> str:
        """
        Search for an item and suggest it to the customer with price.
        Use this when customer mentions a SINGLE item name (not multiple items at once).
        For multiple items, use process_multiple_items instead.
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
        
        # Check if customer specified a size already
        query_lower = item_name.lower()
        has_size_in_query = any(size in query_lower for size in ['small', 'medium', 'large', 'bucket'])
        
        # Check if multiple size variants exist
        if len(items) > 1 and not has_size_in_query:
            # Group by base name (without size prefix)
            item_groups = {}
            for item in items:
                # Remove size prefix to get base name
                base_name = item.name
                for size_prefix in ['Small ', 'Medium ', 'Large ']:
                    if base_name.startswith(size_prefix):
                        base_name = base_name[len(size_prefix):]
                        break
                
                if base_name not in item_groups:
                    item_groups[base_name] = []
                item_groups[base_name].append(item)
            
            # If we have multiple items with same base name, ask for size
            for base_name, group_items in item_groups.items():
                if len(group_items) > 1:
                    logger.info(f"📏 Multiple sizes found for: {base_name}")
                    size_options = []
                    for item in group_items:
                        size_options.append(f"{item.name} - {item.price:.0f} rupees")
                    
                    options_text = "\n".join(size_options)
                    return f"We have different sizes available:\n{options_text}\n\nWhich size would you like?"
        
        # Single match or customer already specified size
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
    

