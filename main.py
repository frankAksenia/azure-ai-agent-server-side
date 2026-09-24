import os
import asyncio
from clients.foundry import create_credential, create_project_client
from config.settings import get_config
from agents.deployment.factory import deploy_agents
from agents.runtime.factory import create_agents
from orchestration.magentic_workflow import create_workflow

async def run_workflow(agent):
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        result = await agent.run(user_input)
        print(getattr(result, "text", str(result)))

def main():
    config = get_config()
    project_endpoint = os.environ.get("AZURE_PROJECT_ENDPOINT")
    if not project_endpoint:
        raise RuntimeError("AZURE_PROJECT_ENDPOINT is not set")

    credential = create_credential()
    project_client = create_project_client()

    with project_client:
        deploy_agents(project_client=project_client, config=config, tools=[])

    agents = create_agents(
        project_endpoint=project_endpoint,
        credential=credential,
        config=config,
    )

    workflow = create_workflow(agents)
    asyncio.run(run_workflow(workflow))

if __name__ == "__main__":
    main()