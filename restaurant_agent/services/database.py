"""
MongoDB connection and database operations
"""
import os
import ssl
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import certifi

# Set SSL env vars before any MongoDB operations
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from ..config import settings
from datetime import datetime, date, timedelta


class MongoDB:
    """MongoDB connection manager for phone-based customer tracking"""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB with SSL fallback"""
        
        # First attempt: Use certifi certificates
        try:
            print("🔌 Connecting to MongoDB with certifi certificates...")
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=10,
                retryWrites=True,
            )
            # Test connection
            await cls.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
            
            # Create indexes
            db = cls.client[settings.DATABASE_NAME]
            
            # Customers collection - index on phone
            customers_collection = db[settings.CUSTOMERS_COLLECTION]
            await customers_collection.create_index("phone", unique=True)
            
            # Orders collection - index on phone and created_at
            orders_collection = db[settings.ORDERS_COLLECTION]
            await orders_collection.create_index("phone")
            await orders_collection.create_index("created_at")
            
            # Reservations collection - indexes on phone, booking_date, and status
            await cls.create_reservation_indexes()
            
            print("✅ Database indexes created")
            return
            
        except Exception as e:
            print(f"⚠️  First connection attempt failed: {str(e)[:100]}")
            
            # Second attempt: Try with system SSL certificates
            try:
                print("🔌 Trying with system SSL certificates...")
                cls.client = AsyncIOMotorClient(
                    settings.MONGODB_URL,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    maxPoolSize=10,
                    retryWrites=True,
                )
                await cls.client.admin.command('ping')
                print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
                
                # Create indexes
                db = cls.client[settings.DATABASE_NAME]
                customers_collection = db[settings.CUSTOMERS_COLLECTION]
                await customers_collection.create_index("phone", unique=True)
                orders_collection = db[settings.ORDERS_COLLECTION]
                await orders_collection.create_index("phone")
                await orders_collection.create_index("created_at")
                
                # Reservations indexes
                await cls.create_reservation_indexes()
                
                print("✅ Database indexes created")
                return
                
            except Exception as e2:
                print(f"❌ MongoDB connection failed: {str(e2)[:100]}")
                print(f"⚠️  Continuing without database (orders won't be saved)")
                cls.client = None
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client is not None:
            cls.client.close()
            print("✅ MongoDB connection closed")
    
    @classmethod
    def get_db(cls):
        """Get database instance"""
        if cls.client is None:
            return None
        return cls.client[settings.DATABASE_NAME]
    
    @classmethod
    def get_customers_collection(cls):
        """Get customers collection"""
        db = cls.get_db()
        if db is None:
            return None
        return db[settings.CUSTOMERS_COLLECTION]
    
    @classmethod
    def get_orders_collection(cls):
        """Get orders collection"""
        db = cls.get_db()
        if db is None:
            return None
        return db[settings.ORDERS_COLLECTION]
    
    @classmethod
    async def get_customer_by_phone(cls, phone: str) -> dict | None:
        """Get customer by phone number"""
        collection = cls.get_customers_collection()
        if collection is None:
            return None
        return await collection.find_one({"phone": phone})
    
    @classmethod
    async def save_order(cls, order_data: dict) -> bool:
        """Save order to database"""
        collection = cls.get_orders_collection()
        if collection is None:
            print("⚠️  Database not available, order not saved")
            return False
        
        try:
            await collection.insert_one(order_data)
            print(f"✅ Order saved for {order_data.get('phone')}")
            return True
        except Exception as e:
            print(f"❌ Error saving order: {e}")
            return False
    
    # ============= RESERVATION METHODS =============
    
    @classmethod
    def get_reservations_collection(cls):
        """Get reservations collection"""
        db = cls.get_db()
        if db is None:
            return None
        return db[settings.RESERVATIONS_COLLECTION]
    
    @classmethod
    async def create_reservation_indexes(cls):
        """Create indexes for reservations collection"""
        collection = cls.get_reservations_collection()
        if collection is None:
            return
        
        try:
            # Compound index for phone and booking date
            await collection.create_index([("phone", 1), ("booking_date", 1)])
            
            # Compound index for date, time, and status (for availability queries)
            await collection.create_index([
                ("booking_date", 1),
                ("booking_time", 1),
                ("status", 1)
            ])
            
            # Index on status for quick filtering
            await collection.create_index("status")
            
            print("✅ Reservation indexes created")
        except Exception as e:
            print(f"⚠️  Error creating reservation indexes: {e}")
    
    @classmethod
    async def save_reservation(cls, reservation_data: dict) -> bool:
        """Save reservation to database"""
        collection = cls.get_reservations_collection()
        if collection is None:
            print("⚠️  Database not available, reservation not saved")
            return False
        
        try:
            await collection.insert_one(reservation_data)
            print(f"✅ Reservation saved for {reservation_data.get('phone')} "
                  f"on {reservation_data.get('booking_date')} at {reservation_data.get('booking_time')}")
            return True
        except Exception as e:
            print(f"❌ Error saving reservation: {e}")
            return False
    
    @classmethod
    async def get_reservations_by_phone(cls, phone: str, date_from: date = None) -> list:
        """
        Get reservations for a phone number.
        
        Args:
            phone: Customer's phone number
            date_from: Only get reservations from this date onwards (default: today)
        
        Returns:
            List of reservation documents
        """
        collection = cls.get_reservations_collection()
        if collection is None:
            return []
        
        if date_from is None:
            date_from = date.today()
        
        try:
            # Convert date to datetime for comparison
            date_from_dt = datetime.combine(date_from, datetime.min.time())
            
            reservations = await collection.find({
                "phone": phone,
                "booking_date": {"$gte": date_from_dt},
                "status": "confirmed"
            }).sort("booking_date", 1).to_list(length=100)
            
            return reservations
        except Exception as e:
            print(f"❌ Error fetching reservations: {e}")
            return []
    
    @classmethod
    async def get_reservations_for_slot(
        cls,
        booking_date: date,
        booking_time: str,
        dining_duration: int = 90
    ) -> list:
        """
        Get all reservations that overlap with a specific time slot.
        
        Args:
            booking_date: Date of the slot
            booking_time: Time of the slot in HH:MM format
            dining_duration: Duration in minutes (default: 90)
        
        Returns:
            List of overlapping reservation documents
        """
        collection = cls.get_reservations_collection()
        if collection is None:
            return []
        
        try:
            # Parse the booking time
            hour, minute = map(int, booking_time.split(':'))
            slot_start = datetime.combine(booking_date, datetime.min.time().replace(hour=hour, minute=minute))
            slot_end = slot_start + timedelta(minutes=dining_duration)
            
            # Generate all time slots that would overlap
            # A reservation overlaps if:
            # (reservation_start < slot_end) AND (reservation_end > slot_start)
            
            # For simplicity, get all reservations for this date
            # Then filter in Python (more complex query would be needed for exact overlap)
            date_start = datetime.combine(booking_date, datetime.min.time())
            date_end = datetime.combine(booking_date, datetime.max.time())
            
            reservations = await collection.find({
                "booking_date": {
                    "$gte": date_start,
                    "$lte": date_end
                },
                "status": "confirmed"
            }).to_list(length=1000)
            
            # Filter for overlaps
            overlapping = []
            for reservation in reservations:
                # Parse reservation time
                res_time = reservation.get('booking_time', '00:00')
                res_hour, res_minute = map(int, res_time.split(':'))
                res_start = datetime.combine(
                    booking_date,
                    datetime.min.time().replace(hour=res_hour, minute=res_minute)
                )
                res_duration = reservation.get('dining_duration', 90)
                res_end = res_start + timedelta(minutes=res_duration)
                
                # Check overlap: (res_start < slot_end) AND (res_end > slot_start)
                if res_start < slot_end and res_end > slot_start:
                    overlapping.append(reservation)
            
            return overlapping
            
        except Exception as e:
            print(f"❌ Error fetching slot reservations: {e}")
            return []

