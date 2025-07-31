"""
API routes for agent interactions.
Provides endpoints for M365 Teams integration and multi-agent workflows.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import asyncio
from datetime import datetime

from ..agents.supervisor_agent import SupervisorAgent, TaskType
from ..agents.base_agent import AgentState, AgentResponse
from ..agents.agent_tools import tool_manager, get_critical_tools
from ..services.hitl_service import hitl_service
from ..services.streaming_service import streaming_service

router = APIRouter(prefix="/agents", tags=["agents"])

# Global supervisor instance
supervisor = SupervisorAgent()


class QueryRequest(BaseModel):
    """Request model for agent queries"""
    question: str
    conversation_id: Optional[str] = "default"
    task_type: Optional[TaskType] = TaskType.GENERAL_INQUIRY
    metadata: Optional[Dict[str, Any]] = {}


class WorkflowRequest(BaseModel):
    """Request model for workflow execution"""
    workflow_definition: Dict[str, Any]
    conversation_id: Optional[str] = "default"


class QueryResponse(BaseModel):
    """Response model for agent queries"""
    task_id: str
    success: bool
    answer: str
    sources: List[Dict[str, Any]] = []
    agent_used: str
    processing_time: float
    conversation_id: str
    error: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Process a query through the multi-agent system.
    Designed for M365 Teams integration.
    """
    start_time = datetime.utcnow()
    task_id = str(uuid.uuid4())
    
    try:
        # Create agent state
        state = AgentState(
            agent_id="supervisor",
            task_id=task_id,
            data={
                "question": request.question,
                "task_type": request.task_type,
                "conversation_id": request.conversation_id,
                **request.metadata
            }
        )
        
        # Process through supervisor
        response = await supervisor.process(state)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return QueryResponse(
            task_id=task_id,
            success=True,
            answer=response.content,
            sources=response.sources,
            agent_used=response.agent_used,
            processing_time=processing_time,
            conversation_id=request.conversation_id
        )
        
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return QueryResponse(
            task_id=task_id,
            success=False,
            answer="",
            agent_used="supervisor",
            processing_time=processing_time,
            conversation_id=request.conversation_id,
            error=f"Internal error: {str(e)}"
        )


@router.post("/query/stream")
async def stream_query_agent(request: QueryRequest):
    """
    Stream a query response through the multi-agent system with real-time updates.
    Returns Server-Sent Events (SSE) for real-time feedback.
    """
    stream_id = str(uuid.uuid4())
    
    async def generate_stream():
        try:
            # Send initial event
            yield await streaming_service.format_sse_event("started", {
                "message": "Processing your question...",
                "query": request.question,
                "conversation_id": request.conversation_id,
                "stream_id": stream_id
            })
            
            # Send supervisor analysis event
            yield await streaming_service.format_sse_event("supervisor_analyzing", {
                "message": "Supervisor agent analyzing request...",
                "step": "task_analysis"
            })
            
            # Create agent state
            task_id = str(uuid.uuid4())
            state = AgentState(
                agent_id="supervisor",
                task_id=task_id,
                data={
                    "question": request.question,
                    "task_type": request.task_type,
                    "conversation_id": request.conversation_id,
                    **request.metadata
                }
            )
            
            # Send agent selection event
            yield await streaming_service.format_sse_event("agent_selected", {
                "message": "Selected appropriate agent for your query",
                "step": "agent_selection"
            })
            
            # Send processing event
            yield await streaming_service.format_sse_event("processing", {
                "message": "Processing through specialized agent...",
                "step": "agent_processing"
            })
            
            # Process through supervisor (this would be enhanced to support streaming in real implementation)
            response = await supervisor.process(state)
            
            # Get the response content from the correct field
            response_text = response.data.get("answer", response.message) if response.success else response.message
            
            if response.success and response_text:
                # Simulate streaming the response in chunks
                chunk_size = max(1, len(response_text) // 10)  # Split into ~10 chunks
                
                partial_response = ""
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    partial_response += chunk
                    
                    yield await streaming_service.format_sse_event("chunk", {
                        "content": chunk,
                        "partial_response": partial_response,
                        "chunk_index": i // chunk_size
                    })
                    
                    # Small delay to simulate real streaming
                    await asyncio.sleep(0.1)
                
                # Send completion event
                yield await streaming_service.format_sse_event("completed", {
                    "message": "Response generated successfully",
                    "final_response": response_text,
                    "sources": response.data.get("sources", []),
                    "agent_used": response.data.get("target_agent", response.agent_id),
                    "conversation_id": request.conversation_id,
                    "success": True
                })
            else:
                # Handle error case
                yield await streaming_service.format_sse_event("completed", {
                    "message": "Request completed with issues",
                    "final_response": response.message or "No response generated",
                    "sources": [],
                    "agent_used": response.agent_id,
                    "conversation_id": request.conversation_id,
                    "success": False,
                    "error": response.error
                })
            
        except Exception as e:
            yield await streaming_service.format_sse_event("error", {
                "message": f"Error processing request: {str(e)}",
                "error_type": type(e).__name__
            })
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/workflow")
async def execute_workflow(request: WorkflowRequest):
    """
    Execute a multi-step workflow through the supervisor agent.
    """
    task_id = str(uuid.uuid4())
    
    try:
        # Create agent state for workflow
        state = AgentState(
            agent_id="supervisor",
            task_id=task_id,
            data={
                "task_type": TaskType.MULTI_STEP_WORKFLOW,
                "workflow": request.workflow_definition,
                "conversation_id": request.conversation_id
            }
        )
        
        # Execute workflow
        response = await supervisor.process(state)
        
        return {
            "task_id": task_id,
            "success": response.success,
            "workflow_result": response.data,
            "message": response.message,
            "error": response.error
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/status")
async def get_agent_status():
    """
    Get status of all agents in the system.
    Useful for monitoring and debugging.
    """
    return supervisor.get_agent_status()


@router.get("/capabilities")
async def get_system_capabilities():
    """
    Get all capabilities available in the multi-agent system.
    """
    return {
        "capabilities": supervisor.get_capabilities(),
        "task_types": [task_type.value for task_type in TaskType],
        "available_agents": list(supervisor.agents.keys())
    }


# M365 Teams specific endpoints
@router.post("/teams/message")
async def handle_teams_message(request: QueryRequest):
    """
    Handle messages from Microsoft Teams.
    Optimized for Teams bot integration.
    """
    # Add Teams-specific metadata
    request.metadata.update({
        "source": "microsoft_teams",
        "timestamp": datetime.now().isoformat()
    })
    
    # Process through standard query endpoint
    return await query_agent(request)


@router.post("/teams/adaptive-card")
async def create_adaptive_card_response(request: QueryRequest):
    """
    Create an Adaptive Card response for Teams.
    Returns formatted card JSON for rich Teams integration.
    """
    # Process the query first
    response = await query_agent(request)
    
    if not response.success:
        # Error card
        card = {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "❌ Error Processing Request",
                    "weight": "Bolder",
                    "color": "Attention"
                },
                {
                    "type": "TextBlock",
                    "text": response.error or "An unknown error occurred",
                    "wrap": True
                }
            ]
        }
    else:
        # Success card with answer and sources
        body = [
            {
                "type": "TextBlock",
                "text": "🤖 Procurement Assistant",
                "weight": "Bolder",
                "size": "Medium"
            },
            {
                "type": "TextBlock",
                "text": response.answer,
                "wrap": True,
                "spacing": "Medium"
            }
        ]
        
        # Add sources if available
        if response.sources:
            body.append({
                "type": "TextBlock",
                "text": "📚 Sources:",
                "weight": "Bolder",
                "spacing": "Medium"
            })
            
            for source in response.sources[:3]:  # Limit to 3 sources for card
                body.append({
                    "type": "TextBlock",
                    "text": f"• {source.get('title', 'Unknown Source')}",
                    "wrap": True,
                    "size": "Small"
                })
        
        # Add metadata
        body.append({
            "type": "FactSet",
            "facts": [
                {
                    "title": "Agent:",
                    "value": response.agent_used
                },
                {
                    "title": "Processing Time:",
                    "value": f"{response.processing_time:.2f}s"
                }
            ],
            "spacing": "Medium"
        })
        
        card = {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": body
        }
    
    return {
        "card": card,
        "response_data": response
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for the agent system"""
    try:
        # Test supervisor functionality
        test_state = AgentState(
            agent_id="supervisor",
            task_id="health_check",
            data={"question": "health check"}
        )
        
        # Quick capability check
        capabilities = supervisor.get_capabilities()
        agent_status = supervisor.get_agent_status()
        
        return {
            "status": "healthy",
            "agents_registered": len(supervisor.agents),
            "capabilities_count": len(capabilities),
            "supervisor_status": agent_status.get("supervisor_status", "unknown")
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


# Conversation management endpoints
@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history for a specific conversation ID"""
    try:
        # Access memory service through RAG agent
        rag_agent = supervisor.agents.get("rag_agent")
        if rag_agent and hasattr(rag_agent, 'memory_service'):
            rag_agent.memory_service.clear_conversation(conversation_id)
            return {"message": f"Conversation {conversation_id} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Memory service not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {str(e)}")


@router.get("/conversations")
async def list_conversations():
    """List all active conversation IDs"""
    try:
        rag_agent = supervisor.agents.get("rag_agent")
        if rag_agent and hasattr(rag_agent, 'memory_service'):
            conversations = rag_agent.memory_service.get_all_conversations()
            return {"conversations": conversations}
        else:
            return {"conversations": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")
