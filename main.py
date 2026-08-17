"""
Application Entry Point

Creates the FastAPI application and registers all API routes.
"""

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router
from app.utils.langsmith import initialize_langsmith

load_dotenv()
initialize_langsmith()


app = FastAPI(
    title="Telecom RAG Chatbot",
    description="Production-ready RAG chatbot for 3GPP Telecom Standards.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def health_check():
    """
    Health check endpoint.
    """

    return {
        "status": "healthy",
        "service": "Telecom RAG Chatbot",
    }