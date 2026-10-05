import logging

from services.ticket_service import approve_and_create_ticket, list_pending_proposals, cancel_proposal
from storage.database import DEFAULT_DATABASE_PATH


logger = logging.getLogger(__name__)


def review_ticket_proposals(customer_id, session_id, database_path = DEFAULT_DATABASE_PATH, content_safety = None, read_input = input):
    outcomes = []
    for proposal in list_pending_proposals(customer_id, session_id, database_path):
        proposal_id = proposal['id']
        try:
            summary = f"Proposed ticket for invoice {proposal['invoice_id']}: {proposal['issue']}"
            if content_safety and not content_safety.analyze_text(summary)['safe']:
                cancel_proposal(customer_id, session_id, proposal_id, database_path)
                outcome = 'Ticket proposal was blocked by Content Safety and cancelled.'
            else:
                print(summary)
                while True:
                    raw_answer = read_input('Create this support ticket? [y/n]: ')
                    answer = raw_answer.strip().lower()
                    logger.debug(
                        'Ticket proposal %s confirmation input=%r normalised=%r', proposal_id, raw_answer, answer,)
                    if answer in {'y', 'yes', 'n', 'no', ''}:
                        break
                    print(f'Unrecognized response {ascii(raw_answer)}. Enter y/yes to create, or n/no (or Enter) to cancel.')

                if answer in {'y', 'yes'}:
                    ticket = approve_and_create_ticket(customer_id, session_id, proposal_id, database_path)
                    outcome = f"Ticket {ticket['id']} created for invoice {ticket['invoice_id']} (status: {ticket['status']})."
                else:
                    cancel_proposal(customer_id, session_id, proposal_id, database_path)
                    outcome = f"Ticket proposal {proposal_id} cancelled; no ticket was created."
        except Exception:
            logging.exception('Ticket proposal review failed for %s', proposal_id)
            outcome = 'Ticket proposal review failed; no success is assumed. Please retry.'
        print(outcome)
        outcomes.append(outcome)
    return outcomes
