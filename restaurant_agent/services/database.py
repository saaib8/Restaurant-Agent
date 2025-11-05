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

