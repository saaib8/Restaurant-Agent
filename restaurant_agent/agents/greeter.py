"""
Greeter Agent - Welcomes customers and routes to order taking
"""
import logging
from typing import Annotated
from pydantic import Field
from livekit.agents.llm import function_tool
from .base_agent import BaseAgent, RunContext_T

logger = logging.getLogger("restaurant-agent")


class GreeterAgent(BaseAgent):
    """Friendly restaurant greeter - welcomes and routes customers"""
    
    def __init__(self, menu_text: str) -> None:
        super().__init__(
            instructions=(
                "You are a warm and friendly receptionist at a fast food restaurant. "
                "Greet customers and welcome them warmly.\n\n"
                "Your job is to:\n"
                "1. Greet the customer warmly\n"
                "2. Ask if they'd like to place an order\n"
                "3. If they say YES, transfer them to the order agent\n"
                "4. If they say NO or they're not interested, politely say goodbye: "
                "'No problem! Feel free to call us whenever you're hungry. Have a great day!'\n\n"
                "VOICE FORMATTING:\n"
                "- This is a VOICE conversation, NOT text\n"
                "- NEVER use markdown formatting like **bold** or *italic*\n"
                "- NEVER use special characters: *, #, _, etc.\n"
                "- Speak naturally, as if talking to someone in person\n\n"
                "Be friendly, helpful, and professional!"
            ),
        )
        self.menu_text = menu_text
    
    @function_tool()
    async def to_order_agent(self, context: RunContext_T) -> tuple:
        """
        Transfer customer to order taking agent.
        Call this when customer wants to place an order or see the menu.
        """
        logger.info("📋 Greeter transferring to order agent")
        return await self._transfer_to_agent("order", context)

