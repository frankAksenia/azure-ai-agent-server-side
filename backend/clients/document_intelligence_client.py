import os

from azure.ai.documentintelligence import DocumentIntelligenceClient

def create_document_intelligence_client(credential) -> DocumentIntelligenceClient:
    endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")

    if not endpoint:
        raise ValueError("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable is not set.")

    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=credential,
    )
