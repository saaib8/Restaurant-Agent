"""
Order model - Customer orders
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class OrderItem(BaseModel):
    """Individual item in an order"""
    item_id: int
    item_name: str
    quantity: int = 1
    price: float
    special_instructions: Optional[str] = None


class Order(BaseModel):
    """Customer order"""
    phone: str = Field(..., description="Customer's phone number")
    customer_name: Optional[str] = Field(None, description="Customer's name")
    
    items: list[OrderItem] = Field(default_factory=list)
    total_amount: float = Field(default=0.0)
    
    status: Literal["pending", "confirmed", "preparing", "completed", "cancelled"] = "pending"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+923001234567",
                "customer_name": "John Doe",
                "items": [
                    {
                        "item_id": 1,
                        "item_name": "Margherita Pizza",
                        "quantity": 2,
                        "price": 899.0
                    }
                ],
                "total_amount": 1798.0,
                "status": "pending"
            }
        }

