from rag.models import RetrievedChunk
from services.embedding_service import EmbeddingService
from storage.vector_store import CosmosVectorStore


class RetrievalService:

    VALID_DOMAINS = {
        "support",
        "billing",
        "technical",
    }

    def __init__(self, embedding_service: EmbeddingService, vector_store: CosmosVectorStore):
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    def search(self, query, domain, limit = 5) -> list[RetrievedChunk]:

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if domain not in self.VALID_DOMAINS:
            raise ValueError(f"Unsupported domain: {domain}")

        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 20:
            raise ValueError("Search limit must be an integer between 1 and 20.")

        embedding = self._embedding_service.embed(query)

        return self._vector_store.search(
            embedding=embedding,
            domain=domain,
            limit=limit,
        )
