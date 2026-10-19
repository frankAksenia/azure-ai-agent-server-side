import hashlib
import math
import os
from contextlib import ExitStack
from numbers import Real

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from clients.cosmosdb_client import create_cosmosdb_client
from rag.models import DocumentChunk, RetrievedChunk


class CosmosVectorStore:
    EMBEDDING_DIMENSIONS = 1536
    ACTIVE_GENERATION_ID = "active-corpus-generation"

    def __init__(self, credential):
        database_name = os.getenv("AZURE_COSMOS_DATABASE", "agent-knowledge")
        container_name = os.getenv("AZURE_COSMOS_CONTAINER", "knowledge")
        self._resources = ExitStack()
        try:
            self._client = create_cosmosdb_client(credential)
            self._resources.callback(self._client.close)
            database = self._client.get_database_client(database_name)
            self._container = database.get_container_client(container_name)
        except BaseException:
            self._resources.close()
            raise

    def close(self):
        self._resources.close()

    def upsert_chunk(self, chunk: DocumentChunk, embedding: list[float], generation: str):
        item_id = hashlib.sha256(f"{generation}:{chunk.id}".encode("utf-8")).hexdigest()
        self._container.upsert_item(body={
            "id": item_id,
            "chunkId": chunk.id,
            "type": "chunk",
            "generation": generation,
            "domain": chunk.domain,
            "content": chunk.text,
            "source": chunk.source,
            "page": chunk.page,
            "embedding": embedding,
        })

    def activate_generation(self, domain, generation) :
        self._container.upsert_item(body={
            "id": self.ACTIVE_GENERATION_ID,
            "domain": domain,
            "type": "corpus_manifest",
            "generation": generation,
        })

    def get_active_generation(self, domain):
        try:
            manifest = self._container.read_item(item=self.ACTIVE_GENERATION_ID, partition_key=domain)
        except CosmosResourceNotFoundError:
            return None
        generation = manifest.get("generation")
        return generation

    def search(self, embedding: list[float], domain: str, limit: int = 5) -> list[RetrievedChunk]:
        generation = self.get_active_generation(domain)
        if generation is None:
            return []
        items = self._container.query_items(
            query=f"""
                SELECT TOP {limit}
                    c.chunkId AS id, c.domain, c.content, c.source,
                    c.page,
                    VectorDistance(c.embedding, @embedding) AS score
                FROM c
                WHERE c.domain = @domain
                  AND c.generation = @generation
                  AND c.type = 'chunk'
                ORDER BY VectorDistance(c.embedding, @embedding)
            """,
            parameters=[
                {"name": "@embedding", "value": embedding},
                {"name": "@domain", "value": domain},
                {"name": "@generation", "value": generation},
            ],
            partition_key=domain,
        )
        return [RetrievedChunk(
            id=item["id"],
            content=item["content"],
            source=item["source"],
            page=item["page"],
            domain=item["domain"],
            score=item["score"],
        ) for item in items]
