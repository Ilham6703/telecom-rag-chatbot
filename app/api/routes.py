"""
API routes for the chatbot.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest, ChatResponse
from app.services.chat import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint used by the frontend and API clients.
    """

    service = ChatService(session_id=request.session_id)
    response = service.chat(request.message)
    return ChatResponse(response=response)


@router.post("/chat/stream")
def chat_stream_endpoint(request: ChatRequest):
    """Stream the assistant answer chunk by chunk to reduce perceived latency."""

    service = ChatService(session_id=request.session_id)

    def generate():
        for chunk in service.chat_stream(request.message):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")