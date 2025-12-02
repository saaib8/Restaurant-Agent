"""
Reservation model - Table reservations
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, date


class Reservation(BaseModel):
    """Customer reservation"""
    phone: str = Field(..., description="Customer's phone number")
    customer_name: Optional[str] = Field(None, description="Customer's name")
    
    party_size: int = Field(..., description="Number of people", ge=1, le=15)
    
    booking_date: date = Field(..., description="Reservation date (YYYY-MM-DD)")
    booking_time: str = Field(..., description="Reservation time in 24-hour format (HH:MM)")
    
    dining_duration: int = Field(default=90, description="Expected dining duration in minutes")
    
    status: Literal["confirmed", "cancelled", "completed", "no_show"] = "confirmed"
    
    special_requests: Optional[str] = Field(None, description="Special requests or notes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('booking_date')
    @classmethod
    def validate_booking_date(cls, v: date) -> date:
        """Ensure booking date is today or in the future"""
        if v < date.today():
            raise ValueError("Booking date cannot be in the past")
        return v
    
    @field_validator('booking_time')
    @classmethod
    def validate_booking_time(cls, v: str) -> str:
        """Validate time format (HH:MM in 24-hour format)"""
        try:
            # Try to parse to ensure valid format
            hour, minute = v.split(':')
            h, m = int(hour), int(minute)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            return v
        except (ValueError, AttributeError):
            raise ValueError("Booking time must be in HH:MM format (24-hour)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+1-555-123-4567",
                "customer_name": "Ali Khan",
                "party_size": 4,
                "booking_date": "2025-12-06",
                "booking_time": "19:00",
                "dining_duration": 90,
                "status": "confirmed",
                "special_requests": "Window seat preferred"
            }
        }

