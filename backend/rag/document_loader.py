from rag.models import DocumentChunk


SUPPORTED_DOMAINS = {
    "support",
    "billing",
    "technical",
}

def load_domain_documents(data_directory, domain, document_service) -> list[DocumentChunk]:

    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"Unsupported domain: {domain}")

    directory = data_directory / domain

    if not directory.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {directory}")

    chunks: list[DocumentChunk] = []

    for pdf_path in sorted(
        directory.rglob("*.pdf")
    ):
        print(f"Analyzing {pdf_path.name}...")

        document_chunks = (
            document_service.analyze_pdf(
                path=pdf_path,
                domain=domain,
            )
        )

        chunks.extend(document_chunks)

    return chunks


def load_all_documents(data_directory, document_service) -> list[DocumentChunk]:

    chunks: list[DocumentChunk] = []

    for domain in sorted(SUPPORTED_DOMAINS):
        chunks.extend(
            load_domain_documents(
                data_directory=data_directory,
                domain=domain,
                document_service=document_service,
            )
        )

    return chunks
