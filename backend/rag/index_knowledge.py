import time
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4

from azure.core.exceptions import ServiceResponseTimeoutError

from config.settings import load_environment
from clients.credential import create_credential

from rag.document_loader import SUPPORTED_DOMAINS, load_all_documents
from services.document_intelligence_service import DocumentIntelligenceService
from services.embedding_service import EmbeddingService
from storage.vector_store import CosmosVectorStore


DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "data"

MAX_RETRIES = 3


def main():
    load_environment()
    with ExitStack() as resources:
        credential = create_credential()
        resources.callback(credential.close)
        document_service = DocumentIntelligenceService(credential)
        resources.callback(document_service.close)
        embedding_service = EmbeddingService(credential)
        resources.callback(embedding_service.close)
        vector_store = CosmosVectorStore(credential)
        resources.callback(vector_store.close)

        print("Analyzing PDF documents...")
        chunks = load_all_documents(
            data_directory=DATA_DIRECTORY,
            document_service=document_service,
        )
        print(f"Extracted {len(chunks)} searchable pages.")
        generation = uuid4().hex

        for index, page in enumerate(chunks, start=1):
            print(f"[{index}/{len(chunks)}] {page.domain} / {page.source} / page {page.page}")
            embedding = embedding_service.embed(page.text)
            _retry_cosmos(lambda: vector_store.upsert_chunk(
                chunk=page, embedding=embedding, generation=generation,
            ))

        for domain in sorted(SUPPORTED_DOMAINS):
            _retry_cosmos(lambda: vector_store.activate_generation(domain, generation))

        print(f"Indexing completed. {len(chunks)} chunks published in generation {generation}.")


def _retry_cosmos(operation: Callable[[], None]) -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            operation()
            return
        except ServiceResponseTimeoutError:
            if attempt == MAX_RETRIES:
                raise
            delay = 2 ** attempt
            print(f"Cosmos timeout. Retrying in {delay}s ({attempt}/{MAX_RETRIES})...")
            time.sleep(delay)


if __name__ == "__main__":
    main()
