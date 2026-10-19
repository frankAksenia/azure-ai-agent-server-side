import os

from azure.ai.contentsafety import ContentSafetyClient

def create_content_safety_client(credential) -> ContentSafetyClient:
    endpoint = os.environ.get("CONTENT_SAFETY_ENDPOINT")

    if not endpoint:
        raise ValueError("CONTENT_SAFETY_ENDPOINT environment variable is not set.")

    return ContentSafetyClient(
        endpoint=endpoint,
        credential=credential,
    )
