import logging

from agent_framework.orchestrations import MagenticBuilder

from agents.runtime.factory import SpecialistAgents
from prompts.magentic import FINAL_ANSWER_PROMPT, PROGRESS_LEDGER_PROMPT


logger = logging.getLogger(__name__)


def create_workflow(specialist_agents: SpecialistAgents):
    """
    Create the Magentic multi-agent orchestration workflow.

    The manager coordinates the specialist agents and dynamically
    delegates tasks based on their capabilities.
    """

    logger.info("Creating Magentic workflow...")

    workflow = MagenticBuilder(
        manager_agent=specialist_agents.manager_agent,
        progress_ledger_prompt=PROGRESS_LEDGER_PROMPT,
        final_answer_prompt=FINAL_ANSWER_PROMPT,
        max_round_count=5,
        max_stall_count=3,
        max_reset_count=2,
        participants=[
            specialist_agents.support_agent,
            specialist_agents.billing_agent,
            specialist_agents.technical_agent
        ],
    ).build()

    logger.info("Magentic workflow created successfully.")

    return workflow
