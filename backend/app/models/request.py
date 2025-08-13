"""Request models for the application."""

from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for agent queries."""

    question: str
    conversation_id: Optional[str] = None
