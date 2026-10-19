"""Create new Foundry agent versions explicitly with `python deploy.py`."""

import logging
import os

from agents.deployment.factory import deploy_agents
from clients.credential import create_credential
from clients.project_client import create_project_client
from config.settings import get_config, load_environment


def main():
    load_environment()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not os.environ.get("AZURE_PROJECT_ENDPOINT"):
        raise RuntimeError("AZURE_PROJECT_ENDPOINT is not set")

    credential = create_credential()
    try:
        config = get_config()
        with create_project_client(credential) as project_client:
            deploy_agents(project_client=project_client, config=config, tools=[])
    finally:
        credential.close()

    print("Agent deployment completed. Start the API with: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
