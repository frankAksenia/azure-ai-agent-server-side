# Azure AI Agent Server Side

A FastAPI customer-support API that coordinates manager, billing, support and technical agents in Microsoft Foundry. Specialists retrieve PDF knowledge from a Cosmos DB vector store. Customer invoices, conversations and confirmed support tickets persist in SQLite.

## Request workflow

1. The API runs every request as one configured synthetic demo customer.
2. A new chat creates a conversation for that customer; later requests must use an owned conversation ID. Conversation history is loaded from SQLite.
3. The manager coordinates specialists through Microsoft Agent Framework's Magentic workflow. Each specialist receives a domain-scoped PDF retrieval tool; billing also receives customer-scoped invoice and ticket tools.
4. PDF retrieval embeds the search query and searches the domain's published corpus generation. Retrieved passages include document and page metadata for source attribution.
5. Optional Content Safety moderation checks messages, answers and proposal text before it reaches clients. Accepted turns persist for follow-up requests.
6. Billing can save a support-ticket proposal. The client displays pending proposals and uses the explicit approval or cancellation endpoint. Ticket creation is retry-safe.

The workflow allows up to five rounds, three stalls and two resets. Agents are bound to the configured demo customer and conversation when processing each request. Conversation and ticket state survive API restarts; SQLite must reside on persistent storage. This demo is intended for one API process; a multi-instance deployment needs shared persistence and concurrency handling.

## Local setup

Run these commands from the repository root unless a command shows otherwise. Python 3.13 is used for local development.

```bash
cp .env.example .env
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
az login
```

Every entry point loads the repository-root `.env` without overriding existing process environment variables. Each entry point creates one `DefaultAzureCredential`, passes it to the Azure clients it owns, and closes it when that operation ends; a hosted application can use a managed identity.

SDK construction lives in `clients/`. Each service or store retains and closes the SDK clients it creates, including cleanup after partial initialization. FastAPI reuses services for one worker lifespan; indexing and deployment jobs own their services for one run. Clients close before the credential owned by their entry point. `RetrievalService` borrows its injected services and does not close them.

Configure these values in the root `.env`:

| Variable | Purpose |
| --- | --- |
| `AZURE_PROJECT_ENDPOINT` | Foundry project URL, `https://<account>.services.ai.azure.com/api/projects/<project>`. |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Deployment name for `text-embedding-3-small`; embeddings have 1536 dimensions. |
| `AZURE_COSMOS_ENDPOINT` | Cosmos DB for NoSQL account endpoint. |
| `AZURE_COSMOS_DATABASE` | Knowledge database; defaults to `agent-knowledge`. |
| `AZURE_COSMOS_CONTAINER` | Knowledge container; defaults to `knowledge`. |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | Document Intelligence endpoint used during PDF indexing. |
| `CONTENT_SAFETY_ENDPOINT` | Optional moderation endpoint; omit or leave empty to disable moderation. |
| `DEMO_CUSTOMER_ID` | Seeded customer ID used for every request. Default: `CUS-001`. |
| `DATABASE_PATH` | Optional SQLite path; relative paths resolve from the repository root. Default: `backend/storage/demo.sqlite3`. |

Set `DEMO_CUSTOMER_ID=CUS-001` in `.env` to use the first seeded customer. The API does not require a Bearer token or Microsoft Entra configuration.

The repository configures local CORS for `http://localhost:5173`; update the allowed origin for your frontend before hosting it.

## Azure resources

The Bicep deployment provisions:

- A Foundry account and project, plus `gpt-5.1`, `gpt-4.1` and `text-embedding-3-small` deployments.
- Azure AI Content Safety and Document Intelligence. Document Intelligence defaults to S0 so longer PDFs are fully analyzed; F0 is configurable and processes only the first two pages per request.
- A Cosmos DB for NoSQL account with vector search, a database and a dedicated-throughput knowledge container partitioned by `/domain`.
- Optional access assignments for a PDF-indexing identity and a FastAPI runtime identity. The indexer gets Cosmos Data Contributor; the runtime gets Cosmos Data Reader. Both can use Foundry models and Content Safety, and the indexer can use Document Intelligence.

The container loads the existing JSON policies under `backend/infra/cosmosdb`: `/embedding`, float32, 1536 dimensions, cosine distance and a `quantizedFlat` vector index. Ordinary array indexing is excluded for embeddings. Cosmos uses a full vector scan below 1,000 vectors; this is expected for the bundled corpus.

From `backend`, review names and identity object IDs, then preview your deployment:

```bash
make group
make what-if INDEXER_PRINCIPAL_ID=<developer-or-indexer-object-id> RUNTIME_PRINCIPAL_ID=<runtime-managed-identity-object-id>
make validate INDEXER_PRINCIPAL_ID=<developer-or-indexer-object-id> RUNTIME_PRINCIPAL_ID=<runtime-managed-identity-object-id>
```

When ready to provision these resources:

```bash
make deploy INDEXER_PRINCIPAL_ID=<developer-or-indexer-object-id> RUNTIME_PRINCIPAL_ID=<runtime-managed-identity-object-id>
make outputs
```

The Makefile exposes `RESOURCE_GROUP`, `LOCATION`, `AI_FOUNDRY_NAME`, `INDEXER_PRINCIPAL_ID`, and `RUNTIME_PRINCIPAL_ID`. Other infrastructure defaults live in `infra/main.bicep`. Deployment needs appropriate model availability, quota and permissions to create resources and role assignments. Empty identity parameters leave those application access assignments to your existing configuration. Deployment outputs provide the application's Azure endpoints and model names.

For an **existing Cosmos account**, ensure the `cosmosServerless` and `cosmosFreeTier` defaults in `infra/main.bicep` match its immutable settings. The existing `azure-agent-rag-cosmos` account is provisioned and has free tier enabled, which matches the current defaults. For an **existing Cosmos container**, check its partition key and policies before deploying or indexing. The application requires `/domain`; changing an existing container's partition key requires a new container and reindexing. Update the `cosmosContainerName` default in `infra/main.bicep` and `.env` when using a replacement container. Preserve existing data until the replacement has been verified.

The account template explicitly configures a single replication region, Session consistency, Entra-only Cosmos authentication and public networking. When applying it to an existing account, preserve your desired account settings in the template and inspect `make what-if`. Existing manually assigned Azure roles may need to be retained or imported into your infrastructure workflow to avoid duplicate assignments.

Vector-search feature activation can take time after account creation. If indexing reports that vector search is not ready, retry after activation completes. Runtime hosting is configured separately from these resource templates.

## Run the application

Run the remaining commands from `backend` with the virtual environment activated.

For the first local setup, after Azure resources have been configured and the root `.env` contains their endpoints:

```bash
make seed
make rag-index
make agents-deploy
```

`make seed` is local and repeatable. `make rag-index` sends the PDF corpus to Document Intelligence, creates embeddings, and writes a new searchable corpus generation to Cosmos DB. `make agents-deploy` publishes new versions of the Foundry agents. Run the latter two only after changing the PDFs, agent prompts, tool schemas, or agent configuration; they are not normal server-start commands.

Start or restart the API with:

```bash
make serve
```

`make seed` initializes/migrates the configured SQLite database and inserts synthetic customers, invoices and tickets from `storage/synthetic_data.json`. Existing records are preserved. Explicit `python -m storage.seed --database /absolute/path/demo.sqlite3` can select a different seed destination; use the same `DATABASE_PATH` for the API.

`make rag-index` reads PDFs from `data/billing`, `data/support` and `data/technical`; Document Intelligence extracts each page as Markdown. Each nonempty page becomes one searchable record with its full extracted text, stable ID and document/page/domain metadata. Pages are not split into token windows or overlapped. Each page record is embedded with the configured model and staged under a new corpus generation. The generation is published per domain only after all uploads succeed. An unsuccessful upload leaves the prior published corpus available. Deleted or shortened PDFs stop appearing in the newly published corpus. Old generations are retained for readers already using them; cleanup is a separate maintenance operation.

**Run a full reindex after upgrading from the original chunk schema.** Existing rows without a published generation are not searched. Indexing is an explicit job; the API does not index PDFs at startup.

Domain publication uses independent writes. If publication fails after one domain switches, different domains can temporarily use different complete generations; rerun indexing to publish them together. Uploaded chunks are never exposed through a partially uploaded domain.

`make agents-deploy` publishes new versions of all four Foundry agents, including the PDF-retrieval and billing-tool schemas. Run it after changing deployed instructions, model-visible tools or agent model configuration. Editing PDFs requires reindexing; restarting the API loads local service and workflow changes. `config/config.yaml` selects agent deployment names and model deployments.

`make serve` runs `python -m uvicorn main:app --reload`. Open `http://localhost:8000/docs` for the API schema. The health endpoint is `GET /health`.

## Chat and proposal endpoints

```bash
curl http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is the subscription cancellation policy?"}'
```

The response includes `message`, `conversation_id` and `pending_proposals`. Include the returned `conversation_id` with the next chat request to continue that conversation. Another customer's conversation ID cannot be used.

| Endpoint | Action |
| --- | --- |
| `POST /api/chat` | Send a message, optionally within an existing owned conversation. |
| `GET /api/conversations/{conversation_id}/proposals` | List the conversation's pending ticket proposals. |
| `POST /api/conversations/{conversation_id}/proposals/{proposal_id}/approve` | Confirm a proposal and create or return its ticket. |
| `POST /api/conversations/{conversation_id}/proposals/{proposal_id}/cancel` | Cancel a pending proposal. |

Every endpoint uses the configured demo customer. Creating a ticket requires application confirmation through the approval endpoint; an agent's proposal alone does not create one. Billing status lookups and invoice tools remain customer-scoped. General tickets without an invoice and cancellation of an existing ticket are not implemented.

## Verification

```bash
make test
```

The test suite uses mocked Azure clients to verify client cleanup, FastAPI startup/shutdown, schema checks, domain isolation and safe corpus publication. It does not require Azure access or modify your application database.

## Project layout

```text
.env.example                  Root environment template
backend/main.py               FastAPI startup and shared client lifecycle
backend/api/                  HTTP routes and schemas
backend/agents/deployment/    Explicit Foundry agent version creation
backend/agents/runtime/       Customer/conversation-bound runtime agents
backend/clients/              Azure credential and SDK client factories
backend/config/               YAML configuration and environment loader
backend/data/                 Fictional PDF knowledge corpus
backend/rag/                  PDF loading and page indexing
backend/storage/              Cosmos vector store and persistent SQLite data
backend/services/             Retrieval, conversations, moderation, billing and tickets
backend/tools/                Domain retrieval and customer-scoped billing tools
backend/infra/                Bicep templates and Cosmos policies
backend/scripts/              Optional Azure verification commands
backend/tests/                Offline workflow and regression checks
```

The PDFs are a fictional Northstar Cloud Systems knowledge corpus. SQLite billing records are synthetic demo data. See `backend/data/README_CORPUS.txt` and `backend/storage/README.md` for dataset details.

## License

[MIT](LICENSE).
