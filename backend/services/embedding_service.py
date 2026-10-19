import os
from contextlib import ExitStack
from urllib.parse import urlsplit

from clients.project_client import create_project_client


class EmbeddingService:
    EMBEDDING_DIMENSIONS = 1536

    def __init__(self, credential):
        self._deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "").strip()
        project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT", "").strip()
        if not self._deployment:
            raise ValueError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT environment variable is not set.")
        if not project_endpoint:
            raise ValueError("AZURE_PROJECT_ENDPOINT environment variable is not set.")
        endpoint = urlsplit(project_endpoint)
        if endpoint.scheme != "https" or not endpoint.netloc:
            raise ValueError("AZURE_PROJECT_ENDPOINT must be an HTTPS project endpoint.")

        self._resources = ExitStack()
        try:
            self._project_client = create_project_client(credential)
            self._resources.callback(self._project_client.close)
            self._client = self._project_client.get_openai_client(
                base_url=f"{endpoint.scheme}://{endpoint.netloc}/openai/v1/",
            )
            self._resources.callback(self._client.close)
        except BaseException:
            self._resources.close()
            raise

    def close(self):
        self._resources.close()

    def embed(self, text) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text.")
        response = self._client.embeddings.create(
            model=self._deployment,
            input=text,
            dimensions=self.EMBEDDING_DIMENSIONS,
        )
        embedding = response.data[0].embedding
        if len(embedding) != self.EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"Expected {self.EMBEDDING_DIMENSIONS} dimensions, "
                f"received {len(embedding)}."
            )
        return embedding
