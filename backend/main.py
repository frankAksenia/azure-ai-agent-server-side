from contextlib import AsyncExitStack, asynccontextmanager, closing
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from api.routes import router
from agents.runtime.factory import create_agents
from clients.credential import create_credential
from config.settings import get_config, get_database_path, load_environment
from services.conversation_manager import ConversationManager
from services.content_safety_service import get_content_safety_service
from services.chat_service import ChatService
from services.embedding_service import EmbeddingService
from services.retrieval_service import RetrievalService
from storage.database import connect, require_database
from storage.vector_store import CosmosVectorStore


def require_customer_record(customer_id, database_path):
    with closing(connect(database_path)) as connection:
        if connection.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is None:
            raise RuntimeError(f"Configured customer ID does not exist: {customer_id}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_environment()
    config = get_config()
    project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
    if not project_endpoint:
        raise RuntimeError("AZURE_PROJECT_ENDPOINT is not set")

    customer_id = os.getenv("DEMO_CUSTOMER_ID", "CUS-001").strip()
    if not customer_id:
        raise RuntimeError("DEMO_CUSTOMER_ID must not be blank.")
    database_path = get_database_path()
    await run_in_threadpool(require_database, database_path)
    await run_in_threadpool(require_customer_record, customer_id, database_path)
    conversation_manager = await run_in_threadpool(ConversationManager, database_path)

    async with AsyncExitStack() as resources:
        credential = create_credential()
        resources.push_async_callback(run_in_threadpool, credential.close)

        embeddings = await run_in_threadpool(EmbeddingService, credential)
        resources.push_async_callback(run_in_threadpool, embeddings.close)
        vector_store = await run_in_threadpool(CosmosVectorStore, credential)
        resources.push_async_callback(run_in_threadpool, vector_store.close)
        retrieval = RetrievalService(embeddings, vector_store)

        content_safety = None
        if os.getenv("CONTENT_SAFETY_ENDPOINT"):
            content_safety = await run_in_threadpool(get_content_safety_service, credential)
            resources.push_async_callback(run_in_threadpool, content_safety.close)

        def agent_factory(customer_id, conversation_id):
            return create_agents(
                project_endpoint=project_endpoint,
                credential=credential,
                config=config,
                customer_id=customer_id,
                session_id=conversation_id,
                database_path=database_path,
                retrieval_service=retrieval,
            )

        app.state.customer_id = customer_id
        app.state.chat_service = ChatService(
            agent_factory=agent_factory,
            conversation_manager=conversation_manager,
            content_safety_service=content_safety,
            database_path=database_path,
        )
        yield


app = FastAPI(title="Azure Multi-Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
