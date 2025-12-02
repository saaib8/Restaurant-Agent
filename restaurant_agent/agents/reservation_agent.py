"""
Reservation Agent - Handles table reservations
"""
import logging
import re
from typing import Annotated
from pydantic import Field
from datetime import datetime, date
from livekit.agents.llm import function_tool

from .base_agent import BaseAgent, RunContext_T
from ..services.database import MongoDB
from ..services.reservation_service import ReservationService
from ..config.reservation_config import reservation_config

logger = logging.getLogger("restaurant-agent")


def normalize_phone_number(phone_str: str) -> str:
    """Convert spoken phone number words to digits and remove formatting characters"""
    # First, remove common phone number formatting characters (hyphens, spaces, parentheses, dots)
    phone_str = phone_str.replace('-', ' ').replace('(', '').replace(')', '').replace('.', ' ')
    
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
    
    # Final cleanup: remove any remaining non-digit characters
    phone_number = re.sub(r'\D', '', phone_number)
    
    return phone_number


class ReservationAgent(BaseAgent):
    """Reservation booking agent"""
    
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly reservation coordinator at Los Pollos Hermanos restaurant. "
                "Welcome to the reservation service!\n\n"
                "Your job is to help customers make table reservations following this flow:\n"
                "1. FIRST: Say 'Welcome to our reservation service!' and collect customer NAME\n"
                "   - Ask: 'May I have your name for the reservation?'\n"
                "   - When customer provides name, IMMEDIATELY call update_customer_name function\n"
                "2. Then collect customer PHONE NUMBER\n"
                "   - Ask: 'And what's your phone number?'\n"
                "   - When customer provides phone, IMMEDIATELY call update_customer_phone function\n"
                "3. Collect reservation DATE (ask: 'Great! What date would you like to reserve for?')\n"
                "4. Collect reservation TIME (ask: 'What time would you prefer?')\n"
                "5. Collect PARTY SIZE (ask: 'How many people will be dining with us?')\n"
                "6. Check AVAILABILITY using the check_availability function\n"
                "7. If available: Confirm the reservation details and ask for confirmation\n"
                "8. If NOT available: Suggest alternative times using suggest_alternative_slots\n"
                "9. When customer confirms: Create the reservation using confirm_reservation\n\n"
                "CRITICAL FUNCTION CALL RULES:\n"
                "- After collecting NAME, IMMEDIATELY call update_customer_name function\n"
                "- After collecting PHONE, IMMEDIATELY call update_customer_phone function\n"
                "- After collecting date, IMMEDIATELY call collect_reservation_date function\n"
                "- After collecting time, IMMEDIATELY call collect_reservation_time function\n"
                "- After collecting party size, IMMEDIATELY call collect_party_size function\n"
                "- After customer provides all info (name, phone, date, time, party), call check_availability\n"
                "- When customer confirms the reservation, call confirm_reservation\n"
                "- Always repeat the EXACT message returned by functions\n\n"
                "DATE PARSING:\n"
                "- Accept: 'today', 'tomorrow', day names ('Friday', 'Saturday'), specific dates\n"
                "- Always CONFIRM the parsed date with customer: 'So that's Friday, December 6th, correct?'\n"
                "- If customer says a day name, calculate the next occurrence of that day\n\n"
                "TIME PARSING:\n"
                "- Accept: '7 PM', '19:00', '7:30 PM', 'evening', 'dinner time'\n"
                "- Round to nearest 15-minute slot (7:05 → 7:00, 7:20 → 7:15)\n"
                "- Always CONFIRM the rounded time: 'So that's 7:00 PM, correct?'\n"
                "- If customer says 'evening' or 'dinner time', suggest 7:00 PM as default\n\n"
                "PARTY SIZE:\n"
                "- Minimum: 1 person, Maximum: 50 people\n"
                "- If customer says 'party of 4' or 'four people', extract the number 4\n"
                "- Confirm: 'So that's 4 people, correct?'\n\n"
                "AVAILABILITY RESPONSES:\n"
                "When slot is available:\n"
                "  'Great! I have availability for your party of 4 on Friday, December 6th at 7:00 PM. "
                "  Would you like me to confirm this reservation?'\n\n"
                "When slot is NOT available:\n"
                "  'I'm sorry, 7:00 PM is fully booked. However, I have availability at:'\n"
                "  Then call suggest_alternative_slots to get alternatives\n\n"
                "CONFIRMATION:\n"
                "Before confirming, summarize:\n"
                "  'Let me confirm your reservation:\n"
                "  - Name: [name]\n"
                "  - Phone: [phone]\n"
                "  - Date: Friday, December 6th\n"
                "  - Time: 7:00 PM\n"
                "  - Party size: 4 people\n"
                "  Is everything correct?'\n\n"
                "When customer says yes, call confirm_reservation immediately.\n\n"
                "VOICE FORMATTING:\n"
                "- This is a VOICE conversation, NOT text\n"
                "- NEVER use markdown formatting like **bold** or *italic*\n"
                "- NEVER use special characters: *, #, _, etc.\n"
                "- Speak naturally, as if talking to someone in person\n"
                "- Say times naturally: '7:00 PM' or 'seven PM'\n"
                "- Say dates naturally: 'Friday, December sixth' not '12/6/2025'\n\n"
                "CUSTOMER INFO:\n"
                "- ALWAYS collect name and phone at the START of the reservation process\n"
                "- First ask for name, then phone number\n"
                "- Call update_customer_name and update_customer_phone immediately after receiving each\n"
                "- These are REQUIRED before you can confirm any reservation\n\n"
                "Be warm, professional, and helpful!"
            ),
        )
        self.reservation_service = ReservationService()
    
    @function_tool()
    async def collect_reservation_date(
        self,
        date_str: Annotated[str, Field(description="Date string from customer (e.g., 'tomorrow', 'Friday', 'Dec 6')")],
        context: RunContext_T,
    ) -> str:
        """
        Parse and store the reservation date.
        Call this IMMEDIATELY when customer provides a date.
        """
        userdata = context.userdata
        
        # Parse the date
        parsed_date = self.reservation_service.parse_natural_date(date_str)
        
        if parsed_date is None:
            logger.warning(f"📅 Could not parse date: {date_str}")
            return f"I'm sorry, I didn't quite catch that date. Could you please say the date again? For example, 'tomorrow' or 'this Friday'."
        
        # Validate: must be today or future
        if parsed_date < date.today():
            return "I'm sorry, I can only make reservations for today or future dates. What date would work for you?"
        
        # Store the date
        userdata.reservation_date = parsed_date.isoformat()  # Store as YYYY-MM-DD
        
        # Format for speech
        formatted_date = self.reservation_service.format_date_for_speech(parsed_date)
        
        logger.info(f"📅 Reservation date set: {parsed_date} ({formatted_date})")
        
        return f"Perfect! So that's {formatted_date}. What time would you prefer?"
    
    @function_tool()
    async def collect_reservation_time(
        self,
        time_str: Annotated[str, Field(description="Time string from customer (e.g., '7 PM', '19:00', 'evening')")],
        context: RunContext_T,
    ) -> str:
        """
        Parse and store the reservation time.
        Call this IMMEDIATELY when customer provides a time.
        """
        userdata = context.userdata
        
        # Handle common natural language times
        time_str_lower = time_str.lower()
        if 'evening' in time_str_lower or 'dinner' in time_str_lower:
            time_str = "7:00 PM"
        elif 'lunch' in time_str_lower:
            time_str = "12:00 PM"
        elif 'afternoon' in time_str_lower:
            time_str = "3:00 PM"
        
        # Round to nearest 15-minute slot
        rounded_time = self.reservation_service.round_time_to_slot(time_str)
        
        # Store the time
        userdata.reservation_time = rounded_time
        
        # Format for speech
        formatted_time = self.reservation_service.format_time_for_speech(rounded_time)
        
        logger.info(f"🕐 Reservation time set: {rounded_time} ({formatted_time})")
        
        return f"Great! So that's {formatted_time}. How many people will be dining with us?"
    
    @function_tool()
    async def collect_party_size(
        self,
        party_size: Annotated[int, Field(description="Number of people in the party")],
        context: RunContext_T,
    ) -> str:
        """
        Store the party size and validate it.
        Call this IMMEDIATELY when customer provides party size.
        """
        userdata = context.userdata
        
        # Validate party size
        if party_size < reservation_config.MIN_PARTY_SIZE:
            return f"I'm sorry, the minimum party size is {reservation_config.MIN_PARTY_SIZE}. How many people will be dining?"
        
        if party_size > reservation_config.MAX_PARTY_SIZE:
            return (f"I'm sorry, for parties larger than {reservation_config.MAX_PARTY_SIZE} people, "
                   "please call us directly at our restaurant so we can arrange special seating. "
                   "Would you like to make a reservation for a smaller party?")
        
        # Store party size
        userdata.party_size = party_size
        
        logger.info(f"👥 Party size set: {party_size}")
        
        # Check if we have all required info
        if userdata.reservation_date and userdata.reservation_time:
            return f"Perfect! Party of {party_size}. Let me check availability for you."
        else:
            return f"Got it, party of {party_size}. I still need the date and time for your reservation."
    
    @function_tool()
    async def check_availability(
        self,
        context: RunContext_T,
    ) -> str:
        """
        Check if the requested slot is available.
        Call this after you have date, time, and party size.
        
        This will automatically suggest alternatives if the slot is not available.
        """
        userdata = context.userdata
        
        # Validate we have all required info
        if not userdata.reservation_date or not userdata.reservation_time or not userdata.party_size:
            missing = []
            if not userdata.reservation_date:
                missing.append("date")
            if not userdata.reservation_time:
                missing.append("time")
            if not userdata.party_size:
                missing.append("party size")
            return f"I still need the following information: {', '.join(missing)}."
        
        # Parse date
        booking_date = date.fromisoformat(userdata.reservation_date)
        booking_time = userdata.reservation_time
        party_size = userdata.party_size
        
        # Check availability
        available_capacity = await self.reservation_service.calculate_available_capacity(
            booking_date,
            booking_time,
            reservation_config.DEFAULT_DINING_DURATION
        )
        
        # Format date and time for speech
        formatted_date = self.reservation_service.format_date_for_speech(booking_date)
        formatted_time = self.reservation_service.format_time_for_speech(booking_time)
        
        logger.info(f"🔍 Availability check: {booking_date} {booking_time} - "
                   f"Available: {available_capacity}, Requested: {party_size}")
        
        if available_capacity >= party_size:
            # Available! Store pending reservation
            userdata.pending_reservation = {
                "date": booking_date,
                "time": booking_time,
                "party_size": party_size,
                "formatted_date": formatted_date,
                "formatted_time": formatted_time,
            }
            
            return (f"Great news! I have availability for your party of {party_size} "
                   f"on {formatted_date} at {formatted_time}. "
                   f"Would you like me to confirm this reservation?")
        else:
            # Not available - suggest alternatives
            logger.info(f"❌ Requested slot not available (only {available_capacity} seats free)")
            return f"I'm sorry, {formatted_time} on {formatted_date} is fully booked. Let me suggest some alternative times."
    
    @function_tool()
    async def suggest_alternative_slots(
        self,
        context: RunContext_T,
    ) -> str:
        """
        Suggest alternative time slots when the requested time is not available.
        Call this when check_availability indicates the slot is full.
        """
        userdata = context.userdata
        
        if not userdata.reservation_date or not userdata.reservation_time or not userdata.party_size:
            return "I need the date, time, and party size to suggest alternatives."
        
        # Parse date
        booking_date = date.fromisoformat(userdata.reservation_date)
        booking_time = userdata.reservation_time
        party_size = userdata.party_size
        
        # Get available slots
        available_slots = await self.reservation_service.get_available_slots(
            booking_date,
            party_size,
            preferred_time=booking_time
        )
        
        # Format date for speech
        formatted_date = self.reservation_service.format_date_for_speech(booking_date)
        
        if not available_slots:
            return (f"Unfortunately, we're fully booked for {formatted_date}. "
                   f"Would you like to try a different date?")
        
        # Take top 3 alternatives
        top_alternatives = available_slots[:reservation_config.MAX_ALTERNATIVE_SUGGESTIONS]
        
        # Format alternatives for speech
        alt_times = []
        for slot in top_alternatives:
            formatted_time = self.reservation_service.format_time_for_speech(slot['time'])
            alt_times.append(formatted_time)
        
        # Build response
        if len(alt_times) == 1:
            times_text = alt_times[0]
        elif len(alt_times) == 2:
            times_text = f"{alt_times[0]} or {alt_times[1]}"
        else:
            times_text = ", ".join(alt_times[:-1]) + f", or {alt_times[-1]}"
        
        logger.info(f"💡 Suggesting alternatives: {alt_times}")
        
        return f"I have availability at {times_text}. Which time would work better for you?"
    
    @function_tool()
    async def confirm_reservation(
        self,
        context: RunContext_T,
    ) -> str:
        """
        Confirm and save the reservation to the database.
        Call this ONLY after customer explicitly confirms they want the reservation.
        """
        userdata = context.userdata
        
        # Validate we have all required data
        if not userdata.customer_phone:
            return "I need your phone number to confirm the reservation. What's your phone number?"
        
        if not userdata.customer_name:
            return "I need your name to confirm the reservation. May I have your name please?"
        
        if not userdata.pending_reservation:
            return "There's no pending reservation to confirm. Let's start over. What date would you like to reserve for?"
        
        # Get reservation details from pending
        pending = userdata.pending_reservation
        booking_date = pending['date']
        booking_time = pending['time']
        party_size = pending['party_size']
        
        # Create reservation document
        reservation_data = {
            "phone": userdata.customer_phone,
            "customer_name": userdata.customer_name,
            "party_size": party_size,
            "booking_date": datetime.combine(booking_date, datetime.min.time()),  # Store as datetime
            "booking_time": booking_time,
            "dining_duration": reservation_config.DEFAULT_DINING_DURATION,
            "status": "confirmed",
            "special_requests": None,
            "created_at": datetime.utcnow(),
            "modified_at": datetime.utcnow(),
        }
        
        # Save to database
        saved = await MongoDB.save_reservation(reservation_data)
        
        formatted_date = pending['formatted_date']
        formatted_time = pending['formatted_time']
        
        if saved:
            logger.info(f"✅ Reservation confirmed: {userdata.customer_name} - "
                       f"{booking_date} {booking_time} - Party of {party_size}")
            
            # Clear pending reservation
            userdata.pending_reservation = None
            
            return (f"Excellent! Your reservation is confirmed, {userdata.customer_name}. "
                   f"We'll see you on {formatted_date} at {formatted_time} for {party_size} people. "
                   f"We look forward to serving you! "
                   f"Is there anything else I can help you with?")
        else:
            logger.warning(f"⚠️  Reservation saved locally but not in database")
            return (f"Your reservation is confirmed for {formatted_date} at {formatted_time}. "
                   f"Thank you!")
    
    @function_tool()
    async def show_reservation_summary(
        self,
        context: RunContext_T,
    ) -> str:
        """
        Show the current reservation details being created.
        Use this for confirmation before calling confirm_reservation.
        """
        userdata = context.userdata
        
        if userdata.pending_reservation:
            pending = userdata.pending_reservation
            formatted_date = pending['formatted_date']
            formatted_time = pending['formatted_time']
            party_size = pending['party_size']
            
            return (f"Here are your reservation details:\n"
                   f"Name: {userdata.customer_name or 'Not provided'}\n"
                   f" with the Phone Number : {userdata.customer_phone or 'Not provided'}\n"
                   f" on the Date: {formatted_date}\n"
                   f" at the Time: {formatted_time}\n"
                   f" for the : {party_size} people\n\n"
                   f"Would you like to confirm this reservation?")
        else:
            return "There's no pending reservation yet. What date would you like to reserve for?"
    
    @function_tool()
    async def update_customer_name(
        self,
        name: Annotated[str, Field(description="Customer's name")],
        context: RunContext_T,
    ) -> str:
        """
        Update customer's name for the reservation.
        Call this IMMEDIATELY when customer provides their name.
        """
        userdata = context.userdata
        userdata.customer_name = name
        logger.info(f"📝 Customer name updated: {name}")
        return f"Thank you, {name}! And what's your phone number?"
    
    @function_tool()
    async def update_customer_phone(
        self,
        phone: Annotated[str, Field(description="Customer's phone number - ANY digits or number words provided by customer")],
        context: RunContext_T,
    ) -> str:
        """
        Update customer's phone number for the reservation.
        Call this IMMEDIATELY when customer provides their phone.
        
        Accepts various formats:
        - "555-123-4567"
        - "five five five one two three four"
        - "double five triple six"
        """
        userdata = context.userdata
        
        # Normalize phone number (convert words to digits, remove hyphens and spaces)
        normalized_phone = normalize_phone_number(phone)
        
        # Validate: phone number should contain only digits after normalization
        if not normalized_phone or not normalized_phone.isdigit():
            logger.warning(f"📞 Invalid phone number provided: {phone} → {normalized_phone}")
            # Ask user to provide a valid phone number again
            if userdata.customer_name:
                return f"I'm sorry {userdata.customer_name}, I didn't catch that correctly. Could you please tell me your phone number again? Please say all the digits clearly."
            else:
                return f"I'm sorry, I didn't catch that correctly. Could you please tell me your phone number again? Please say all the digits clearly."
        
        # Valid phone number - save it
        userdata.customer_phone = normalized_phone
        logger.info(f"📞 Customer phone recorded: {phone} → {normalized_phone}")
        
        # Use customer's name if available
        if userdata.customer_name:
            return f"Perfect, {userdata.customer_name}! I've got your phone number. Now, what date would you like to reserve for?"
        else:
            return f"Perfect! I've got your phone number. Now, what date would you like to reserve for?"

