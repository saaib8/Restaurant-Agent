"""
Reservation system configuration
"""
from datetime import time


class ReservationConfig:
    """Restaurant reservation system configuration"""
    
    # Capacity Management
    TOTAL_CAPACITY = 50  # Total seats available
    
    # Operating Hours
    OPENING_TIME = time(11, 0)  # 11:00 AM
    CLOSING_TIME = time(23, 0)  # 11:00 PM
    
    # Time Slot Configuration
    SLOT_INTERVAL_MINUTES = 15  # Booking granularity (15-minute intervals)
    DEFAULT_DINING_DURATION = 90  # Average dining time in minutes
    
    # Capacity Limits
    PEAK_HOURS_START = time(19, 0)  # 7:00 PM
    PEAK_HOURS_END = time(21, 0)    # 9:00 PM
    PEAK_HOUR_CAPACITY_LIMIT = 1.00  # 100% of capacity during peak hours (full utilization)
    OFF_PEAK_CAPACITY_LIMIT = 1.00   # 100% of capacity during off-peak
    
    # Party Size Limits
    MIN_PARTY_SIZE = 1
    MAX_PARTY_SIZE = 50  # Maximum party size for standard bookings
    
    # Availability Search
    ALTERNATIVE_TIME_WINDOW_MINUTES = 60  # Search ±60 minutes for alternatives
    MAX_ALTERNATIVE_SUGGESTIONS = 3  # Show top 3 alternative slots
    
    @classmethod
    def get_max_capacity_for_time(cls, booking_time: time) -> int:
        """Get maximum bookable capacity for a specific time"""
        if cls.PEAK_HOURS_START <= booking_time < cls.PEAK_HOURS_END:
            return int(cls.TOTAL_CAPACITY * cls.PEAK_HOUR_CAPACITY_LIMIT)
        return int(cls.TOTAL_CAPACITY * cls.OFF_PEAK_CAPACITY_LIMIT)
    
    @classmethod
    def is_peak_hour(cls, booking_time: time) -> bool:
        """Check if given time is during peak hours"""
        return cls.PEAK_HOURS_START <= booking_time < cls.PEAK_HOURS_END


reservation_config = ReservationConfig()

