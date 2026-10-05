from contextlib import asynccontextmanager
import os
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from agents.runtime.factory import create_agents
from clients.foundry import get_credential
from config.settings import get_config
from services.conversation_manager import ConversationManager
from services.content_safety_service import get_content_safety_service
from services.chat_service import ChatService


@asynccontextmanager
async def lifespan(app: FastAPI):

    load_dotenv()

    config = get_config()

    project_endpoint = os.environ.get("AZURE_PROJECT_ENDPOINT")

    if not project_endpoint:
        raise RuntimeError("AZURE_PROJECT_ENDPOINT is not set")

    credential = get_credential()

    customer_id = "CUS-001" 
    session_id = uuid4().hex

    agents = create_agents(
        project_endpoint=project_endpoint,
        credential=credential,
        config=config,
        customer_id=customer_id,
        session_id=session_id,
    )

    conversation_manager = ConversationManager()

    try:
        content_safety_service = get_content_safety_service()
    except ValueError:
        content_safety_service = None

    app.state.chat_service = ChatService(
        agents=agents,
        conversation_manager=conversation_manager,
        content_safety_service=content_safety_service,
    )

    yield


app = FastAPI(
    title="Azure Multi-Agent API",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}

