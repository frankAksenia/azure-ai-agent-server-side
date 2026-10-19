import logging

from azure.ai.projects.models import PromptAgentDefinition
from prompts.technical import build_system_prompt
from azure.core.exceptions import HttpResponseError
from tools.knowledge_tools import create_knowledge_tool_definitions


logger = logging.getLogger(__name__)

def deploy_technical_agent(project_client, config, tools):
    """
    Create a technical agent that handles technical support tasks.
    """

    system_prompt = build_system_prompt(
        include_tool_rules=True,
        )

    try:
        logger.info("Creating Technical Agent...")
        technical_agent = project_client.agents.create_version(
            agent_name=config["technical_agent"]["name"],
            description=config["technical_agent"]["description"],
            definition=PromptAgentDefinition(
                model=config["technical_agent"]["model"],
                instructions=system_prompt,
                tools=create_knowledge_tool_definitions("technical"),
                temperature=config["technical_agent"]["temperature"],
                )
            )
        logger.info("Technical Agent returned: name=%s version=%s id=%s", technical_agent.name, technical_agent.version, technical_agent.id)
        return technical_agent
    except HttpResponseError as e:
        logger.error("Failed to create Technical Agent: %s", e)
        raise
    except Exception as e:
        logger.error("An unexpected error occurred while creating Technical Agent: %s", e)
        raise
