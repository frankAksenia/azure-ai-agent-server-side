import os

from azure.cosmos import CosmosClient

def create_cosmosdb_client(credential) -> CosmosClient:
    endpoint = os.environ.get("AZURE_COSMOS_ENDPOINT")

    if not endpoint:
        raise ValueError("AZURE_COSMOS_ENDPOINT environment variable is not set.")

    return CosmosClient(
        url=endpoint,
        credential=credential,
    )
