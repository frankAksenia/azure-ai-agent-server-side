
import os

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

def create_credential():
    """
    Creates and returns an instance of DefaultAzureCredential.
    """
    return DefaultAzureCredential()

def create_project_client():
    """
    Creates and returns an instance of AIProjectClient using the DefaultAzureCredential.
    """
    project_endpoint = os.environ.get("AZURE_PROJECT_ENDPOINT")

    assert project_endpoint, "AZURE_PROJECT_ENDPOINT environment variable is not set."

    credential = create_credential()
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
    )
    return project_client

