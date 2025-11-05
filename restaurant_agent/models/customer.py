"""
Customer model - Phone-based customer tracking
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Customer(BaseModel):
    """Customer identified by phone number"""
    phone: str = Field(..., description="Customer's phone number (primary identifier)")
    name: Optional[str] = Field(None, description="Customer's name")
    
    # Order history
    total_orders: int = Field(default=0, description="Total number of orders")
    last_order_date: Optional[datetime] = Field(None, description="Last order timestamp")
    favorite_items: list[str] = Field(default_factory=list, description="Frequently ordered items")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+923001234567",
                "name": "Ahmed Khan",
                "total_orders": 5,
                "favorite_items": ["Chicken Biryani", "Mutton Karahi"]
            }
        }

