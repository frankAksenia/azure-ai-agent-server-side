import logging

from azure.ai.projects.models import PromptAgentDefinition
from prompts.billing import build_system_prompt
from azure.core.exceptions import HttpResponseError
from data.knowledge_base import build_knowledge_context


logger = logging.getLogger(__name__)

def deploy_billing_agent(project_client, config, tools):
    """
    Create a billing agent that handles billing-related tasks.
    """

    knowledge_context = build_knowledge_context("billing")
    system_prompt = build_system_prompt(
        include_tool_rules=False,
        additional_instructions=[knowledge_context] if knowledge_context else None,
        )

    try:
        logger.info("Creating Billing Agent...")
        billing_agent = project_client.agents.create_version(
            agent_name=config["billing_agent"]["name"],
            description=config["billing_agent"]["description"],
            definition=PromptAgentDefinition(
                model=config["billing_agent"]["model"],
                instructions=system_prompt,
                temperature=config["billing_agent"]["temperature"],
                )
            )
        logger.info("Billing Agent created successfully with ID: %s", billing_agent.id)
        return billing_agent
    except HttpResponseError as e:
        logger.error("Failed to create Billing Agent: %s", e)
        raise
    except Exception as e:
        logger.error("An unexpected error occurred while creating Billing Agent: %s", e)
        raise
            
    