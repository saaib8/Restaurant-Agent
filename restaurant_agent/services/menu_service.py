"""
Pakistani Restaurant Menu Service
"""
from typing import Dict, List
from pydantic import BaseModel


class MenuItem(BaseModel):
    """Menu item"""
    id: str
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
            # PAKISTANI CUISINE
            "biryani": [
                MenuItem(
                    id="biryani_chicken",
                    name="Chicken Biryani",
                    price=450.0,
                    category="biryani",
                    description="Aromatic basmati rice with tender chicken"
                ),
                MenuItem(
                    id="biryani_mutton",
                    name="Mutton Biryani",
                    price=650.0,
                    category="biryani",
                    description="Special mutton biryani with fragrant spices"
                ),
                MenuItem(
                    id="biryani_beef",
                    name="Beef Biryani",
                    price=550.0,
                    category="biryani",
                    description="Delicious beef biryani"
                ),
                MenuItem(
                    id="biryani_prawn",
                    name="Prawn Biryani",
                    price=750.0,
                    category="biryani",
                    description="Special seafood biryani with jumbo prawns"
                ),
            ],
            "karahi": [
                MenuItem(
                    id="karahi_chicken",
                    name="Chicken Karahi",
                    price=1200.0,
                    category="karahi",
                    description="Full chicken karahi for 4-5 people"
                ),
                MenuItem(
                    id="karahi_mutton",
                    name="Mutton Karahi",
                    price=1800.0,
                    category="karahi",
                    description="Premium mutton karahi"
                ),
                MenuItem(
                    id="karahi_white",
                    name="White Karahi",
                    price=1400.0,
                    category="karahi",
                    description="Creamy white chicken karahi"
                ),
            ],
            "bbq": [
                MenuItem(
                    id="bbq_tikka",
                    name="Chicken Tikka",
                    price=350.0,
                    category="bbq",
                    description="Grilled chicken tikka"
                ),
                MenuItem(
                    id="bbq_malai_boti",
                    name="Malai Boti",
                    price=400.0,
                    category="bbq",
                    description="Creamy malai boti"
                ),
                MenuItem(
                    id="bbq_seekh_kebab",
                    name="Seekh Kebab",
                    price=300.0,
                    category="bbq",
                    description="Minced meat seekh kebab"
                ),
                MenuItem(
                    id="bbq_reshmi_kebab",
                    name="Reshmi Kebab",
                    price=380.0,
                    category="bbq",
                    description="Silky smooth chicken kebabs"
                ),
                MenuItem(
                    id="bbq_beef_tikka",
                    name="Beef Tikka",
                    price=420.0,
                    category="bbq",
                    description="Tender beef tikka pieces"
                ),
            ],
            "curry": [
                MenuItem(
                    id="curry_nihari",
                    name="Nihari",
                    price=500.0,
                    category="curry",
                    description="Slow-cooked beef stew"
                ),
                MenuItem(
                    id="curry_haleem",
                    name="Haleem",
                    price=450.0,
                    category="curry",
                    description="Traditional meat and lentil stew"
                ),
                MenuItem(
                    id="curry_korma",
                    name="Chicken Korma",
                    price=600.0,
                    category="curry",
                    description="Creamy chicken curry"
                ),
            ],
            
            # CHINESE CUISINE
            "fried_rice": [
                MenuItem(
                    id="rice_chicken",
                    name="Chicken Fried Rice",
                    price=350.0,
                    category="fried_rice",
                    description="Wok-fried rice with chicken"
                ),
                MenuItem(
                    id="rice_beef",
                    name="Beef Fried Rice",
                    price=400.0,
                    category="fried_rice",
                    description="Fried rice with beef"
                ),
                MenuItem(
                    id="rice_prawn",
                    name="Prawn Fried Rice",
                    price=500.0,
                    category="fried_rice",
                    description="Fried rice with prawns"
                ),
                MenuItem(
                    id="rice_vegetable",
                    name="Vegetable Fried Rice",
                    price=250.0,
                    category="fried_rice",
                    description="Mixed vegetable fried rice"
                ),
            ],
            "noodles": [
                MenuItem(
                    id="noodles_chicken_chow_mein",
                    name="Chicken Chow Mein",
                    price=380.0,
                    category="noodles",
                    description="Stir-fried noodles with chicken"
                ),
                MenuItem(
                    id="noodles_beef_chow_mein",
                    name="Beef Chow Mein",
                    price=420.0,
                    category="noodles",
                    description="Beef chow mein noodles"
                ),
                MenuItem(
                    id="noodles_vegetable",
                    name="Vegetable Chow Mein",
                    price=280.0,
                    category="noodles",
                    description="Vegetable noodles"
                ),
            ],
            "chinese_main": [
                MenuItem(
                    id="chinese_chicken_manchurian",
                    name="Chicken Manchurian",
                    price=450.0,
                    category="chinese_main",
                    description="Crispy chicken in spicy sauce"
                ),
                MenuItem(
                    id="chinese_sweet_sour_chicken",
                    name="Sweet and Sour Chicken",
                    price=480.0,
                    category="chinese_main",
                    description="Tangy sweet and sour chicken"
                ),
                MenuItem(
                    id="chinese_kung_pao",
                    name="Kung Pao Chicken",
                    price=500.0,
                    category="chinese_main",
                    description="Spicy Szechuan chicken"
                ),
                MenuItem(
                    id="chinese_spring_rolls",
                    name="Spring Rolls",
                    price=200.0,
                    category="chinese_main",
                    description="Crispy vegetable spring rolls (4 pieces)"
                ),
                MenuItem(
                    id="chinese_chicken_wings",
                    name="Chinese Style Chicken Wings",
                    price=350.0,
                    category="chinese_main",
                    description="Glazed chicken wings (6 pieces)"
                ),
            ],
            
            # CONTINENTAL CUISINE
            "pasta": [
                MenuItem(
                    id="pasta_alfredo",
                    name="Chicken Alfredo Pasta",
                    price=550.0,
                    category="pasta",
                    description="Creamy white sauce pasta with chicken"
                ),
                MenuItem(
                    id="pasta_bolognese",
                    name="Spaghetti Bolognese",
                    price=500.0,
                    category="pasta",
                    description="Classic meat sauce pasta"
                ),
                MenuItem(
                    id="pasta_carbonara",
                    name="Pasta Carbonara",
                    price=520.0,
                    category="pasta",
                    description="Creamy pasta with bacon"
                ),
                MenuItem(
                    id="pasta_arrabiata",
                    name="Penne Arrabiata",
                    price=450.0,
                    category="pasta",
                    description="Spicy tomato sauce pasta"
                ),
            ],
            "steaks": [
                MenuItem(
                    id="steak_chicken_grilled",
                    name="Grilled Chicken Steak",
                    price=650.0,
                    category="steaks",
                    description="Juicy grilled chicken with sides"
                ),
                MenuItem(
                    id="steak_beef",
                    name="Beef Steak",
                    price=950.0,
                    category="steaks",
                    description="Premium beef steak with vegetables"
                ),
                MenuItem(
                    id="steak_fish",
                    name="Fish Steak",
                    price=750.0,
                    category="steaks",
                    description="Grilled fish fillet with lemon butter"
                ),
            ],
            "pizza": [
                MenuItem(
                    id="pizza_margherita",
                    name="Margherita Pizza",
                    price=600.0,
                    category="pizza",
                    description="Classic cheese and tomato pizza"
                ),
                MenuItem(
                    id="pizza_pepperoni",
                    name="Pepperoni Pizza",
                    price=750.0,
                    category="pizza",
                    description="Loaded with pepperoni"
                ),
                MenuItem(
                    id="pizza_chicken_tikka",
                    name="Chicken Tikka Pizza",
                    price=800.0,
                    category="pizza",
                    description="Fusion pizza with chicken tikka"
                ),
                MenuItem(
                    id="pizza_veggie",
                    name="Vegetable Pizza",
                    price=650.0,
                    category="pizza",
                    description="Mixed vegetable pizza"
                ),
            ],
            
            # FAST FOOD
            "burgers": [
                MenuItem(
                    id="burger_beef",
                    name="Beef Burger",
                    price=350.0,
                    category="burgers",
                    description="Classic beef burger with cheese"
                ),
                MenuItem(
                    id="burger_chicken",
                    name="Chicken Burger",
                    price=300.0,
                    category="burgers",
                    description="Crispy chicken burger"
                ),
                MenuItem(
                    id="burger_zinger",
                    name="Zinger Burger",
                    price=320.0,
                    category="burgers",
                    description="Spicy chicken zinger"
                ),
                MenuItem(
                    id="burger_veggie",
                    name="Veggie Burger",
                    price=250.0,
                    category="burgers",
                    description="Vegetarian burger"
                ),
            ],
            "fast_food": [
                MenuItem(
                    id="ff_club_sandwich",
                    name="Club Sandwich",
                    price=400.0,
                    category="fast_food",
                    description="Triple-decker sandwich"
                ),
                MenuItem(
                    id="ff_chicken_nuggets",
                    name="Chicken Nuggets",
                    price=280.0,
                    category="fast_food",
                    description="Crispy chicken nuggets (8 pieces)"
                ),
                MenuItem(
                    id="ff_french_fries",
                    name="French Fries",
                    price=150.0,
                    category="fast_food",
                    description="Crispy golden fries"
                ),
                MenuItem(
                    id="ff_loaded_fries",
                    name="Loaded Fries",
                    price=250.0,
                    category="fast_food",
                    description="Fries with cheese and toppings"
                ),
                MenuItem(
                    id="ff_wings",
                    name="Buffalo Wings",
                    price=400.0,
                    category="fast_food",
                    description="Spicy chicken wings (6 pieces)"
                ),
            ],
            
            # BREAD
            "bread": [
                MenuItem(
                    id="bread_naan",
                    name="Naan",
                    price=30.0,
                    category="bread",
                    description="Fresh tandoori naan"
                ),
                MenuItem(
                    id="bread_roti",
                    name="Roti",
                    price=20.0,
                    category="bread",
                    description="Whole wheat roti"
                ),
                MenuItem(
                    id="bread_paratha",
                    name="Paratha",
                    price=40.0,
                    category="bread",
                    description="Layered paratha"
                ),
                MenuItem(
                    id="bread_garlic_naan",
                    name="Garlic Naan",
                    price=50.0,
                    category="bread",
                    description="Naan with garlic butter"
                ),
                MenuItem(
                    id="bread_cheese_naan",
                    name="Cheese Naan",
                    price=80.0,
                    category="bread",
                    description="Stuffed with cheese"
                ),
            ],
            
            # ENHANCED DRINKS
            "drinks": [
                MenuItem(
                    id="drink_lassi_sweet",
                    name="Sweet Lassi",
                    price=120.0,
                    category="drinks",
                    description="Chilled sweet yogurt drink"
                ),
                MenuItem(
                    id="drink_lassi_mango",
                    name="Mango Lassi",
                    price=150.0,
                    category="drinks",
                    description="Mango flavored lassi"
                ),
                MenuItem(
                    id="drink_lassi_salted",
                    name="Salted Lassi",
                    price=100.0,
                    category="drinks",
                    description="Traditional salted lassi"
                ),
                MenuItem(
                    id="drink_coke",
                    name="Coca Cola",
                    price=80.0,
                    category="drinks",
                    description="Chilled Coke"
                ),
                MenuItem(
                    id="drink_sprite",
                    name="Sprite",
                    price=80.0,
                    category="drinks",
                    description="Lemon-lime soda"
                ),
                MenuItem(
                    id="drink_fanta",
                    name="Fanta",
                    price=80.0,
                    category="drinks",
                    description="Orange flavored soda"
                ),
                MenuItem(
                    id="drink_water",
                    name="Mineral Water",
                    price=50.0,
                    category="drinks",
                    description="Bottled water"
                ),
                MenuItem(
                    id="drink_fresh_lime",
                    name="Fresh Lime Soda",
                    price=120.0,
                    category="drinks",
                    description="Fresh lime with soda"
                ),
                MenuItem(
                    id="drink_juice_mango",
                    name="Mango Juice",
                    price=150.0,
                    category="drinks",
                    description="Fresh mango juice"
                ),
                MenuItem(
                    id="drink_juice_orange",
                    name="Orange Juice",
                    price=150.0,
                    category="drinks",
                    description="Fresh orange juice"
                ),
                MenuItem(
                    id="drink_mojito",
                    name="Mint Mojito",
                    price=180.0,
                    category="drinks",
                    description="Refreshing mint mojito"
                ),
                MenuItem(
                    id="drink_milkshake_vanilla",
                    name="Vanilla Milkshake",
                    price=200.0,
                    category="drinks",
                    description="Creamy vanilla shake"
                ),
                MenuItem(
                    id="drink_milkshake_chocolate",
                    name="Chocolate Milkshake",
                    price=200.0,
                    category="drinks",
                    description="Rich chocolate shake"
                ),
                MenuItem(
                    id="drink_milkshake_strawberry",
                    name="Strawberry Milkshake",
                    price=200.0,
                    category="drinks",
                    description="Fresh strawberry shake"
                ),
            ],
            
            # ENHANCED DESSERTS
            "desserts": [
                MenuItem(
                    id="dessert_kheer",
                    name="Kheer",
                    price=150.0,
                    category="desserts",
                    description="Traditional rice pudding"
                ),
                MenuItem(
                    id="dessert_gulab_jamun",
                    name="Gulab Jamun",
                    price=100.0,
                    category="desserts",
                    description="Sweet syrupy dumplings (2 pieces)"
                ),
                MenuItem(
                    id="dessert_ras_malai",
                    name="Ras Malai",
                    price=180.0,
                    category="desserts",
                    description="Cottage cheese in sweetened milk (2 pieces)"
                ),
                MenuItem(
                    id="dessert_gajar_halwa",
                    name="Gajar Halwa",
                    price=200.0,
                    category="desserts",
                    description="Traditional carrot dessert"
                ),
                MenuItem(
                    id="dessert_lab_e_shireen",
                    name="Lab-e-Shireen",
                    price=220.0,
                    category="desserts",
                    description="Creamy vermicelli pudding"
                ),
                MenuItem(
                    id="dessert_ice_cream_vanilla",
                    name="Vanilla Ice Cream",
                    price=150.0,
                    category="desserts",
                    description="Classic vanilla (2 scoops)"
                ),
                MenuItem(
                    id="dessert_ice_cream_chocolate",
                    name="Chocolate Ice Cream",
                    price=150.0,
                    category="desserts",
                    description="Rich chocolate (2 scoops)"
                ),
                MenuItem(
                    id="dessert_brownie",
                    name="Chocolate Brownie",
                    price=180.0,
                    category="desserts",
                    description="Warm chocolate brownie with ice cream"
                ),
                MenuItem(
                    id="dessert_cheesecake",
                    name="Cheesecake",
                    price=250.0,
                    category="desserts",
                    description="Classic New York cheesecake"
                ),
                MenuItem(
                    id="dessert_tiramisu",
                    name="Tiramisu",
                    price=300.0,
                    category="desserts",
                    description="Italian coffee dessert"
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

PAKISTANI CUISINE:
- biryani (4 items)
- karahi (3 items)
- bbq (5 items)
- curry (3 items)

CHINESE CUISINE:
- fried_rice (4 items)
- noodles (3 items)
- chinese_main (5 items)

CONTINENTAL CUISINE:
- pasta (4 items)
- steaks (3 items)
- pizza (4 items)

FAST FOOD:
- burgers (4 items)
- fast_food (5 items)

SIDES:
- bread (5 items)

DRINKS:
- drinks (14 items)

DESSERTS:
- desserts (10 items)

IMPORTANT: When customer asks about a cuisine, ALWAYS use the show_category_items tool with the specific category name.
"""
    
    @staticmethod
    def get_categories() -> dict:
        """Get organized menu categories"""
        return {
            "main_courses": {
                "Pakistani": ["biryani", "karahi", "bbq", "curry"],
                "Chinese": ["fried_rice", "noodles", "chinese_main"],
                "Continental": ["pasta", "steaks", "pizza"],
                "Fast Food": ["burgers", "fast_food"]
            },
            "sides": ["bread"],
            "drinks": ["drinks"],
            "desserts": ["desserts"]
        }
    
    @staticmethod
    def get_category_description(category: str) -> str:
        """Get items in a specific category for speech"""
        menu = MenuService.get_menu()
        if category not in menu:
            return f"Sorry, {category} is not available."
        
        items = menu[category]
        text = f"{category.replace('_', ' ').title()}:\n"
        for item in items:
            text += f"{item.name} - {item.price:.0f} rupees\n"
        
        return text
    
    @staticmethod
    def find_item_by_id(item_id: str) -> MenuItem | None:
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
        query = query.lower()
        menu = MenuService.get_menu()
        results = []
        
        for items in menu.values():
            for item in items:
                if query in item.name.lower():
                    results.append(item)
        
        return results


# Convenience function
def get_menu() -> Dict[str, List[MenuItem]]:
    """Get menu"""
    return MenuService.get_menu()

