from azure.identity import DefaultAzureCredential

def create_credential() -> DefaultAzureCredential:
    return DefaultAzureCredential()
