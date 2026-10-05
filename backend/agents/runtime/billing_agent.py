from agent_framework.foundry import FoundryAgent

from backend.tools.billing_tools import create_billing_tools
from backend.storage.database import DEFAULT_DATABASE_PATH


def  create_billing_agent(project_endpoint, credential, config, customer_id, session_id, database_path=DEFAULT_DATABASE_PATH):

    return FoundryAgent(
        project_endpoint=project_endpoint,
        agent_name=config["billing_agent"]["name"],
        description=config["billing_agent"]["description"],
        credential=credential,
        tools=create_billing_tools(customer_id, session_id, database_path=database_path),
    )
