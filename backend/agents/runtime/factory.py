from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from storage.database import DEFAULT_DATABASE_PATH

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


@asynccontextmanager
async def create_agents(project_endpoint, credential, config, customer_id, session_id, database_path=DEFAULT_DATABASE_PATH, *, retrieval_service):
    async with AsyncExitStack() as resources:
        manager = await resources.enter_async_context(create_manager_agent(
            project_endpoint, credential, config,
        ))
        support = await resources.enter_async_context(create_support_agent(
            project_endpoint, credential, config, retrieval_service=retrieval_service,
        ))
        billing = await resources.enter_async_context(create_billing_agent(
            project_endpoint, credential, config,
            customer_id=customer_id, session_id=session_id,
            database_path=database_path, retrieval_service=retrieval_service,
        ))
        technical = await resources.enter_async_context(create_technical_agent(
            project_endpoint, credential, config, retrieval_service=retrieval_service,
        ))
        yield SpecialistAgents(support, billing, technical, manager)
