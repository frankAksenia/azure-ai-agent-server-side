import os

from azure.ai.projects import AIProjectClient

def create_project_client(credential) -> AIProjectClient:
    project_endpoint = os.environ.get("AZURE_PROJECT_ENDPOINT")

    if not project_endpoint:
        raise ValueError("AZURE_PROJECT_ENDPOINT environment variable is not set.")
    
    return AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
    )

