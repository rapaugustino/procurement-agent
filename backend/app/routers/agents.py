"""
API router for handling agent-related requests, including streaming RAG queries.
"""

import asyncio
import uuid
import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ..agents.rag_agent import RAGAgent


class AgentQuery(BaseModel):
    """Request model for agent queries"""
    question: str
    conversation_id: Optional[str] = None

router = APIRouter()

# Initialize agents
# In a real app, you might use a dependency injection system
rag_agent = RAGAgent()

@router.post("/query/stream")
async def query_agent_stream(query: AgentQuery):
    """
    Handles a streaming query to the RAG agent.

    This endpoint consumes the async generator from the RAGAgent and streams
    its responses back to the client using Server-Sent Events (SSE).
    """
    question = query.question
    conversation_id = query.conversation_id or f"user_{uuid.uuid4()}"
    task_id = str(uuid.uuid4())

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    async def stream_generator():
        """Generator function that yields data from the RAG agent stream."""
        try:
            async for chunk in rag_agent.run(question, conversation_id, task_id):
                if isinstance(chunk, str):
                    # Format response as JSON for Teams frontend
                    response_data = {
                        "type": "chunk",
                        "content": chunk,
                        "task_id": task_id
                    }
                    yield json.dumps(response_data)
                else:
                    # Handle potential error dicts or other objects if needed
                    response_data = {
                        "type": "chunk", 
                        "content": str(chunk),
                        "task_id": task_id
                    }
                    yield json.dumps(response_data)
        except Exception as e:
            error_message = f"An error occurred during streaming: {e}"
            print(error_message)
            error_data = {
                "type": "error",
                "content": error_message,
                "task_id": task_id
            }
            yield json.dumps(error_data)

    return EventSourceResponse(stream_generator())
