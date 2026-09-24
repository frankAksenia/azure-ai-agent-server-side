import os
import asyncio
from clients.foundry import  create_project_client, get_credential
from config.settings import get_config
from agents.deployment.factory import deploy_agents
from agents.runtime.factory import create_agents
from orchestration.magentic_workflow import create_workflow
from services.content_safety_service import get_content_safety_service

from dotenv import load_dotenv
load_dotenv()


async def run_workflow(workflow_agent):

    session = workflow_agent.create_session()

    try:
        content_safety = get_content_safety_service()
    except ValueError:
        content_safety = None
        print("Content Safety is not configured; continuing without moderation.")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit", "bye"}:
            break

        if content_safety:
            moderation = content_safety.analyze_text(user_input)
            if not moderation["safe"]:
                print("Your message was blocked by Content Safety filters.")
                continue

        result = await workflow_agent.run(messages=user_input, session=session, stream=False)
        final_text = getattr(result, "text", str(result))

        if content_safety:
            output_moderation = content_safety.analyze_text(final_text)
            if not output_moderation["safe"]:
                print("The agent response was blocked by Content Safety filters.")
                continue

        print(final_text)

def main():
    config = get_config()
    project_endpoint = os.environ.get("AZURE_PROJECT_ENDPOINT")
    if not project_endpoint:
        raise RuntimeError("AZURE_PROJECT_ENDPOINT is not set")

    credential = get_credential()
    project_client = create_project_client()

    with project_client:
        deploy_agents(project_client=project_client, config=config, tools=[])

    agents = create_agents(
        project_endpoint=project_endpoint,
        credential=credential,
        config=config,
    )

    workflow_agent = create_workflow(agents)

    asyncio.run(run_workflow(workflow_agent))

if __name__ == "__main__":
    main()