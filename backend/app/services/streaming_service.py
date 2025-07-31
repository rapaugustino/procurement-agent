"""
Streaming service for real-time API responses using Server-Sent Events (SSE).
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
import uuid

class StreamingService:
    """Service for managing streaming responses and real-time updates."""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
    
    async def create_stream(self, stream_id: Optional[str] = None) -> str:
        """Create a new streaming session."""
        if not stream_id:
            stream_id = str(uuid.uuid4())
        
        self.active_streams[stream_id] = {
            "created_at": datetime.utcnow(),
            "status": "active",
            "events": []
        }
        
        return stream_id
    
    async def send_event(self, stream_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Send an event to a specific stream."""
        if stream_id in self.active_streams:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "data": data
            }
            self.active_streams[stream_id]["events"].append(event)
    
    async def close_stream(self, stream_id: str) -> None:
        """Close a streaming session."""
        if stream_id in self.active_streams:
            self.active_streams[stream_id]["status"] = "closed"
    
    async def format_sse_event(self, event_type: str, data: Dict[str, Any], event_id: Optional[str] = None) -> str:
        """Format data as Server-Sent Event."""
        sse_data = []
        
        if event_id:
            sse_data.append(f"id: {event_id}")
        
        sse_data.append(f"event: {event_type}")
        sse_data.append(f"data: {json.dumps(data)}")
        sse_data.append("")  # Empty line to end the event
        
        return "\n".join(sse_data)
    
    async def stream_generator(self, stream_id: str) -> AsyncGenerator[str, None]:
        """Generate streaming events for a specific stream."""
        last_event_index = 0
        
        while stream_id in self.active_streams:
            stream_data = self.active_streams[stream_id]
            
            # Send any new events
            events = stream_data["events"][last_event_index:]
            for event in events:
                sse_event = await self.format_sse_event(
                    event["event_type"],
                    event["data"],
                    f"{stream_id}_{last_event_index}"
                )
                yield sse_event
                last_event_index += 1
            
            # Check if stream is closed
            if stream_data["status"] == "closed":
                # Send final event
                final_event = await self.format_sse_event(
                    "stream_closed",
                    {"message": "Stream completed"},
                    f"{stream_id}_final"
                )
                yield final_event
                break
            
            # Wait before checking for new events
            await asyncio.sleep(0.1)
    
    async def stream_rag_response(self, stream_id: str, query: str, conversation_id: str) -> AsyncGenerator[str, None]:
        """Stream RAG agent response with progress updates."""
        try:
            # Send initial event
            yield await self.format_sse_event("started", {
                "message": "Processing your question...",
                "query": query,
                "conversation_id": conversation_id
            })
            
            # Send search event
            yield await self.format_sse_event("searching", {
                "message": "Searching knowledge base...",
                "step": "document_retrieval"
            })
            
            await asyncio.sleep(0.5)  # Simulate search time
            
            # Send generation event
            yield await self.format_sse_event("generating", {
                "message": "Generating response...",
                "step": "ai_processing"
            })
            
            # This would be replaced with actual streaming from the RAG agent
            # For now, we'll simulate chunked response
            response_chunks = [
                "Procurement policies are",
                " guidelines that ensure",
                " fair and transparent",
                " purchasing processes",
                " within organizations."
            ]
            
            full_response = ""
            for i, chunk in enumerate(response_chunks):
                full_response += chunk
                await asyncio.sleep(0.3)  # Simulate AI generation time
                
                yield await self.format_sse_event("chunk", {
                    "content": chunk,
                    "partial_response": full_response,
                    "chunk_index": i
                })
            
            # Send completion event
            yield await self.format_sse_event("completed", {
                "message": "Response generated successfully",
                "final_response": full_response,
                "conversation_id": conversation_id
            })
            
        except Exception as e:
            yield await self.format_sse_event("error", {
                "message": f"Error processing request: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def stream_workflow_response(self, stream_id: str, workflow_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream multi-agent workflow response with step-by-step updates."""
        try:
            # Send workflow started event
            yield await self.format_sse_event("workflow_started", {
                "message": "Starting multi-agent workflow...",
                "workflow_id": workflow_data.get("workflow_id"),
                "user_id": workflow_data.get("user_id")
            })
            
            # Send supervisor analysis event
            yield await self.format_sse_event("supervisor_analyzing", {
                "message": "Supervisor agent analyzing request...",
                "step": "task_analysis"
            })
            
            await asyncio.sleep(1)
            
            # Send tool selection event
            yield await self.format_sse_event("tool_selected", {
                "message": "Selected procurement RAG agent tool",
                "tool": "procurement_rag_agent_tool",
                "step": "tool_selection"
            })
            
            # Send tool execution event
            yield await self.format_sse_event("tool_executing", {
                "message": "Executing RAG agent query...",
                "step": "tool_execution"
            })
            
            await asyncio.sleep(2)
            
            # Simulate response chunks
            response_chunks = [
                "Based on the procurement policies",
                " in our knowledge base,",
                " here are the key guidelines",
                " you should follow..."
            ]
            
            full_response = ""
            for i, chunk in enumerate(response_chunks):
                full_response += chunk
                await asyncio.sleep(0.4)
                
                yield await self.format_sse_event("response_chunk", {
                    "content": chunk,
                    "partial_response": full_response,
                    "chunk_index": i
                })
            
            # Send workflow completion event
            yield await self.format_sse_event("workflow_completed", {
                "message": "Workflow completed successfully",
                "final_result": full_response,
                "steps_completed": 1,
                "total_steps": 1
            })
            
        except Exception as e:
            yield await self.format_sse_event("workflow_error", {
                "message": f"Workflow error: {str(e)}",
                "error_type": type(e).__name__
            })

# Global streaming service instance
streaming_service = StreamingService()
