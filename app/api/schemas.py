"""
API Schemas

Request and response models for the chatbot API.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Chat request model.
    """

    message: str = Field(
        ...,
        min_length=1,
        description="User message",
    )
    session_id: str = Field(
        ...,
        min_length=1,
        description="Browser session identifier for in-memory chat history",
    )


class ChatResponse(BaseModel):
    """
    Chat response model.
    """

    response: str = Field(
        ...,
        description="Assistant response",
    )