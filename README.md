# Azure AI Agent Server Side

A Python customer-support assistant for a fictional Contoso Corporation, using Azure AI Foundry agents and Microsoft Agent Framework's Magentic orchestration. The current entry point is an interactive terminal chat.

## Current capabilities

| Capability | Implementation |
| --- | --- |
| Multi-agent coordination | A manager routes requests and coordinates three specialist agents. |
| Billing guidance | Answers questions about invoices, subscription changes, refunds, and billing policies. |
| Customer support | Provides account-access guidance, policy clarification, and escalation guidance. |
| Technical support | Provides API-latency troubleshooting and incident-triage guidance. |
| Local knowledge | Markdown documents are embedded in each specialist's instructions when its agent version is created. |
| Conversational context | Reuses one workflow session across messages during a terminal run. |
| Optional text moderation | Azure AI Content Safety checks user messages before execution and final responses before display. |
| Agent configuration | Agent names, descriptions, model deployment names, and temperatures are configured in YAML. |
| Infrastructure templates | Bicep and Make targets support provisioning the Azure resources. |

## How it works

1. Load `.env` and `config/config.yaml`, then authenticate with `DefaultAzureCredential`.
2. Create a new Foundry agent version for the manager and each specialist. Specialist instructions include their local Markdown knowledge.
3. Connect runtime agents to Foundry by their configured names and build the Magentic workflow.
4. Create a session and accept terminal input, optionally moderating each message.
5. Run the workflow, optionally moderate its final response, and print the result.

The workflow sets `max_round_count=5`, `max_stall_count=3`, and `max_reset_count=2`. Responses are requested with `stream=False`.

## Run locally

You need Python with support for the dependencies in `requirements.txt`, an Azure AI Foundry project, and a model deployment matching the configuration. The repository's local development environment uses Python 3.13; dependency versions are not pinned.

Your Azure identity needs permission to create and use agents in the project and, if moderation is enabled, analyse text with the Content Safety resource. The included infrastructure does not assign these permissions.

### 1. Install dependencies

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install python-dotenv
```

### 2. Configure endpoints and authentication

```bash
cp .env.example .env
az login
```

Edit `.env` with your resource endpoints:

| Variable | Required | Purpose |
| --- | --- | --- |
| `AZURE_PROJECT_ENDPOINT` | Yes | The actual project endpoint from your Foundry project. |
| `CONTENT_SAFETY_ENDPOINT` | No | Endpoint of the Azure AI Content Safety resource. Omit it or leave it empty to disable moderation. |

Authentication uses the shared `DefaultAzureCredential` in `clients/foundry.py`. The application does not use API keys. 


### 3. Check agent configuration

Edit [config/config.yaml](config/config.yaml) so each agent's `model` matches an available model deployment in your project. All four agents currently use `gpt-5.1`. The manager temperature is `0.3`; specialist temperatures are `0.5`.

### 4. Start the chat

```bash
python main.py
```

Example requests:

```text
You: What is the policy for changing my subscription?
You: I cannot access my account. What should I check?
You: Our API latency increased after a deployment. How should we triage it?
```

Enter `exit`, `quit`, or `bye` to end the session.


## Content Safety behavior

When `CONTENT_SAFETY_ENDPOINT` is configured, the application blocks text if any returned category has severity greater than `2`.

- Blocked user input is not sent to the workflow.
- A blocked final response is replaced with a notice instead of being displayed. The workflow has already run at that point.
- Intermediate agent messages are not explicitly moderated by this application.
- If the endpoint is missing, the CLI prints a notice and continues without moderation.
- Moderation request failures are not caught by the chat loop and can terminate the run.

## Azure infrastructure

[infra/main.bicep](infra/main.bicep) defines a Foundry account and project, `gpt-5.1` and `gpt-4.1` model deployments, and an Azure AI Content Safety resource. Both model deployments use `GlobalStandard` with capacity `1`. The default application configuration only uses `gpt-5.1`.

The [Makefile](Makefile) provides these commands:

| Command | Action |
| --- | --- |
| `make group` | Create the configured resource group. |
| `make validate` | Validate the infrastructure deployment against Azure. |
| `make what-if` | Preview infrastructure changes. |
| `make deploy` | Create the resource group, upgrade Bicep, and deploy resources. |
| `make outputs` | Show deployment outputs. |
| `make list` | List resource groups in the subscription. |
| `make deleted` | List soft-deleted Cognitive Services accounts. |
| `make cleanup` | Delete the configured resource group and all its resources. |
| `make purge` | Permanently purge the accounts named in that target. |

Review the Makefile defaults before running commands. Variables can be overridden, for example:

```bash
make what-if RESOURCE_GROUP=my-resource-group AI_FOUNDRY_NAME=my-foundry
```

Deployment requires an appropriate region, model availability, quota, and Azure permissions. The outputs include `OPENAI_ENDPOINT`, model deployment names, and `CONTENT_SAFETY_ENDPOINT`. They do not include `AZURE_PROJECT_ENDPOINT`; obtain that from your Foundry project. `OPENAI_ENDPOINT` is not a substitute for the project endpoint.


## Project layout

```text
main.py                       Terminal chat and startup
agents/deployment/            Foundry agent version creation
agents/runtime/               Runtime Foundry agent clients
clients/foundry.py            Shared Azure credential and project client
config/                       YAML configuration and loader
data/                         Specialist reference documents and loader
infra/                        Azure Bicep templates
orchestration/                Magentic workflow construction
prompts/                      Agent personas and instructions
services/content_safety_service.py  Text moderation
Makefile                      Azure infrastructure commands
```

## License

[MIT](LICENSE).
