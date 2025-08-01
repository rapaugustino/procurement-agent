"""
Agent Tools for the multi-agent system.
Provides tool-based interfaces for agent capabilities with HITL support.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool

from .base_agent import AgentState
from .rag_agent import RAGAgent
from .communication_agent import CommunicationAgent


class ToolResult(BaseModel):
    """Standard result format for tool execution"""
    success: bool
    data: Dict[str, Any] = {}
    message: str = ""
    error: Optional[str] = None
    requires_approval: bool = False


class AgentToolManager:
    """Manages tool-based access to agents with HITL capabilities"""
    
    def __init__(self):
        self.rag_agent = RAGAgent()
        self.communication_agent = CommunicationAgent()
    
    async def procurement_rag_tool(self, query: str) -> ToolResult:
        """
        Tool interface for the RAG agent.
        Answers questions about procurement policies, contracts, vendors, etc.
        """
        try:
            state = AgentState(
                agent_id="rag_agent",
                task_id="tool_query",
                data={"question": query}
            )
            
            response = await self.rag_agent.process(state)
            
            if response.success:
                return ToolResult(
                    success=True,
                    data=response.data,
                    message=response.data.get("answer", response.message)
                )
            else:
                return ToolResult(
                    success=False,
                    error=response.error,
                    message="Failed to process procurement query"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Error executing procurement RAG tool"
            )
    
    async def draft_communication_tool(self, context: str, recipient: str, 
                                     request: str, communication_type: str = "email") -> ToolResult:
        """
        Tool interface for drafting communications.
        Creates professional emails or Teams messages.
        """
        try:
            state = AgentState(
                agent_id="communication_agent",
                task_id="draft_tool",
                data={
                    "action": "draft",
                    "context": context,
                    "recipient": recipient,
                    "request": request,
                    "type": communication_type
                }
            )
            
            response = await self.communication_agent.process(state)
            
            if response.success:
                return ToolResult(
                    success=True,
                    data=response.data,
                    message=f"Draft created for {recipient}",
                    requires_approval=False  # Drafting doesn't require approval
                )
            else:
                return ToolResult(
                    success=False,
                    error=response.error,
                    message="Failed to draft communication"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Error executing draft communication tool"
            )
    
    async def send_communication_tool(self, draft: str, recipient: str, 
                                    approved: bool = False, user_access_token: str = None,
                                    user_email: str = None, user_name: str = None) -> ToolResult:
        """
        Tool interface for sending communications.
        REQUIRES HUMAN APPROVAL - this is a critical action.
        """
        try:
            # This tool ALWAYS requires approval
            state = AgentState(
                agent_id="communication_agent",
                task_id="send_communication",
                data={
                    "action": "send",
                    "draft": draft,
                    "recipient": recipient,
                    "approved": approved,
                    "user_access_token": user_access_token,
                    "user_email": user_email,
                    "user_name": user_name
                }
            )
            
            response = await self.communication_agent.process(state)
            
            if response.success:
                return ToolResult(
                    success=True,
                    data=response.data,
                    message=response.message
                )
            else:
                return ToolResult(
                    success=False,
                    error=response.error,
                    message=response.message,
                    requires_approval=not approved
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Error in send communication tool: {str(e)}"
            )


# Global tool manager instance
tool_manager = AgentToolManager()


# LangChain tool definitions for use with LLM
@tool
async def procurement_rag_agent_tool(query: str) -> str:
    """
    Use this tool to answer any questions about University of Washington procurement policies,
    contracts, vendors, or related procedures.
    
    Args:
        query: The procurement-related question to answer
    """
    result = await tool_manager.procurement_rag_tool(query)
    if result.success:
        return result.message
    else:
        return f"Error: {result.error or result.message}"


@tool
async def draft_communication_tool(context: str, recipient: str, request: str, 
                                 communication_type: str = "email") -> str:
    """
    Use this tool to draft a professional email or Teams message.
    Provide the context for the message, the recipient's name or role, and a clear request.
    
    Args:
        context: Background information and context for the communication
        recipient: Name or role of the person receiving the message
        request: What you want to request or communicate
        communication_type: Type of communication ("email" or "teams")
    """
    result = await tool_manager.draft_communication_tool(
        context, recipient, request, communication_type
    )
    if result.success:
        draft = result.data.get("draft", "")
        return f"Draft created:\n\n{draft}"
    else:
        return f"Error: {result.error or result.message}"


@tool
async def send_communication_tool(draft: str, recipient: str = "", 
                                 user_access_token: str = None, user_email: str = None, 
                                 user_name: str = None) -> str:
    """
    Use this tool ONLY AFTER a draft has been created AND the human user has given their
    explicit approval to send it. Sends the communication on behalf of the user.
    
    CRITICAL: This tool requires human approval and will be interrupted for review.
    
    Args:
        draft: The complete draft message to send
        recipient: The recipient of the message (optional if included in draft)
        user_access_token: User's access token for Graph API (optional)
        user_email: User's email address (optional)
        user_name: User's display name (optional)
    """
    # This tool always requires approval - the supervisor will handle the interrupt
    result = await tool_manager.send_communication_tool(
        draft=draft, 
        recipient=recipient, 
        approved=False,
        user_access_token=user_access_token,
        user_email=user_email,
        user_name=user_name
    )
    
    if result.requires_approval:
        return f"APPROVAL_REQUIRED: {result.message}"
    elif result.success:
        return result.message
    else:
        return f"Error: {result.error or result.message}"


# List of all available tools
AVAILABLE_TOOLS = [
    procurement_rag_agent_tool,
    draft_communication_tool,
    send_communication_tool
]


def get_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available tools"""
    return {
        "procurement_rag_agent_tool": "Answers questions about procurement policies and procedures",
        "draft_communication_tool": "Drafts professional emails and Teams messages",
        "send_communication_tool": "Sends communications (requires human approval)"
    }


def get_critical_tools() -> list:
    """Get list of tools that require human approval"""
    return ["send_communication_tool"]
