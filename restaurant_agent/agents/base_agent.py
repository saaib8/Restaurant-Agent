"""
Base agent class with shared functionality
"""
import logging
from dataclasses import dataclass, field
from typing import Optional
from livekit.agents.voice import Agent, RunContext
from livekit.agents.llm import ChatContext
import yaml

logger = logging.getLogger("restaurant-agent")
logger.setLevel(logging.INFO)


@dataclass
class UserData:
    """User data for the session - phone-based customer tracking"""
    
    # Customer info (from caller ID or asked)
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    
    # Current order
    order_items: list[dict] = field(default_factory=list)
    total_amount: float = 0.0
    
    # Bulk order processing
    pending_bulk_order: list[dict] = field(default_factory=list)
    
    # Agent management
    agents: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    
    def summarize(self) -> str:
        """Summarize user data for AI context"""
        data = {
            "customer_phone": self.customer_phone or "not provided",
            "customer_name": self.customer_name or "not provided",
            "order_items": self.order_items or [],
            "total_amount": f"Rs. {self.total_amount:.0f}" if self.total_amount else "Rs. 0",
        }
        return yaml.dump(data, default_flow_style=False)


RunContext_T = RunContext[UserData]


class BaseAgent(Agent):
    """Base agent with shared functionality"""
    
    async def on_enter(self) -> None:
        """Called when agent becomes active"""
        agent_name = self.__class__.__name__
        logger.info(f"🎯 Entering {agent_name}")
        
        userdata: UserData = self.session.userdata
        chat_ctx = self.chat_ctx.copy()
        
        # Add previous agent's chat history
        if isinstance(userdata.prev_agent, Agent):
            truncated_chat_ctx = userdata.prev_agent.chat_ctx.copy(
                exclude_instructions=True, exclude_function_call=False
            ).truncate(max_items=6)
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [
                item for item in truncated_chat_ctx.items 
                if item.id not in existing_ids
            ]
            chat_ctx.items.extend(items_copy)
        
        # Add user data context
        chat_ctx.add_message(
            role="system",
            content=f"You are {agent_name}. Current session data:\n{userdata.summarize()}",
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply(tool_choice="none")
    
    async def on_assistant_speech_committed(self, message: str) -> None:
        """Called when agent finishes speaking - log what was said"""
        agent_name = self.__class__.__name__
        logger.info(f"🗣️  [{agent_name}] AGENT SAID: {message}")
    
    async def on_user_speech_committed(self, message: str) -> None:
        """Called when user finishes speaking - log what was heard"""
        agent_name = self.__class__.__name__
        logger.info(f"👤 [USER] Customer said: {message}")
    
    async def on_function_calls_finished(self, called_functions: list) -> None:
        """Called after function execution - ensure agent generates a response"""
        agent_name = self.__class__.__name__
        logger.info(f"🔧 [{agent_name}] Function calls finished: {[f.function_info.name for f in called_functions]}")
        # Force the agent to generate a reply after function execution
        # This ensures the function return values are spoken
    
    async def _transfer_to_agent(
        self, 
        name: str, 
        context: RunContext_T
    ) -> tuple[Agent, str]:
        """Transfer to another agent"""
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.agents[name]
        userdata.prev_agent = current_agent
        
        logger.info(f"🔀 Transferring from {current_agent.__class__.__name__} to {name}")
        return next_agent, f"Transferring to {name}."

