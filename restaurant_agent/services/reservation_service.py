"""
Reservation Service - Availability calculation and time slot management
"""
import logging
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
import re

from ..config.reservation_config import reservation_config
from .database import MongoDB

logger = logging.getLogger("restaurant-agent")


class ReservationService:
    """Handles reservation availability and time slot management"""
    
    @staticmethod
    def round_time_to_slot(time_str: str) -> str:
        """
        Round a time string to the nearest 15-minute slot.
        
        Args:
            time_str: Time in various formats (e.g., "7:05 PM", "19:08", "7 PM")
        
        Returns:
            Time string in HH:MM 24-hour format rounded to nearest 15-min slot
        """
        try:
            # Parse various time formats
            time_str = time_str.strip().lower()
            
            # Handle "7 pm", "7pm", "19:00", "7:30 PM", "6 p.m.", etc.
            # Try to extract hour and minute
            hour, minute = 0, 0
            
            # Check for AM/PM BEFORE removing anything
            is_pm = 'p.m' in time_str or 'pm' in time_str or 'p m' in time_str
            is_am = 'a.m' in time_str or 'am' in time_str or 'a m' in time_str
            
            # Remove all AM/PM variations and dots
            time_str = time_str.replace('p.m.', '').replace('a.m.', '')
            time_str = time_str.replace('p.m', '').replace('a.m', '')
            time_str = time_str.replace('pm', '').replace('am', '')
            time_str = time_str.replace('p m', '').replace('a m', '')
            time_str = time_str.replace('.', '')  # Remove any remaining dots
            
            # Remove spaces
            time_str = time_str.strip().replace(' ', '')
            
            # Parse hour and minute
            if ':' in time_str:
                parts = time_str.split(':')
                hour = int(parts[0])
                # Handle minute part that might have text
                minute_str = parts[1] if len(parts) > 1 else '0'
                # Extract digits only
                import re
                minute_digits = re.findall(r'\d+', minute_str)
                minute = int(minute_digits[0]) if minute_digits else 0
            else:
                # Just hour provided - extract digits
                import re
                hour_digits = re.findall(r'\d+', time_str)
                hour = int(hour_digits[0]) if hour_digits else 19  # Default to 7 PM
                minute = 0
            
            # Convert to 24-hour format
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
            
            # Round minute to nearest 15
            rounded_minute = round(minute / 15) * 15
            if rounded_minute == 60:
                hour += 1
                rounded_minute = 0
            
            # Ensure hour is within valid range
            hour = hour % 24
            
            return f"{hour:02d}:{rounded_minute:02d}"
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse time: {time_str} - {e}")
            # Default to 7:00 PM if parsing fails
            return "19:00"
    
    @staticmethod
    def generate_time_slots(target_date: date) -> List[str]:
        """
        Generate all available time slots for a given date.
        
        Args:
            target_date: The date to generate slots for
        
        Returns:
            List of time strings in HH:MM format (e.g., ["11:00", "11:15", ...])
        """
        slots = []
        current_time = datetime.combine(target_date, reservation_config.OPENING_TIME)
        closing_time = datetime.combine(target_date, reservation_config.CLOSING_TIME)
        
        while current_time <= closing_time:
            slots.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=reservation_config.SLOT_INTERVAL_MINUTES)
        
        return slots
    
    @staticmethod
    async def calculate_available_capacity(
        booking_date: date,
        booking_time: str,
        dining_duration: int = 90
    ) -> int:
        """
        Calculate available capacity for a specific time slot.
        
        Args:
            booking_date: Date of the reservation
            booking_time: Time in HH:MM format
            dining_duration: Duration of dining in minutes
        
        Returns:
            Number of available seats
        """
        # Parse booking time
        try:
            hour, minute = map(int, booking_time.split(':'))
            booking_time_obj = time(hour, minute)
        except (ValueError, AttributeError):
            logger.error(f"Invalid booking time format: {booking_time}")
            return 0
        
        # Get max capacity for this time
        max_capacity = reservation_config.get_max_capacity_for_time(booking_time_obj)
        
        # Calculate time range this reservation would occupy
        booking_datetime = datetime.combine(booking_date, booking_time_obj)
        end_datetime = booking_datetime + timedelta(minutes=dining_duration)
        
        # Get all active reservations that overlap with this time range
        overlapping_reservations = await MongoDB.get_reservations_for_slot(
            booking_date,
            booking_time,
            dining_duration
        )
        
        # Calculate occupied capacity
        occupied_capacity = sum(
            reservation.get('party_size', 0)
            for reservation in overlapping_reservations
            if reservation.get('status') == 'confirmed'
        )
        
        available = max_capacity - occupied_capacity
        
        logger.info(
            f"Availability check: {booking_date} {booking_time} - "
            f"Max: {max_capacity}, Occupied: {occupied_capacity}, Available: {available}"
        )
        
        return available
    
    @staticmethod
    async def get_available_slots(
        booking_date: date,
        party_size: int,
        preferred_time: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Get available time slots for a given date and party size.
        
        Args:
            booking_date: Date to check availability
            party_size: Number of people in the party
            preferred_time: Optional preferred time in HH:MM format (will search ±60 min)
        
        Returns:
            List of available slots with format:
            [{"time": "19:00", "available_capacity": 45, "distance_minutes": 0}, ...]
        """
        available_slots = []
        
        # Generate all time slots for the day
        all_slots = ReservationService.generate_time_slots(booking_date)
        
        # If preferred time provided, calculate search window
        search_slots = all_slots
        if preferred_time:
            try:
                pref_hour, pref_minute = map(int, preferred_time.split(':'))
                pref_datetime = datetime.combine(booking_date, time(pref_hour, pref_minute))
                
                # Filter slots within ±60 minutes
                window = reservation_config.ALTERNATIVE_TIME_WINDOW_MINUTES
                search_slots = []
                for slot in all_slots:
                    slot_hour, slot_minute = map(int, slot.split(':'))
                    slot_datetime = datetime.combine(booking_date, time(slot_hour, slot_minute))
                    diff_minutes = abs((slot_datetime - pref_datetime).total_seconds() / 60)
                    
                    if diff_minutes <= window:
                        search_slots.append(slot)
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse preferred time: {preferred_time}")
                search_slots = all_slots
        
        # Check availability for each slot
        for slot in search_slots:
            capacity = await ReservationService.calculate_available_capacity(
                booking_date,
                slot,
                reservation_config.DEFAULT_DINING_DURATION
            )
            
            if capacity >= party_size:
                # Calculate distance from preferred time (for sorting)
                distance = 0
                if preferred_time:
                    try:
                        pref_hour, pref_minute = map(int, preferred_time.split(':'))
                        slot_hour, slot_minute = map(int, slot.split(':'))
                        pref_datetime = datetime.combine(booking_date, time(pref_hour, pref_minute))
                        slot_datetime = datetime.combine(booking_date, time(slot_hour, slot_minute))
                        distance = abs((slot_datetime - pref_datetime).total_seconds() / 60)
                    except:
                        pass
                
                available_slots.append({
                    'time': slot,
                    'available_capacity': capacity,
                    'distance_minutes': distance
                })
        
        # Sort by distance from preferred time (if provided), otherwise by time
        if preferred_time:
            available_slots.sort(key=lambda x: x['distance_minutes'])
        else:
            available_slots.sort(key=lambda x: x['time'])
        
        return available_slots
    
    @staticmethod
    def parse_natural_date(date_str: str) -> Optional[date]:
        """
        Parse natural language date inputs.
        
        Args:
            date_str: Date string like "today", "tomorrow", "friday", "dec 6", etc.
        
        Returns:
            date object or None if parsing fails
        """
        date_str = date_str.strip().lower()
        today = date.today()
        
        # Handle relative dates
        if date_str in ['today', 'tonight']:
            return today
        elif date_str == 'tomorrow':
            return today + timedelta(days=1)
        elif 'next week' in date_str:
            return today + timedelta(days=7)
        
        # Handle day names (find next occurrence)
        days_of_week = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in days_of_week.items():
            if day_name in date_str:
                # Calculate days until next occurrence
                current_day = today.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week if it's the same day
                return today + timedelta(days=days_ahead)
        
        # Try to parse as specific date (basic formats)
        # This is simplified - in production you'd use dateutil.parser
        try:
            # Try YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
        
        try:
            # Try MM/DD/YYYY
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            pass
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    @staticmethod
    def format_time_for_speech(time_str: str) -> str:
        """
        Format time for natural speech output.
        
        Args:
            time_str: Time in HH:MM format (24-hour)
        
        Returns:
            Natural language time (e.g., "7:00 PM", "11:30 AM")
        """
        try:
            hour, minute = map(int, time_str.split(':'))
            
            # Convert to 12-hour format
            period = "AM"
            if hour >= 12:
                period = "PM"
                if hour > 12:
                    hour -= 12
            elif hour == 0:
                hour = 12
            
            # Format with or without minutes
            if minute == 0:
                return f"{hour} {period}"
            else:
                return f"{hour}:{minute:02d} {period}"
                
        except (ValueError, AttributeError):
            return time_str
    
    @staticmethod
    def format_date_for_speech(target_date: date) -> str:
        """
        Format date for natural speech output.
        
        Args:
            target_date: Date object
        
        Returns:
            Natural language date (e.g., "Friday, December 6th")
        """
        # Get day name and month name
        day_name = target_date.strftime("%A")
        month_name = target_date.strftime("%B")
        day = target_date.day
        
        # Add ordinal suffix
        if 10 <= day % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        
        return f"{day_name}, {month_name} {day}{suffix}"

