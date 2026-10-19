import hashlib
from pathlib import Path

from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult, DocumentContentFormat
from clients.document_intelligence_client import create_document_intelligence_client
from rag.models import DocumentChunk


class DocumentIntelligenceService:

    def __init__(self, credential):
        self._client = create_document_intelligence_client(credential)

    def analyze_pdf(self, path, domain) -> list[DocumentChunk]:

        with path.open("rb") as f:
            file_bytes = f.read()

        poller = self._client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=AnalyzeDocumentRequest(bytes_source=file_bytes),
            output_content_format=DocumentContentFormat.MARKDOWN,
            string_index_type="unicodeCodePoint",
        )

        result = poller.result()

        if not result.content:
            return []

        return self._build_page_records(
            result=result,
            source=path.as_posix(),
            domain=domain,
        )

    @staticmethod
    def _build_page_records(result: AnalyzeResult, source: str, domain: str) -> list[DocumentChunk]:

        chunks: list[DocumentChunk] = []
        content = result.content
        if not content:
            return chunks

        for page in result.pages or []:
            if not page.spans:
                continue

            page_text = "".join(
                content[span.offset:span.offset + span.length]
                for span in page.spans
            ).strip()

            if not page_text:
                continue

            identity = f"{domain}:{source}:{page.page_number}"
            chunks.append(
                DocumentChunk(
                    id=hashlib.sha256(identity.encode("utf-8")).hexdigest(),
                    text=page_text,
                    source=source,
                    page=page.page_number,
                    domain=domain,
                )
            )

        return chunks

    def close(self):
        self._client.close()
