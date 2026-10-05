from agents.deployment.billing_agent import deploy_billing_agent
from agents.deployment.support_agent import deploy_support_agent
from agents.deployment.technical_agent import deploy_technical_agent
from agents.deployment.manager_agent import deploy_manager_agent


def deploy_agents(project_client, config, tools):

    deploy_manager_agent(project_client, config, tools)

    deploy_support_agent(project_client, config, tools)

    deploy_billing_agent(project_client, config, tools)

    deploy_technical_agent(project_client, config, tools)
