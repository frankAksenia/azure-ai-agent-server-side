"""Create new Foundry agent versions explicitly with `python deploy.py`."""

import logging
import os

from dotenv import load_dotenv

from agents.deployment.factory import deploy_agents
from clients.foundry import create_project_client
from config.settings import get_config


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not os.environ.get("AZURE_PROJECT_ENDPOINT"):
        raise RuntimeError("AZURE_PROJECT_ENDPOINT is not set")

    config = get_config()
    with create_project_client() as project_client:
        deploy_agents(project_client=project_client, config=config, tools=[])

    print("Agent deployment completed. Start the chat with: python main.py")


if __name__ == "__main__":
    main()
