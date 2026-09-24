import logging

from azure.ai.projects.models import PromptAgentDefinition
from prompts.support import build_system_prompt
from azure.core.exceptions import HttpResponseError
from data.knowledge_base import build_knowledge_context


logger = logging.getLogger(__name__)

def deploy_support_agent(project_client, config, tools):
    """
    Create a support agent that handles customer support tasks.
    """

    knowledge_context = build_knowledge_context("support")
    system_prompt = build_system_prompt(
        include_tool_rules=False,
        additional_instructions=[knowledge_context] if knowledge_context else None,
        )

    try:
        logger.info("Creating Support Agent...")
        support_agent = project_client.agents.create_version(
            agent_name=config["support_agent"]["name"],
            description=config["support_agent"]["description"],
            definition=PromptAgentDefinition(
                model=config["support_agent"]["model"],
                instructions=system_prompt,
                temperature=config["support_agent"]["temperature"],
                )
            )
        logger.info("Support Agent created successfully with ID: %s", support_agent.id)
        return support_agent
    except HttpResponseError as e:
        logger.error("Failed to create Support Agent: %s", e)
        raise
    except Exception as e:
        logger.error("An unexpected error occurred while creating Support Agent: %s", e)
        raise
            
    