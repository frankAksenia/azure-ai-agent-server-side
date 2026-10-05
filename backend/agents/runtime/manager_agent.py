from agent_framework.foundry import FoundryAgent

def create_manager_agent(project_endpoint, credential, config):

    return FoundryAgent(
        project_endpoint=project_endpoint,
        agent_name=config["manager_agent"]["name"],
        description=config["manager_agent"]["description"],
        credential=credential,
        tools=None,
    )
