from contextlib import closing
from pathlib import Path

from storage.database import DEFAULT_DATABASE_PATH, connect


def list_invoices(customer_id, database_path = DEFAULT_DATABASE_PATH):

    with closing(connect(database_path)) as connection:
        rows = connection.execute(
            'SELECT * FROM invoices WHERE customer_id = ? ORDER BY billing_period, id', (customer_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_invoice(customer_id, invoice_id, database_path = DEFAULT_DATABASE_PATH):

    with closing(connect(database_path)) as connection:
        row = connection.execute(
            'SELECT * FROM invoices WHERE id = ? AND customer_id = ?',(invoice_id, customer_id),
        ).fetchone()
        return dict(row) if row else None
