"""
Configuration settings for restaurant agent
"""
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

class Settings:
    """Application settings"""
    
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL",
        "mongodb+srv://saaibahmed456_db_user:bWAxtCTj0PfBTRTD@restauran-agent.ivbb37l.mongodb.net/pakistani_restaurant?retryWrites=true&w=majority"
    )
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "pakistani_restaurant")
    
    # Collections
    CUSTOMERS_COLLECTION: str = "customers"
    ORDERS_COLLECTION: str = "orders"
    
    # LiveKit Configuration
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")
    
    # AI APIs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    CARTESIA_API_KEY: str = os.getenv("CARTESIA_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

settings = Settings()

