from contextlib import closing
from pathlib import Path
import sqlite3
from uuid import uuid4

from storage.database import DEFAULT_DATABASE_PATH, connect


class ProposalNotFoundError(ValueError):
    pass


class ProposalConflictError(ValueError):
    pass


def get_ticket(customer_id, ticket_id, database_path = DEFAULT_DATABASE_PATH):

    with closing(connect(database_path)) as connection:
        row = connection.execute(
            'SELECT id, invoice_id, issue, status FROM support_tickets WHERE id = ? AND customer_id = ?',(ticket_id, customer_id),
        ).fetchone()
        return dict(row) if row else None


def _proposal(connection, customer_id, session_id, proposal_id):

    row = connection.execute(
        'SELECT * FROM ticket_proposals WHERE id = ? AND customer_id = ? AND session_id = ?', (proposal_id, customer_id, session_id),
    ).fetchone()
    if row is None:
        raise ProposalNotFoundError('Proposal not found for this customer and conversation.')
    return dict(row)


def get_proposal(customer_id, session_id, proposal_id, database_path=DEFAULT_DATABASE_PATH):
    with closing(connect(database_path)) as connection:
        return _proposal(connection, customer_id, session_id, proposal_id)


def prepare_ticket(customer_id, session_id, invoice_id, issue, database_path = DEFAULT_DATABASE_PATH):

    if not session_id.strip():
        raise ValueError('Session ID must not be empty.')
    issue = issue.strip()
    if not issue:
        raise ValueError('Issue must not be empty.')
    with closing(connect(database_path)) as connection, connection:
        invoice = connection.execute(
            'SELECT id FROM invoices WHERE id = ? AND customer_id = ?', (invoice_id, customer_id),
        ).fetchone()
        if invoice is None:
            raise ValueError('Invoice not found for this customer.')
        proposal_id = f'PRP-{uuid4().hex}'
        connection.execute(
            '''INSERT INTO ticket_proposals (id, customer_id, session_id, invoice_id, issue) VALUES (?, ?, ?, ?, ?)''',
            (proposal_id, customer_id, session_id, invoice_id, issue),
        )
        return _proposal(connection, customer_id, session_id, proposal_id)


def approve_and_create_ticket(customer_id, session_id, proposal_id, database_path = DEFAULT_DATABASE_PATH):
    with closing(connect(database_path)) as connection, connection:
        connection.execute('BEGIN IMMEDIATE')
        proposal = _proposal(connection, customer_id, session_id, proposal_id)
        existing = connection.execute(
            'SELECT * FROM support_tickets WHERE proposal_id = ?', (proposal_id,),
        ).fetchone()
        if existing:
            return dict(existing)
        if proposal['status'] != 'pending':
            raise ProposalConflictError('Only pending proposals can be approved.')
        ticket_id = f'TKT-{uuid4().hex}'
        connection.execute(
            '''INSERT INTO support_tickets
               (id, customer_id, invoice_id, issue, status, proposal_id)
               VALUES (?, ?, ?, ?, 'open', ?)''',
            (ticket_id, customer_id, proposal['invoice_id'], proposal['issue'], proposal_id),
        )
        connection.execute(
            "UPDATE ticket_proposals SET status = 'consumed' WHERE id = ?", (proposal_id,),
        )
        ticket = dict(connection.execute(
            'SELECT * FROM support_tickets WHERE id = ?', (ticket_id,),
        ).fetchone())
        return ticket



def list_pending_proposals(customer_id, session_id, database_path = DEFAULT_DATABASE_PATH):

    with closing(connect(database_path)) as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM ticket_proposals WHERE customer_id = ? AND session_id = ? AND status = 'pending' ORDER BY rowid",
            (customer_id, session_id),
        )]


def cancel_proposal(customer_id, session_id, proposal_id, database_path = DEFAULT_DATABASE_PATH):
    
    with closing(connect(database_path)) as connection, connection:
        connection.execute('BEGIN IMMEDIATE')
        proposal = _proposal(connection, customer_id, session_id, proposal_id)
        if proposal['status'] == 'consumed':
            raise ProposalConflictError('A ticket already exists for this proposal.')
        if proposal['status'] == 'cancelled':
            return proposal
        connection.execute("UPDATE ticket_proposals SET status = 'cancelled' WHERE id = ?", (proposal_id,))
        cancelled = _proposal(connection, customer_id, session_id, proposal_id)
        return cancelled
