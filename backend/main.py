import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Multi-agent system chat interface app.",
    description="Implementation of a multi-agent system chat interface using FastAPI and Pydantic."
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str = Field(..., description="The message to send to the chat interface.")

class ChatResponse(BaseModel):
    message: str = Field(..., description="The message to send to the chat interface.")


@app.get("/api/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_agent(payload: ChatRequest):

    response_message = payload.message

    if not response_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    return ChatResponse(message=response_message)