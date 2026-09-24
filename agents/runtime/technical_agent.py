from agent_framework.foundry import FoundryAgent

def create_technical_agent(project_endpoint, credential, config):

    return FoundryAgent(
        project_endpoint=project_endpoint,
        agent_name=config["technical_agent"]["name"],
        credential=credential,
        tools=None,
    )