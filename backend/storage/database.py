import sqlite3
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "demo.sqlite3"

def require_database(database_path = DEFAULT_DATABASE_PATH):

    path = Path(database_path).resolve()

    try:
        connection = sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True)
        try:
            for table in ('customers', 'invoices', 'ticket_proposals', 'support_tickets'):
                connection.execute(f'SELECT 1 FROM {table} LIMIT 1')
            connection.execute('SELECT proposal_id FROM support_tickets LIMIT 1')
            if connection.execute("SELECT 1 FROM customers WHERE id = 'CUS-001'").fetchone() is None:
                raise sqlite3.DatabaseError('Demo customer CUS-001 is missing.')
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise RuntimeError(f'Billing database is not ready at {path}. Run `python -m storage.seed` before starting the chat.') from error


def connect(database_path):

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection):

    connection.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(id),
            subscription_id TEXT NOT NULL,
            billing_period TEXT NOT NULL,
            amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
            currency TEXT NOT NULL CHECK (length(currency) = 3),
            payment_status TEXT NOT NULL
                CHECK (payment_status IN ('paid', 'unpaid', 'refunded')),
            UNIQUE (id, customer_id)
        );

        CREATE TABLE IF NOT EXISTS ticket_proposals (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(id),
            session_id TEXT NOT NULL CHECK (length(trim(session_id)) > 0),
            invoice_id TEXT NOT NULL,
            issue TEXT NOT NULL CHECK (length(trim(issue)) > 0),
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'cancelled', 'consumed')),
            FOREIGN KEY (invoice_id, customer_id) REFERENCES invoices(id, customer_id)
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(id),
            invoice_id TEXT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('open', 'in_progress', 'closed')),
            FOREIGN KEY (invoice_id, customer_id)
                REFERENCES invoices(id, customer_id)
        );
    """)

    with connection:
        columns = {row['name'] for row in connection.execute('PRAGMA table_info(support_tickets)')}
        if 'proposal_id' not in columns:
            connection.execute('ALTER TABLE support_tickets ADD COLUMN proposal_id TEXT REFERENCES ticket_proposals(id)')
        connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS tickets_by_proposal ON support_tickets(proposal_id)')
    _migrate_proposal_statuses(connection)


def _migrate_proposal_statuses(connection):

    schema = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'ticket_proposals'").fetchone()[0]
    if "'cancelled'" in schema:
        return
    connection.execute('PRAGMA foreign_keys = OFF')
    try:
        with connection:
            connection.execute('BEGIN IMMEDIATE')
            connection.execute(schema.replace('ticket_proposals', 'ticket_proposals_new', 1).replace("'approved'", "'cancelled'"))
            connection.execute("""INSERT INTO ticket_proposals_new
                SELECT id, customer_id, session_id, invoice_id, issue,
                    CASE WHEN status = 'approved' THEN 'pending' ELSE status END
                    FROM ticket_proposals""")
            connection.execute('DROP TABLE ticket_proposals')
            connection.execute('ALTER TABLE ticket_proposals_new RENAME TO ticket_proposals')
            if connection.execute('PRAGMA foreign_key_check').fetchall():
                raise sqlite3.IntegrityError('Proposal migration would break foreign keys.')
    finally:
        connection.execute('PRAGMA foreign_keys = ON')
