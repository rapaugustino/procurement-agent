"""
Base Agent class for the multi-agent system.
Provides common functionality for all agents in the procurement system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_core.documents import Document


class AgentState(BaseModel):
    """Base state model for agent communication"""
    agent_id: str
    task_id: str
    status: str = "pending"
    data: Dict[str, Any] = {}
    error: Optional[str] = None


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    agent_id: str
    task_id: str
    success: bool
    data: Dict[str, Any] = {}
    message: str = ""
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Provides common interface and functionality.
    """
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = "initialized"
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentResponse:
        """
        Main processing method that each agent must implement.
        
        Args:
            state: Current agent state with task data
            
        Returns:
            AgentResponse with results
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides.
        Used by supervisor for task routing.
        """
        pass
    
    def validate_input(self, state: AgentState) -> bool:
        """Validate input state before processing"""
        return state.agent_id is not None and state.task_id is not None
    
    def create_response(self, task_id: str, success: bool, data: Dict[str, Any] = None, 
                       message: str = "", error: str = None) -> AgentResponse:
        """Helper method to create standardized responses"""
        return AgentResponse(
            agent_id=self.agent_id,
            task_id=task_id,
            success=success,
            data=data or {},
            message=message,
            error=error
        )
