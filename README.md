# 🍽️ Restaurant Voice Agent

An intelligent voice-based ordering system for restaurants, built with LiveKit Agents Framework. The agent handles customer orders through natural voice conversations, with support for phone-based customer tracking, fuzzy menu search, and automated STT error correction.

## 📋 Table of Contents

- [Features](#features)
- [Order System](#order-system)
- [Constraints & Validation](#constraints--validation)
- [Custom Word Mappings](#custom-word-mappings)
- [Fuzzy Matching](#fuzzy-matching)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Roadmap](#roadmap)

## ✨ Features

### Current Features (Order Agent)

- **Voice-First Ordering**: Natural conversation flow for taking food orders
- **Multi-Item Bulk Processing**: Handle multiple items in a single request
- **Smart Menu Search**: Fuzzy matching with STT error correction
- **Phone Number Validation**: Accepts various formats (with hyphens, spaces, spoken digits)
- **Customer Data Collection**: Name and phone number tracking
- **Order Management**: Add, remove, and review items in cart
- **MongoDB Integration**: Persistent order storage with customer tracking
- **Real-time Voice**: Ultra-low latency with LiveKit infrastructure

### Voice Features

- **STT (Speech-to-Text)**: Groq Whisper Large V3 Turbo (ultra-fast)
- **LLM**: OpenAI GPT-4o-mini
- **TTS (Text-to-Speech)**: Cartesia Sonic 2
- **VAD (Voice Activity Detection)**: Silero
- **Noise Cancellation**: BVC (Background Voice Cancellation)

## 🛒 Order System

### Order Flow

1. **Greeting**: Agent welcomes customer and transfers to order agent
2. **Customer Info**: Collects name and phone number
3. **Menu Browsing**: Customer can request full menu or specific categories
4. **Ordering**: Two methods supported:
   - **Bulk Order**: "I want margherita pizza, two sprites, and loaded fries"
   - **Single Item**: "I want a margherita pizza" (then confirm)
5. **Upselling**: Agent suggests drinks and desserts
6. **Review**: Customer can review their order
7. **Confirmation**: Final confirmation and order saved to database

### Ordering Methods

#### Bulk Order Processing
For multiple items in one sentence:
```
Customer: "Give me one pepperoni pizza, two sprites, and loaded fries"
Agent: [Silently processes all items]
Agent: "Great! Here's what I can add to your order:
       1x Pepperoni Pizza - 1099 rupees
       2x Sprite - 198 rupees  
       1x Loaded Fries - 349 rupees
       Total: 1646 rupees. Would you like me to add these?"
Customer: "Yes"
Agent: [Adds all items at once]
```

#### Single Item Processing
For one item at a time:
```
Customer: "I want a margherita pizza"
Agent: "Would you like me to add Margherita Pizza (899 rupees) to your order?"
Customer: "Yes"
Agent: [Adds item]
```

### Menu Categories

- **Pizza** (6 items): Margherita, Pepperoni, BBQ Chicken, Vegetable, Supreme, Hawaiian
- **Burgers** (7 items): Classic Beef, Double Beef, Crispy Chicken, Grilled Chicken, Zinger, Veggie, Fish
- **Sandwiches** (6 items): Club, Grilled Chicken, Crispy Chicken, Steak, Tuna, Veggie
- **Fried Chicken** (10 items): Buckets (S/M/L), Wings, Strips, Nuggets, Popcorn
- **Fries** (7 items): Regular, Large, Cheese, Loaded, Curly, Wedges, Onion Rings
- **Drinks** (14 items): Sodas, Water, Lemonade, Milkshakes, Coffee
- **Sweets** (12 items): Ice Cream, Sundaes, Brownies, Donuts, Cookies, Pies

## ⚠️ Constraints & Validation

### Quantity Limits
- **Minimum**: 1 item
- **Maximum per item**: 20 items
- If customer requests more than 20, agent politely informs them of the limit

### Phone Number Validation
- Accepts spoken digits: "five five five one two three four"
- Accepts number words: "zero", "one", "two", etc. (also "oh" and "o" for zero)
- Accepts special patterns: "double five" (55), "triple six" (666)
- Removes formatting: Hyphens, spaces, parentheses, dots automatically stripped
- Validates: Must contain only digits after normalization
- Example accepted formats:
  - `555-123-4567`
  - `(555) 123-4567`
  - `five five five one two three four`
  - `double five triple six`

### Order Validation
- Order must contain at least one item
- Phone number required before order confirmation
- Customer name requested (but not strictly required)

## 🔤 Custom Word Mappings

The system includes 250+ custom STT corrections for common speech-to-text errors, especially from phone audio and accents.

### Examples of STT Corrections

#### Drinks
```python
"ist" → "iced tea"          # Common: user says "ice-t", STT hears "ist"
"eyes tea" → "iced tea"     # STT mishears "iced" as "eyes"
"right" → "sprite"          # STT might hear "sprite" as "right"
```

#### Fries
```python
"phrase" → "fries"          # Very common mishearing
"prize" → "fries"           # Common: user says "fries", STT hears "prize"
"praise" → "fries"
"tries" → "fries"
"loaded prize" → "loaded fries"
```

#### Burgers
```python
"singer" → "zinger burger"  # Common: STT hears "singer" instead of "zinger"
"berger" → "burger"         # Valid English word (surname)
"chief burger" → "beef burger"
```

#### Chicken
```python
"girl" → "grilled chicken"  # Common: "grill" sounds like "girl"
"christy chicken" → "crispy chicken"
"wang" → "chicken wings"    # Valid alternate pronunciation
```

#### Pizza
```python
"margarita" → "margherita pizza"  # Valid: the drink vs the pizza
"pepper only" → "pepperoni pizza"
"paper only" → "pepperoni pizza"  # Extreme mishearing
```

### How It Works

The correction system uses a two-step approach:

1. **Exact Match**: If the spoken phrase exactly matches a known error, it's corrected
2. **Partial Match**: If a known error word is contained in the phrase, it's replaced

```python
# From stt_corrections.py
def correct_menu_item_name(item_name: str) -> str:
    item_lower = item_name.lower().strip()
    
    # Exact match
    if item_lower in MENU_ITEM_CORRECTIONS:
        corrected = MENU_ITEM_CORRECTIONS[item_lower]
        return corrected
    
    # Partial match
    for error_word, correct_word in MENU_ITEM_CORRECTIONS.items():
        if error_word in item_lower:
            corrected = item_lower.replace(error_word, correct_word)
            return corrected
    
    return item_name
```

## 🔍 Fuzzy Matching

The menu search uses a three-pass fuzzy matching algorithm to handle typos, phonetic variations, and partial queries.

### Search Algorithm

#### Pass 1: Exact Substring Match
```python
Query: "margherita"
Match: "Margherita Pizza" ✓ (exact substring found)
```

#### Pass 2: Partial Word Matching
```python
Query: "chicken bbq"
Match: "Barbecue Chicken Pizza" ✓ (all query words found in item name)
```

#### Pass 3: Fuzzy Matching (Levenshtein Distance)
```python
Query: "margarita"      # Common misspelling
Match: "Margherita Pizza" ✓ (similarity >= 65%)

Query: "zinjer"         # Typo
Match: "Zinger Burger" ✓ (similarity >= 65%)
```

### Fuzzy Match Implementation

Uses Levenshtein distance with dynamic programming:

```python
def _fuzzy_match(word1: str, word2: str, threshold: float = 0.65) -> bool:
    """
    Check if two words are similar enough.
    Allows 1-2 character differences.
    
    Examples:
    - "margarita" ≈ "margherita" (True)
    - "zinjer" ≈ "zinger" (True)
    - "pizza" ≈ "burger" (False)
    """
    # Levenshtein distance calculation
    distance = calculate_levenshtein(word1, word2)
    similarity = 1 - (distance / max(len(word1), len(word2)))
    return similarity >= threshold
```

### Size Variant Handling

When multiple sizes exist (Small/Medium/Large), the agent asks for clarification:

```
Customer: "I want chicken wings"
Agent: "We have different sizes available:
       Small Chicken Wings
       Large Chicken Wings
       Which size would you like?"
```

## 🛠️ Tech Stack

### Core Framework
- **LiveKit Agents** (~1.2): Real-time voice agent framework
- **Python** (>=3.11): Core programming language

### AI Services
- **STT**: Groq Whisper Large V3 Turbo (ultra-fast speech recognition)
- **LLM**: OpenAI GPT-4o-mini (conversation intelligence)
- **TTS**: Cartesia Sonic 2 (natural voice synthesis)
- **VAD**: Silero (voice activity detection)

### Database
- **MongoDB**: Persistent storage
  - **Motor** (3.3.2+): Async MongoDB driver
  - **PyMongo** (4.6.1+): MongoDB toolkit

### Voice Processing
- **Silero VAD**: Voice activity detection
- **BVC**: Background voice cancellation (noise reduction)

### HTTP & Networking
- **aiohttp** (3.9.0+): Async HTTP client
- **httpx** (0.26.0+): Modern HTTP client
- **certifi** (2024.0.0+): SSL certificate bundle

### Data & Validation
- **Pydantic** (2.5.0+): Data validation and settings
- **email-validator** (2.1.0+): Email validation

### Environment
- **python-dotenv** (1.1.1+): Environment variable management

## 📁 Project Structure

```
restaurant-agent/
├── restaurant_agent/
│   ├── __init__.py
│   ├── agents/                      # Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Base agent class with UserData
│   │   ├── greeter.py              # Greeter agent (welcome & handoff)
│   │   └── order_agent.py          # Order taking agent (main logic)
│   │
│   ├── config/                      # Configuration
│   │   ├── __init__.py
│   │   └── settings.py             # Environment settings (API keys, DB config)
│   │
│   ├── helpers/                     # Utility functions
│   │   ├── __init__.py
│   │   └── stt_corrections.py     # STT error corrections (250+ mappings)
│   │
│   ├── models/                      # Data models
│   │   ├── __init__.py
│   │   └── order.py               # Order data structures
│   │
│   └── services/                    # Business logic services
│       ├── __init__.py
│       ├── database.py            # MongoDB connection & operations
│       └── menu_service.py        # Menu management & search (fuzzy matching)
│
├── restaurant_main.py               # Main entry point
├── pyproject.toml                   # Project dependencies
├── livekit.toml                     # LiveKit configuration
├── restaurant_agent.log            # Application logs
├── view_logs.py                     # Log viewer utility
├── bg_noise.mp3                     # Background noise for testing
└── README.md                        # This file
```

### Key Files

#### `restaurant_main.py`
Main entry point. Sets up SSL certificates, initializes agents, configures STT/TTS/LLM, and starts the LiveKit session.

#### `agents/order_agent.py` (715 lines)
Core ordering logic with 10+ function tools:
- `update_customer_name()` - Collect customer name
- `update_customer_phone()` - Collect and validate phone
- `show_full_menu()` - Display complete menu with pacing
- `show_category_items()` - Show specific category
- `search_and_suggest_item()` - Search single item
- `process_multiple_items()` - Bulk order processing
- `confirm_bulk_order()` - Confirm bulk order
- `add_item_to_order()` - Add single item
- `remove_item_from_order()` - Remove item
- `show_current_order()` - Display cart
- `confirm_order()` - Save to database

#### `services/menu_service.py` (688 lines)
Menu management and fuzzy search:
- Complete menu definition (62 items)
- Three-pass search algorithm
- Fuzzy matching with Levenshtein distance
- Category descriptions for speech
- Size variant detection

#### `helpers/stt_corrections.py` (280 lines)
STT error correction with 250+ phonetic mappings for common voice recognition errors.

## 🚀 Installation

### Prerequisites
- Python 3.11 or higher
- MongoDB instance (local or cloud)
- LiveKit server (cloud or self-hosted)
- API keys for: OpenAI, Groq, Cartesia

### Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd restaurant-agent
```

2. **Install dependencies**
```bash
pip install -e .
```

Or with uv (faster):
```bash
uv pip install -e .
```

3. **Create environment file**
```bash
cp .env.example .env.local
```

4. **Configure environment variables**
Edit `.env.local`:
```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI (for LLM)
OPENAI_API_KEY=sk-...

# Groq (for STT)
GROQ_API_KEY=gsk_...

# Cartesia (for TTS) 
CARTESIA_API_KEY=...

# MongoDB
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=restaurant_db
CUSTOMERS_COLLECTION=customers
ORDERS_COLLECTION=orders
```

5. **Run the agent**
```bash
python restaurant_main.py dev
```

## ⚙️ Configuration

### LiveKit Settings (`livekit.toml`)
Configure your LiveKit agent settings, including room connection, permissions, and agent metadata.

### Voice Settings
Adjust in `restaurant_main.py`:
```python
session = AgentSession[UserData](
    stt=openai.STT(
        model="whisper-large-v3-turbo",  # Fast STT
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    ),
    llm="openai/gpt-4o-mini",           # Smart but fast LLM
    tts="cartesia/sonic-2:...",          # Natural TTS
    vad=silero.VAD.load(),              # Voice detection
    max_tool_steps=10,                   # Function call limit
    allow_interruptions=True,            # User can interrupt
)
```

### Menu Customization
Edit menu items in `services/menu_service.py`:
```python
MenuItem(
    id=1,
    name="Margherita Pizza",
    price=899.0,
    category="pizza",
    description="Classic cheese and tomato pizza"
)
```

### STT Corrections
Add custom corrections in `helpers/stt_corrections.py`:
```python
MENU_ITEM_CORRECTIONS = {
    "common_error": "correct_name",
    "singer": "zinger burger",
    # Add your own...
}
```

## 📖 Usage

### Testing Locally

1. Start the agent:
```bash
python restaurant_main.py dev
```

2. Connect via LiveKit Playground or integrate with your phone system

3. Test conversation:
```
Agent: "Welcome! May I have your name please?"
You: "My name is Ali"
Agent: "Thank you, Ali! And what's your phone number?"
You: "555-123-4567"
Agent: "Perfect, Ali! I've got your phone number. Now, what would you like to order?"
You: "Give me one pepperoni pizza and two sprites"
Agent: "Great! Here's what I can add to your order: 1x Pepperoni Pizza, 2x Sprite..."
```

### View Logs
```bash
python view_logs.py
```

Or directly:
```bash
tail -f restaurant_agent.log
```

## 🗺️ Roadmap

### ✅ Completed
- [x] Voice-based order taking
- [x] Customer name and phone collection
- [x] Multi-item bulk processing
- [x] Fuzzy menu search
- [x] STT error correction (250+ mappings)
- [x] Phone number normalization
- [x] MongoDB integration
- [x] Order management (add/remove/review)

### 🚧 In Progress
- [ ] **Twilio Integration**: Phone system integration
  - Inbound call handling
  - Phone number extraction from caller ID
  - Call routing and forwarding
  - Voice recording and transcription
  - SMS notifications
  
- [ ] **Reservation Agent**: Handle table reservations
  - Date/time selection
  - Party size
  - Special requests
  - Confirmation SMS/Email
  
- [ ] **Messaging Agent**: Send order updates
  - Order confirmation messages
  - Delivery status updates
  - SMS and email support
  - WhatsApp integration

### 🔮 Future Features
- [ ] Delivery address collection and geocoding
- [ ] Real-time order tracking
- [ ] Loyalty program integration
- [ ] Multi-language support (Urdu, English)
- [ ] Voice authentication for returning customers
- [ ] Call recording and quality monitoring (via Twilio)
- [ ] SMS marketing campaigns

## 📝 Notes

### Phone System Integration
Currently, the system collects phone numbers through voice conversation. Future Twilio integration will:
- Automatically capture caller ID from inbound calls
- Enable direct phone-to-agent connections
- Support SMS notifications for order confirmations
- Provide call recording and analytics



### Menu Prices
Currently, menu prices are NOT announced when browsing categories. Prices are only mentioned during the ordering confirmation phase to keep the conversation natural.

### Voice Optimization
- Pauses ("...") added between items for natural speech rhythm
- No markdown formatting in voice responses
- Numbers spoken as words ("rupees" not "Rs")
- Strategic silences for better listening experience

### Error Handling
- Graceful degradation if MongoDB is unavailable
- Retries with fallback SSL configuration
- Comprehensive logging for debugging
- User-friendly error messages


