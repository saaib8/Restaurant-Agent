"""
Pakistani Restaurant Voice Agent - Main Entry Point
Phone-based customer tracking with MongoDB
"""
import logging
import os
import ssl
import certifi

# Set SSL certificate paths BEFORE any imports that use SSL
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['CURL_CA_BUNDLE'] = certifi.where()

# Create SSL context with certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Patch aiohttp to use our SSL context (LiveKit uses aiohttp internally)
# Note: This patching approach is deprecated but necessary for SSL cert issues
import aiohttp
import warnings
warnings.filterwarnings('ignore', message='Inheritance.*ClientSession.*discouraged')

from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import silero, noise_cancellation

from restaurant_agent.agents import GreeterAgent, OrderAgent
from restaurant_agent.agents.base_agent import UserData
from restaurant_agent.services import MenuService, MongoDB

# Setup logging - detailed for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('restaurant_agent.log')
    ]
)
logger = logging.getLogger("restaurant-agent")
logger.info("="*80)
logger.info("🍽️  RESTAURANT AGENT STARTING - Logging all conversations")
logger.info("="*80)


async def entrypoint(ctx: JobContext):
    """Main entry point for the restaurant agent"""
    
    # Connect to database
    await MongoDB.connect_db()
    
    # Get menu summary for agent instructions (not full menu - too long)
    menu_summary = MenuService.get_menu_summary()
    
    # Initialize user data
    userdata = UserData()
    
    # Create agents
    greeter = GreeterAgent(menu_text=menu_summary)
    order_agent = OrderAgent(menu_text=menu_summary)
    
    # Register agents
    userdata.agents = {
        "greeter": greeter,
        "order": order_agent,
    }
    
    # TODO: Extract phone number from LiveKit participant metadata
    # When you integrate phone system:
    # participant = await ctx.wait_for_participant()
    # metadata = json.loads(participant.metadata) if participant.metadata else {}
    # userdata.customer_phone = metadata.get('caller_phone')
    
    # Create session
    session = AgentSession[UserData](
        userdata=userdata,
        stt="assemblyai",  # AssemblyAI STT (better for accents)
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        max_tool_steps=10,
    )
    
    logger.info("🎙️ Starting restaurant agent session")
    
    # Start session with greeter agent
    await session.start(
        agent=greeter,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

