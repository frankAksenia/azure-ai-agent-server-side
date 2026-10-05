
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


credential = DefaultAzureCredential()


def get_credential():
    """Return the shared Azure credential used across this application."""
    return credential


def create_project_client():
    """Create an AIProjectClient using the shared credential."""
    project_endpoint = os.environ.get("AZURE_PROJECT_ENDPOINT")

    assert project_endpoint, "AZURE_PROJECT_ENDPOINT environment variable is not set."

    return AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
    )

