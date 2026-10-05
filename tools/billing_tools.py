import logging
from typing import Annotated

from agent_framework import tool
from azure.ai.projects.models import FunctionTool as FoundryFunctionTool


from services.billing_service import get_invoice, list_invoices
from services.ticket_service import get_ticket, prepare_ticket
from storage.database import DEFAULT_DATABASE_PATH


logger = logging.getLogger(__name__)


def create_billing_tools(customer_id, session_id, database_path = DEFAULT_DATABASE_PATH):

    if not customer_id.strip() or not session_id.strip():
        raise ValueError('Customer ID and session ID must not be empty.')

    @tool(
        name='list_my_invoices',
        description=(
            'List invoices for the current customer, including invoice IDs, '
            'subscription IDs, billing periods, amounts in cents, currencies, '
            'and payment statuses. Use this to answer billing-history questions '
            'or investigate possible duplicate charges. Matching charges are '
            'not proof of a billing error. Returns an empty list if no invoices exist.'
        ),
    )
    def list_my_invoices() -> list[dict]:
        logger.debug("Executing billing tool: list_my_invoices")
        return list_invoices(customer_id, database_path=database_path)

    @tool(
        name='get_invoice_details',
        description=(
            'Retrieve a specific invoice belonging to the current customer. '
            'Use this when an invoice ID is known and its details are needed. '
            'Amounts are in integer cents with a separate currency. Returns null '
            'if the invoice does not exist or is unavailable to the current customer.'
        ),
    )
    def get_invoice_details(invoice_id: Annotated[str, 'The invoice ID to retrieve, for example INV-1003.'],) -> dict | None:
        logger.debug("Executing billing tool: get_invoice_details (invoice_id=%s)", invoice_id)
        return get_invoice(customer_id, invoice_id, database_path=database_path)

    @tool(
        name='prepare_support_ticket',
        description=(
            'Prepare a support-ticket proposal for an invoice belonging to the '
            'current customer when the customer wants to escalate a billing issue. '
            'This saves a pending proposal for user review; it does not create a '
            'support ticket, issue a refund, or change an invoice. Returns the '
            'proposal details and pending status. Tell the user that confirmation '
            'through the application is required. Do not claim a ticket was created. '
            'Do not prepare the same proposal again if it is already pending.'
        ),
    )
    def prepare_support_ticket(
        invoice_id: Annotated[str, 'The invoice ID the proposed support ticket concerns.'],
        issue: Annotated[
            str,
            'A concise description of the customer issue based on the conversation '
            'and verified invoice details. Must not be empty.',
        ],
    ) -> dict:
        logger.debug("Executing billing tool: prepare_support_ticket (invoice_id=%s)", invoice_id)
        return prepare_ticket(
            customer_id, session_id, invoice_id, issue, database_path=database_path,
        )

    @tool(
        name='get_support_ticket_status',
        description=(
            'Look up an existing support ticket belonging to the current customer '
            'by ticket ID. Returns its ID, linked invoice, issue and current status '
            '(open, in_progress, or closed). Returns null when missing or unavailable '
            'to this customer. Does not create, change, or cancel any ticket. '
            'Use this before answering ticket-status questions.'
        ),
    )
    def get_support_ticket_status(
        ticket_id: Annotated[str, 'The existing support ticket ID, for example TKT-3002.'],
    ) -> dict | None:
        logger.debug("Executing billing tool: get_support_ticket_status (ticket_id=%s)", ticket_id)
        return get_ticket(customer_id, ticket_id, database_path=database_path)

    return [list_my_invoices, get_invoice_details, prepare_support_ticket, get_support_ticket_status]


def create_billing_tool_definitions():

    definitions = []
    for runtime_tool in create_billing_tools('schema-only', 'schema-only'):
        parameters = runtime_tool.parameters()
        parameters['additionalProperties'] = False
        definitions.append(FoundryFunctionTool(
            name=runtime_tool.name,
            description=runtime_tool.description,
            parameters=parameters,
            strict=True,
        ))
    return definitions
