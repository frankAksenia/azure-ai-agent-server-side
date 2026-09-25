import asyncio
import logging
import os

from dotenv import load_dotenv

from agents.runtime.factory import create_agents
from clients.foundry import get_credential
from config.settings import get_config
from orchestration.magentic_workflow import create_workflow
from services.content_safety_service import get_content_safety_service
from services.conversation_service import ConversationService


async def run_workflow(specialist_agents):

    conversation = ConversationService()

    try:
        content_safety = get_content_safety_service()

    except ValueError:
        content_safety = None

        print("Content Safety is not configured; continuing without moderation.")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit", "bye"}:
            break

        if not user_input:
            continue

        if content_safety:
            moderation = content_safety.analyze_text(user_input)

            if not moderation["safe"]:
                print("Your message was blocked by Content Safety filters.")
                continue

        task = conversation.build_task(user_input)

        workflow_agent = create_workflow(specialist_agents)

        try:
            result = await workflow_agent.run(messages=task, stream=False)

        except Exception:
            logging.exception("Magentic workflow execution failed.")
            print("The workflow could not complete the request.")
            continue

        final_text = getattr(result, "text", str(result))

        if content_safety:
            output_moderation = (content_safety.analyze_text(final_text))

            if not output_moderation["safe"]:
                print("The agent response was blocked by Content Safety filters.")
                continue

        await conversation.add_turn(user_input=user_input,assistant_output=final_text)

        print(final_text)


def main():
    logging.basicConfig(level=logging.WARNING, format=("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    logging.getLogger("agent_framework_orchestrations").setLevel(logging.DEBUG)

    logging.getLogger("orchestration.magentic_workflow").setLevel(logging.INFO)

    load_dotenv()

    config = get_config()

    project_endpoint = os.environ.get("AZURE_PROJECT_ENDPOINT")

    if not project_endpoint:
        raise RuntimeError("AZURE_PROJECT_ENDPOINT is not set")

    credential = get_credential()

    agents = create_agents(
        project_endpoint=project_endpoint,
        credential=credential,
        config=config,
    )

    asyncio.run(run_workflow(agents))

if __name__ == "__main__":
    main()