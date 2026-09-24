from dataclasses import dataclass

from agent_framework.foundry import FoundryAgent

from agents.runtime.billing_agent import create_billing_agent
from agents.runtime.manager_agent import create_manager_agent
from agents.runtime.support_agent import create_support_agent
from agents.runtime.technical_agent import create_technical_agent


@dataclass
class SpecialistAgents:
    support_agent: FoundryAgent
    billing_agent: FoundryAgent
    technical_agent: FoundryAgent
    manager_agent: FoundryAgent


def create_agents(project_endpoint, credential, config):

    return SpecialistAgents(
        support_agent=create_support_agent(
            project_endpoint,
            credential,
            config,
        ),
        billing_agent=create_billing_agent(
            project_endpoint,
            credential,
            config,
        ),
        technical_agent=create_technical_agent(
            project_endpoint,
            credential,
            config,
        ),
        manager_agent=create_manager_agent(
            project_endpoint,
            credential,
            config,
        )
    )