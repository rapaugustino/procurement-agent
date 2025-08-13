"""
API endpoints for the RAG agent.

This module defines the routes for querying the RAG agent, including the
streaming endpoint for real-time responses.
"""

import logging
from functools import lru_cache
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from ..agents.rag_agent import RAGAgent
from ..models.request import QueryRequest

# Configure logging
logger = logging.getLogger(__name__)

# Create a new router for the agent endpoints
router = APIRouter()


@lru_cache
def get_rag_agent() -> RAGAgent:
    """
    Dependency function to get a cached RAGAgent instance.
    Using lru_cache ensures the agent is a singleton, created only once.
    """
    logger.info("Initializing RAGAgent singleton...")
    return RAGAgent()


@router.post("/query/stream")
async def stream_query(
    request: QueryRequest,
    rag_agent: RAGAgent = Depends(get_rag_agent),
) -> EventSourceResponse:
    """
    Streams the RAG agent's response for a given query.

    This endpoint consumes the async generator from the RAGAgent and streams
    the response back to the client chunk by chunk using Server-Sent Events (SSE).

    Args:
        request: The request body containing the user's question and conversation ID.
        rag_agent: The dependency-injected RAGAgent instance.

    Returns:
        An EventSourceResponse that streams the agent's response.
    """

    async def stream_generator() -> AsyncGenerator[ServerSentEvent, None]:
        """An async generator that yields Server-Sent Events."""
        try:
            async for chunk in rag_agent.stream_run(
                question=request.question, conversation_id=request.conversation_id
            ):
                yield ServerSentEvent(data=chunk)
        except Exception as e:
            logger.error(f"Error during stream for conversation {request.conversation_id}: {e}", exc_info=True)
            error_message = {"error": "An unexpected error occurred.", "details": str(e)}
            yield ServerSentEvent(data=str(error_message), event="error")

    return EventSourceResponse(stream_generator())
