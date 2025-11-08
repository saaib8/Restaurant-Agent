"""
Speech-to-Text (STT) correction utilities
Handles phonetic variations and accent-based mispronunciations
"""
import logging

logger = logging.getLogger("restaurant-agent")



MENU_ITEM_CORRECTIONS = {
    # DRINKS - Real STT mishearings
    "ist": "iced tea",                    # Common: user says "ice-t", STT hears "ist"
    "ice t": "iced tea",
    "ice tea": "iced tea",
    "iced tea": "iced tea",
    "eyes tea": "iced tea",               # STT mishears "iced" as "eyes"
    "i st": "iced tea",
    "iced": "iced tea",
    
    "sprite": "sprite",
    "right": "sprite",                    # STT might hear "sprite" as "right"
    "spright": "sprite",                  # Valid English word
    
    "coke": "coca cola",
    "coca cola": "coca cola",
    "coca": "coca cola",
    
    "seven up": "7up",
    "7 up": "7up",
    
    "mountain do": "mountain dew",
    "mountain due": "mountain dew",
    "mountain dew": "mountain dew",
    
    "mineral": "mineral water",
    "water": "mineral water",
    "bottle water": "mineral water",
    
    "lemonade": "lemonade",
    "lemon aid": "lemonade",              # Valid English words
    
    "milkshake": "milkshake",
    "milk shake": "milkshake",
    "shake": "milkshake",
    
    "coffee": "coffee",
    "cappuccino": "cappuccino",
    
    # FRIES - Real STT mishearings
    "phrase": "fries",                    
    "prize": "fries",                     # Common: user says "fries", STT hears "prize"
    "praise": "fries",                    # Common mishearing
    "tries": "fries",                     # Common mishearing
    "loaded phrase": "loaded fries",
    "loaded prize": "loaded fries",
    "loaded tries": "loaded fries",
    "loaded": "loaded fries",
    "floated fries": "loaded fries",
    "tries" : "fries",
    "cheese fries": "cheese fries",
    "please fries": "cheese fries",       # Mishearing
    
    "curly fries": "curly fries",
    "early fries": "curly fries",         # Mishearing
    
    "regular fries": "regular fries",
    "large fries": "large fries",
    
    "potato wedges": "potato wedges",
    "wedges": "potato wedges",
    "wedge": "potato wedges",
    
    "onion rings": "onion rings",
    "onion ring": "onion rings",
    "rings": "onion rings",
    "fries": "fries",
    "fry": "fries",
    "french fries": "fries",
    "french fry": "fries",
    
    # BURGERS - Real STT mishearings  
    "burger": "burger",
    "berger": "burger",                   # Valid English word (surname)
    "berg": "burger",                     # Valid English word
    
    "zinger": "zinger burger",
    "singer": "zinger burger",            # Common: STT hears "singer" instead of "zinger"
    "singer burger": "zinger burger",
    "zing burger": "zinger burger",
    
    "beef burger": "beef burger",
    "chief burger": "beef burger",        # Mishearing
    "classic burger": "classic beef burger",
    
    "double burger": "double beef burger",
    "double beef": "double beef burger",
    "trouble burger": "double beef burger",  # Mishearing
    
    "fish burger": "fish burger",
    "wish burger": "fish burger",         # Mishearing
    
    "veggie burger": "veggie burger",
    "veg burger": "veggie burger",
    "wedgie burger": "veggie burger",     # Mishearing
    "vegetable burger": "veggie burger",
    
    # CHICKEN - Real STT mishearings
    "grill chicken": "grilled chicken",
    "grilled chicken": "grilled chicken",
    "grilled": "grilled chicken",
    "girl chicken": "grilled chicken",     # Mishearing: "grill" sounds like "girl"
    "girl": "grilled chicken",             # Common mishearing
    "grill": "grilled chicken",
    
    "crispy chicken": "crispy chicken",
    "crispy": "crispy chicken",
    "crisp chicken": "crispy chicken",
    "christy chicken": "crispy chicken",   # Mishearing
    "crisp": "crispy chicken",   
    
    "nugget": "chicken nuggets",
    "nuggets": "chicken nuggets",
    "chicken nugget": "chicken nuggets",
    "chicken nuggets": "chicken nuggets",
    
    "wing": "chicken wings",
    "wings": "chicken wings",
    "chicken wing": "chicken wings",
    "chicken wings": "chicken wings",
    "wang": "chicken wings",               # Valid English word
    "wangs": "chicken wings",
    
    "chicken strip": "chicken strips",
    "chicken strips": "chicken strips",
    "strips": "chicken strips",
    "strip": "chicken strips",
    "stripes": "chicken strips",           # Valid English word
    "chicken stripes": "chicken strips",
    
    "popcorn": "popcorn chicken",
    "popcorn chicken": "popcorn chicken",
    "pop corn": "popcorn chicken",
    "pup corn": "popcorn chicken",         # Mishearing
    
    "fried chicken": "fried chicken",
    "fry chicken": "fried chicken",
    "tried chicken": "fried chicken",      # Mishearing
    "chicken pieces": "fried chicken",
    
    # PIZZA - Real STT mishearings
    "pizza": "pizza",
    "pita": "pizza",                       # Valid: pita bread vs pizza
    "peter": "pizza",                      # Mishearing
    
    "margarita": "margherita pizza",      # Valid English word (the drink)
    "margherita": "margherita pizza",
    "margareta": "margherita pizza",      # Name variant
    "cheese pizza": "margherita pizza",
    
    "pepperoni": "pepperoni pizza",
    "pepperoni pizza": "pepperoni pizza",
    "pepper only": "pepperoni pizza",     # Mishearing
    "paper only": "pepperoni pizza",      # Mishearing
    
    "bbq chicken": "barbeq chicken pizza",
    "barbeque chicken": "barbeq chicken pizza",
    "barbecue chicken": "barbeq chicken pizza",
    "bbq": "barbeq chicken pizza",
    "barbeq": "barbeq chicken pizza",
    
    "hawaiian": "hawaiian pizza",
    "hawaiian pizza": "hawaiian pizza",
    "hawaii": "hawaiian pizza",
    "pineapple pizza": "hawaiian pizza",
    
    "supreme": "supreme pizza",
    "supreme pizza": "supreme pizza",
    
    "veggie pizza": "vegetable pizza",
    "veg pizza": "vegetable pizza",
    "vegetable pizza": "vegetable pizza",
    "vegetarian pizza": "vegetable pizza",
    
    # SANDWICHES - Real STT mishearings
    "club": "club sandwich",
    "club sandwich": "club sandwich",
    "triple decker": "club sandwich",
    
    "grilled sandwich": "grilled chicken sandwich",
    "grill sandwich": "grilled chicken sandwich",
    "girl sandwich": "grilled chicken sandwich",  # Mishearing
    
    "crispy sandwich": "crispy chicken sandwich",
    "crisp sandwich": "crispy chicken sandwich",
    "christy sandwich": "crispy chicken sandwich",  # Mishearing
    
    "steak": "steak sandwich",
    "steak sandwich": "steak sandwich",
    "stake": "steak sandwich",              # Valid English word
    "stake sandwich": "steak sandwich",
    "beef sandwich": "steak sandwich",
    
    "tuna": "tuna sandwich",
    "tuna sandwich": "tuna sandwich",
    "fish sandwich": "tuna sandwich",
    
    "veggie sandwich": "veggie sandwich",
    "veg sandwich": "veggie sandwich",
    "wedgie sandwich": "veggie sandwich",   # Mishearing
    "vegetable sandwich": "veggie sandwich",
    
    # SWEETS - Real STT mishearings
    "vanilla": "vanilla ice cream",
    "vanilla ice cream": "vanilla ice cream",
    "manila": "vanilla ice cream",          # Mishearing
    
    "chocolate": "chocolate ice cream",
    "chocolate ice cream": "chocolate ice cream",
    "choco": "chocolate ice cream",
    
    "strawberry": "strawberry ice cream",
    "strawberry ice cream": "strawberry ice cream",
    "straw berry": "strawberry ice cream",
    
    "brownie": "chocolate brownie",
    "chocolate brownie": "chocolate brownie",
    "choco brownie": "chocolate brownie",
    "browny": "chocolate brownie",          
    
    "sundae": "sundae",
    "sunday": "sundae",                     
    "fudge": "hot fudge sundae",
    "caramel": "caramel sundae",
    
    "ice cream": "ice cream",
    "icecream": "ice cream",
    "ice-cream": "ice cream",
    "i scream": "ice cream",                
}


def correct_menu_item_name(item_name: str) -> str:
    """
    Correct common STT errors in menu item names using phonetic mapping.
    
    Args:
        item_name: The item name as heard by STT (may contain errors)
    
    Returns:
        Corrected item name that better matches menu items
    """
    item_lower = item_name.lower().strip()
    
    
    if item_lower in MENU_ITEM_CORRECTIONS:
        corrected = MENU_ITEM_CORRECTIONS[item_lower]
        logger.info(f"🔧 Corrected STT error: '{item_name}' → '{corrected}'")
        return corrected

    for error_word, correct_word in MENU_ITEM_CORRECTIONS.items():
        if error_word in item_lower:
            corrected = item_lower.replace(error_word, correct_word)
            logger.info(f"🔧 Corrected STT error: '{item_name}' → '{corrected}'")
            return corrected
    
    # No correction needed
    return item_name

