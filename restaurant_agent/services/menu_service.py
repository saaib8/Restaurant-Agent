"""
Fast Food Restaurant Menu Service
"""
from typing import Dict, List
from pydantic import BaseModel


class MenuItem(BaseModel):
    """Menu item"""
    id: int
    name: str
    price: float
    category: str
    description: str = ""


class MenuService:
    """Menu management service"""
    
    @staticmethod
    def get_menu() -> Dict[str, List[MenuItem]]:
        """Get complete restaurant menu"""
        return {
            # PIZZA
            "pizza": [
                MenuItem(
                    id=1,
                    name="Margherita Pizza",
                    price=899.0,
                    category="pizza",
                    description="Classic cheese and tomato pizza"
                ),
                MenuItem(
                    id=2,
                    name="Pepperoni Pizza",
                    price=1099.0,
                    category="pizza",
                    description="Loaded with pepperoni slices"
                ),
                MenuItem(
                    id=3,
                    name="Barbecue Chicken Pizza",
                    price=1199.0,
                    category="pizza",
                    description="Grilled chicken with BBQ sauce"
                ),
                MenuItem(
                    id=4,
                    name="Vegetable Pizza",
                    price=999.0,
                    category="pizza",
                    description="Fresh vegetables and cheese"
                ),
                MenuItem(
                    id=5,
                    name="Supreme Pizza",
                    price=1299.0,
                    category="pizza",
                    description="Loaded with meat and vegetables"
                ),
                MenuItem(
                    id=6,
                    name="Hawaiian Pizza",
                    price=1099.0,
                    category="pizza",
                    description="Ham and pineapple combination"
                ),
            ],
            
            # BURGERS
            "burger": [
                MenuItem(
                    id=7,
                    name="Classic Beef Burger",
                    price=399.0,
                    category="burger",
                    description="Juicy beef patty with cheese"
                ),
                MenuItem(
                    id=8,
                    name="Double Beef Burger",
                    price=549.0,
                    category="burger",
                    description="Two beef patties with double cheese"
                ),
                MenuItem(
                    id=9,
                    name="Crispy Chicken Burger",
                    price=349.0,
                    category="burger",
                    description="Crispy fried chicken fillet"
                ),
                MenuItem(
                    id=10,
                    name="Grilled Chicken Burger",
                    price=379.0,
                    category="burger",
                    description="Grilled chicken with special sauce"
                ),
                MenuItem(
                    id=11,
                    name="Zinger Burger",
                    price=399.0,
                    category="burger",
                    description="Spicy crispy chicken burger"
                ),
                MenuItem(
                    id=12,
                    name="Veggie Burger",
                    price=299.0,
                    category="burger",
                    description="Vegetarian patty with fresh veggies"
                ),
                MenuItem(
                    id=13,
                    name="Fish Burger",
                    price=369.0,
                    category="burger",
                    description="Breaded fish fillet with tartar sauce"
                ),
            ],
            
            # SANDWICHES
            "sandwich": [
                MenuItem(
                    id=14,
                    name="Club Sandwich",
                    price=449.0,
                    category="sandwich",
                    description="Triple-decker with chicken"
                ),
                MenuItem(
                    id=15,
                    name="Grilled Chicken Sandwich",
                    price=379.0,
                    category="sandwich",
                    description="Grilled chicken with lettuce and mayo"
                ),
                MenuItem(
                    id=16,
                    name="Crispy Chicken Sandwich",
                    price=399.0,
                    category="sandwich",
                    description="Crispy chicken with special sauce"
                ),
                MenuItem(
                    id=17,
                    name="Steak Sandwich",
                    price=549.0,
                    category="sandwich",
                    description="Tender beef steak with caramelized onions"
                ),
                MenuItem(
                    id=18,
                    name="Veggie Sandwich",
                    price=299.0,
                    category="sandwich",
                    description="Fresh vegetables with cheese"
                ),
                MenuItem(
                    id=19,
                    name="Tuna Sandwich",
                    price=379.0,
                    category="sandwich",
                    description="Tuna salad with fresh lettuce"
                ),
            ],
            
            # FRIED CHICKEN
            "fried_chicken": [
                MenuItem(
                    id=20,
                    name="6 Piece Fried Chicken",
                    price=899.0,
                    category="fried_chicken",
                    description="6 pieces of crispy fried chicken"
                ),
                MenuItem(
                    id=21,
                    name="9 Piece Fried Chicken",
                    price=1299.0,
                    category="fried_chicken",
                    description="9 pieces of crispy fried chicken"
                ),
                MenuItem(
                    id=22,
                    name="12 Piece Fried Chicken",
                    price=1699.0,
                    category="fried_chicken",
                    description="12 pieces of crispy fried chicken"
                ),
                MenuItem(
                    id=23,
                    name="6 Chicken Wings",
                    price=449.0,
                    category="fried_chicken",
                    description="6 crispy chicken wings"
                ),
                MenuItem(
                    id=24,
                    name="12 Chicken Wings",
                    price=799.0,
                    category="fried_chicken",
                    description="12 crispy chicken wings"
                ),
                MenuItem(
                    id=25,
                    name="3 Chicken Strips",
                    price=349.0,
                    category="fried_chicken",
                    description="3 crispy chicken strips"
                ),
                MenuItem(
                    id=26,
                    name="5 Chicken Strips",
                    price=549.0,
                    category="fried_chicken",
                    description="5 crispy chicken strips"
                ),
                MenuItem(
                    id=27,
                    name="6 Chicken Nuggets",
                    price=299.0,
                    category="fried_chicken",
                    description="6 crispy chicken nuggets"
                ),
                MenuItem(
                    id=28,
                    name="9 Chicken Nuggets",
                    price=399.0,
                    category="fried_chicken",
                    description="9 crispy chicken nuggets"
                ),
                MenuItem(
                    id=29,
                    name="Popcorn Chicken",
                    price=349.0,
                    category="fried_chicken",
                    description="Bite-sized crispy chicken pieces"
                ),
            ],
            
            # FRIES
            "fries": [
                MenuItem(
                    id=30,
                    name="Regular Fries",
                    price=149.0,
                    category="fries",
                    description="Crispy golden french fries"
                ),
                MenuItem(
                    id=31,
                    name="Large Fries",
                    price=199.0,
                    category="fries",
                    description="Large serving of crispy fries"
                ),
                MenuItem(
                    id=32,
                    name="Cheese Fries",
                    price=249.0,
                    category="fries",
                    description="Fries topped with melted cheese"
                ),
                MenuItem(
                    id=33,
                    name="Loaded Fries",
                    price=349.0,
                    category="fries",
                    description="Fries with cheese, bacon, and special sauce"
                ),
                MenuItem(
                    id=34,
                    name="Curly Fries",
                    price=229.0,
                    category="fries",
                    description="Seasoned curly fries"
                ),
                MenuItem(
                    id=35,
                    name="Potato Wedges",
                    price=199.0,
                    category="fries",
                    description="Crispy seasoned potato wedges"
                ),
                MenuItem(
                    id=36,
                    name="Onion Rings",
                    price=229.0,
                    category="fries",
                    description="Crispy breaded onion rings"
                ),
            ],
            
            # DRINKS
            "drinks": [
                MenuItem(
                    id=37,
                    name="Coca Cola",
                    price=99.0,
                    category="drinks",
                    description="Chilled Coca Cola"
                ),
                MenuItem(
                    id=38,
                    name="Pepsi",
                    price=99.0,
                    category="drinks",
                    description="Chilled Pepsi"
                ),
                MenuItem(
                    id=39,
                    name="Sprite",
                    price=99.0,
                    category="drinks",
                    description="Lemon-lime soda"
                ),
                MenuItem(
                    id=40,
                    name="Fanta",
                    price=99.0,
                    category="drinks",
                    description="Orange flavored soda"
                ),
                MenuItem(
                    id=41,
                    name="7UP",
                    price=99.0,
                    category="drinks",
                    description="Lemon-lime soda"
                ),
                MenuItem(
                    id=42,
                    name="Mountain Dew",
                    price=99.0,
                    category="drinks",
                    description="Citrus flavored soda"
                ),
                MenuItem(
                    id=43,
                    name="Mineral Water",
                    price=50.0,
                    category="drinks",
                    description="Bottled mineral water"
                ),
                MenuItem(
                    id=44,
                    name="Lemonade",
                    price=149.0,
                    category="drinks",
                    description="Fresh lemonade"
                ),
                MenuItem(
                    id=45,
                    name="Iced Tea",
                    price=149.0,
                    category="drinks",
                    description="Refreshing iced tea"
                ),
                MenuItem(
                    id=46,
                    name="Vanilla Milkshake",
                    price=249.0,
                    category="drinks",
                    description="Creamy vanilla milkshake"
                ),
                MenuItem(
                    id=47,
                    name="Chocolate Milkshake",
                    price=249.0,
                    category="drinks",
                    description="Rich chocolate milkshake"
                ),
                MenuItem(
                    id=48,
                    name="Strawberry Milkshake",
                    price=249.0,
                    category="drinks",
                    description="Fresh strawberry milkshake"
                ),
                MenuItem(
                    id=49,
                    name="Coffee",
                    price=149.0,
                    category="drinks",
                    description="Hot brewed coffee"
                ),
                MenuItem(
                    id=50,
                    name="Cappuccino",
                    price=199.0,
                    category="drinks",
                    description="Creamy cappuccino"
                ),
            ],
            
            # SWEETS
            "sweets": [
                MenuItem(
                    id=51,
                    name="Vanilla Ice Cream",
                    price=149.0,
                    category="sweets",
                    description="Classic vanilla ice cream (2 scoops)"
                ),
                MenuItem(
                    id=52,
                    name="Chocolate Ice Cream",
                    price=149.0,
                    category="sweets",
                    description="Rich chocolate ice cream (2 scoops)"
                ),
                MenuItem(
                    id=53,
                    name="Strawberry Ice Cream",
                    price=149.0,
                    category="sweets",
                    description="Fresh strawberry ice cream (2 scoops)"
                ),
                MenuItem(
                    id=54,
                    name="Hot Fudge Sundae",
                    price=249.0,
                    category="sweets",
                    description="Ice cream with hot fudge sauce"
                ),
                MenuItem(
                    id=55,
                    name="Caramel Sundae",
                    price=249.0,
                    category="sweets",
                    description="Ice cream with caramel sauce"
                ),
                MenuItem(
                    id=56,
                    name="Chocolate Brownie",
                    price=199.0,
                    category="sweets",
                    description="Warm chocolate brownie"
                ),
                MenuItem(
                    id=57,
                    name="Brownie with Ice Cream",
                    price=299.0,
                    category="sweets",
                    description="Warm brownie topped with ice cream"
                ),
                MenuItem(
                    id=58,
                    name="Glazed Donut",
                    price=99.0,
                    category="sweets",
                    description="Classic glazed donut"
                ),
                MenuItem(
                    id=59,
                    name="Chocolate Donut",
                    price=99.0,
                    category="sweets",
                    description="Chocolate frosted donut"
                ),
                MenuItem(
                    id=60,
                    name="3 Chocolate Chip Cookies",
                    price=149.0,
                    category="sweets",
                    description="Freshly baked chocolate chip cookies"
                ),
                MenuItem(
                    id=61,
                    name="Apple Pie",
                    price=199.0,
                    category="sweets",
                    description="Warm apple pie slice"
                ),
                MenuItem(
                    id=62,
                    name="Cheesecake",
                    price=299.0,
                    category="sweets",
                    description="Creamy New York style cheesecake"
                ),
            ],
        }
    
    @staticmethod
    def get_menu_text() -> str:
        """Get menu as formatted text for AI"""
        menu = MenuService.get_menu()
        text = "🍽️ **Our Menu**:\n\n"
        
        for category, items in menu.items():
            text += f"**{category.title()}**:\n"
            for item in items:
                text += f"  • {item.name} - Rs. {item.price:.0f}\n"
            text += "\n"
        
        return text
    
    @staticmethod
    def get_menu_text_for_speech() -> str:
        """Get menu as TTS-friendly text (no markdown, spell out currency)"""
        menu = MenuService.get_menu()
        text = "Our Menu:\n\n"
        
        for category, items in menu.items():
            text += f"{category.title()}:\n"
            for item in items:
                text += f"{item.name} - {item.price:.0f} rupees\n"
            text += "\n"
        
        return text
    
    @staticmethod
    def get_menu_summary() -> str:
        """Get a summary of available categories for agent instructions"""
        return """
MENU CATEGORIES (Use show_category_items tool to see items):

FAST FOOD RESTAURANT:
- pizza (6 items)
- burger (7 items)
- sandwich (6 items)
- fried_chicken (10 items)
- fries (7 items)
- drinks (14 items)
- sweets (12 items)

IMPORTANT: When customer asks about any category, ALWAYS use the show_category_items tool with the specific category name.
"""
    
    @staticmethod
    def get_categories() -> dict:
        """Get organized menu categories"""
        return {
            "main_items": ["pizza", "burger", "sandwich", "fried_chicken"],
            "sides": ["fries"],
            "drinks": ["drinks"],
            "sweets": ["sweets"]
        }
    
    @staticmethod
    def get_category_description(category: str) -> str:
        """Get items in a specific category for speech"""
        menu = MenuService.get_menu()
        if category not in menu:
            return f"I apologize, but we don't have {category} available at the moment."
        
        items = menu[category]
        text = f"{category.replace('_', ' ').title()}:\n"
        for item in items:
            text += f"{item.name} - {item.price:.0f} rupees\n"
        
        return text
    
    @staticmethod
    def find_item_by_id(item_id: int) -> MenuItem | None:
        """Find menu item by ID"""
        menu = MenuService.get_menu()
        for items in menu.values():
            for item in items:
                if item.id == item_id:
                    return item
        return None
    
    @staticmethod
    def search_items(query: str) -> List[MenuItem]:
        """Search menu items by name"""
        # Normalize the query
        query_normalized = query.lower().strip()
        
        # Convert number words to digits in query
        number_words = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
            'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
            'nineteen': '19', 'twenty': '20'
        }
        
        for word, digit in number_words.items():
            query_normalized = query_normalized.replace(word, digit)
        
        menu = MenuService.get_menu()
        results = []
        
        # First pass: exact substring match
        for items in menu.values():
            for item in items:
                if query_normalized in item.name.lower():
                    results.append(item)
        
        # If no results, try partial word matching
        if not results:
            query_words = query_normalized.split()
            for items in menu.values():
                for item in items:
                    item_name_lower = item.name.lower()
                    # Check if all query words are in the item name
                    if all(word in item_name_lower for word in query_words):
                        results.append(item)
        
        return results


# Convenience function
def get_menu() -> Dict[str, List[MenuItem]]:
    """Get menu"""
    return MenuService.get_menu()
