# Synthetic billing data

The editable records live in [synthetic_data.json](synthetic_data.json).
Database population is a separate, local process. It requires no Azure access.
FastAPI checks that the billing database is ready and never populates billing
records automatically. Its conversation store creates its own history tables.

From `backend`, with the virtual environment activated:

```bash
python -m storage.seed
python -m uvicorn main:app --reload
```

The population command creates the schema, applies existing schema migrations,
and inserts missing records into the configured SQLite database (default
`storage/demo.sqlite3`). Repeating it preserves
existing records, ticket status changes, proposals, and tickets created by users.
It reports the number of newly inserted records. Editing an existing ID in JSON
does not update that record in SQLite; add new IDs to extend an existing database,
or populate a new database file to preview the complete edited dataset.

To select a different dataset or database:

```bash
python -m storage.seed --data storage/synthetic_data.json --database /tmp/demo.sqlite3
```

The destination directory must exist. Both the seed command and the API honor
`DATABASE_PATH` in the root `.env`; relative paths resolve from the repository
root. An explicit `--database` overrides only the seed destination, so use the
same path in `DATABASE_PATH` when starting the API.

For Python callers, both paths are required:

```python
from storage.database import DEFAULT_DATABASE_PATH
from storage.seed import DEFAULT_DATA_PATH, seed_database

inserted = seed_database(DEFAULT_DATABASE_PATH, DEFAULT_DATA_PATH)
```

The returned dictionary contains newly inserted counts for `customers`,
`invoices`, and `support_tickets`. A rerun of the same data normally reports zero
for each table. Population applies schema migrations before inserting records;
the schema/migration work is separate from the record-insertion transaction.

The JSON contains three arrays: `customers`, `invoices`, and `support_tickets`.
Each object uses the corresponding database field names. Monetary amounts are
non-negative integer cents and billing periods are `YYYY-MM`. Every invoice must
reference a customer; every ticket must reference an invoice owned by that same
customer. All inserted records share one transaction: a failed insert rolls back
the dataset inserts. No ticket proposals are pre-approved or seeded.

The loader currently parses JSON and reads the expected fields; it does not
perform comprehensive dataset validation. Use all three arrays and these fields:

| Array | Fields |
| --- | --- |
| `customers` | `id`, `name` |
| `invoices` | `id`, `customer_id`, `subscription_id`, `billing_period`, `amount_cents`, `currency`, `payment_status` |
| `support_tickets` | `id`, `customer_id`, `invoice_id`, `issue`, `status` |

SQLite enforces customer/invoice relationships, allowed statuses, non-negative
amounts, and three-character currencies. Keep IDs unique within each array;
existing IDs are skipped rather than updated. A fresh database populated from
the default JSON has 10 customers, 50 invoices, and 12 tickets; an existing
database can contain additional user-created records.

## Schema and access

| Table | Purpose |
| --- | --- |
| `customers` | Synthetic customer identities. |
| `invoices` | Customer-owned invoices and their payment states. |
| `ticket_proposals` | Pending, cancelled, or consumed proposals scoped to a customer and conversation. |
| `support_tickets` | Customer-owned tickets with an invoice reference and an optional unique proposal reference. |
| `conversations` | Customer ownership and conversation timestamps. |
| `conversation_messages` | Persistent user/assistant text, retaining the latest 20 complete turn pairs. |

`require_database()` opens SQLite read-only and checks the four tables, the
`support_tickets.proposal_id` column, and the presence of customer records. If these are
unavailable, startup instructs you to run `python -m storage.seed`. It does not
create the file, migrate the schema, or insert records.
Startup verifies that `DEMO_CUSTOMER_ID` exists.

During explicit population, existing schemas gain proposal references and a
unique index for retry-safe ticket creation. Older uncompleted `approved`
proposals become `pending` and need confirmation again.

## Dataset

The file contains **10 customers, 50 invoices, and 12 tickets**, all fictional.
Customers have five invoices each. Currencies include EUR, USD, and GBP; invoice
statuses include `paid`, `unpaid`, and `refunded`; ticket statuses include `open`,
`in_progress`, and `closed`.

| Customer | Example scenario |
| --- | --- |
| `CUS-001` — Alex Morgan | EUR 29.00 September payment (`INV-1001`), possible duplicate October charges (`INV-1002`, `INV-1003`), open ticket `TKT-3002`, review ticket `TKT-1001` |
| `CUS-002` — Sam Rivera | Unpaid October invoice `INV-2002`, open ticket `TKT-2001` |
| `CUS-003` — Jordan Chen | Refunded September invoice `INV-3001`, closed ticket `TKT-3001` |
| `CUS-004` — Taylor Brooks | Unpaid October invoice and open review ticket |
| `CUS-005` — Casey Patel | Refunded August invoice and closed review ticket |
| `CUS-006` — Riley Chen | Paid EUR invoices and a ticket in progress |
| `CUS-007` — Morgan Diaz | Unpaid USD invoice and an open ticket |
| `CUS-008` — Jamie Novak | Paid USD invoices and a ticket in progress |
| `CUS-009` — Avery Kim | Refunded GBP invoice and closed review ticket |
| `CUS-010` — Quinn Silva | Paid GBP invoices and a ticket in progress |

Try these requests:

```text
What amount was paid for invoice INV-1001?
Was I charged twice for October 2026?
What is the status of ticket TKT-3002?
Please propose a support ticket for INV-1003 about the possible duplicate charge.
```

The model prepares a pending proposal. The API returns it in `pending_proposals`
so the frontend can ask for confirmation. A request to
`POST /api/conversations/{conversation_id}/proposals/{proposal_id}/approve`
creates its ticket; the corresponding `/cancel` endpoint cancels the proposal.
Creation is transactional and retry-safe for the same proposal. Conversation
IDs persist across API restarts and serve as the proposal's `session_id`.

Billing owns invoice lookups, ticket proposals, and status lookup. The Support
Agent has no ticket tools. Status lookup uses only the ticket ID and returns
`id`, `invoice_id`, `issue`, and `status`; missing or foreign tickets return
`None`. A proposal requires an owned invoice and a non-empty issue.

Ticket creation changes the proposal to `consumed` and inserts an `open` ticket.
Retrying creation for the same proposal returns the existing
ticket. Cancelling a proposal changes its status to `cancelled`; cancellation of
an already-created ticket is not implemented. Separate proposals for the same
issue are not deduplicated. The configured demo customer can list pending proposals
for an owned conversation after restarting the API. No refund or invoice
modification is performed by these operations.

## Inspect local data

With the SQLite CLI installed, run these read-only queries from `backend`:

```bash
sqlite3 storage/demo.sqlite3 "SELECT id, invoice_id, status FROM support_tickets WHERE customer_id = 'CUS-001';"
sqlite3 storage/demo.sqlite3 "SELECT id, status FROM ticket_proposals WHERE customer_id = 'CUS-001';"
```
