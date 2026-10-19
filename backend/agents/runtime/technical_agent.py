from agent_framework.foundry import FoundryAgent
from tools.knowledge_tools import create_knowledge_tools

def create_technical_agent(project_endpoint, credential, config, *, retrieval_service):

    return FoundryAgent(
        project_endpoint=project_endpoint,
        agent_name=config["technical_agent"]["name"],
        description=config["technical_agent"]["description"],
        credential=credential,
        tools=create_knowledge_tools(retrieval_service, "technical"),
    )
