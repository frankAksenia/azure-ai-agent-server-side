import logging

from azure.ai.projects.models import PromptAgentDefinition
from prompts.manager import build_system_prompt
from azure.core.exceptions import HttpResponseError


logger = logging.getLogger(__name__)

def deploy_manager_agent(project_client, config, tools):
    """
    Create a manager agent that handles managerial tasks.
    """

    system_prompt = build_system_prompt(
        include_tool_rules=False,
        additional_instructions=None
        )

    try:
        logger.info("Creating Manager Agent...")
        manager_agent = project_client.agents.create_version(
            agent_name=config["manager_agent"]["name"],
            description=config["manager_agent"]["description"],
            definition=PromptAgentDefinition(
                model=config["manager_agent"]["model"],
                instructions=system_prompt,
                temperature=config["manager_agent"]["temperature"],
                )
            )
        logger.info("Manager Agent created successfully with ID: %s", manager_agent.id)
        return manager_agent
    except HttpResponseError as e:
        logger.error("Failed to create Manager Agent: %s", e)
        raise
    except Exception as e:
        logger.error("An unexpected error occurred while creating Manager Agent: %s", e)
        raise
            
    