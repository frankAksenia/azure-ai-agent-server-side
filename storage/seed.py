import argparse
import json
import sqlite3
from pathlib import Path

from storage.database import DEFAULT_DATABASE_PATH, connect, initialize_database


DEFAULT_DATA_PATH = Path(__file__).with_name('synthetic_data.json')

TABLE_COLUMNS = {
    'customers': ('id', 'name'),
    'invoices': ('id', 'customer_id', 'subscription_id', 'billing_period', 'amount_cents', 'currency', 'payment_status'),
    'support_tickets': ('id', 'customer_id', 'invoice_id', 'issue', 'status'),
}


def load_dataset(data_path):

    with Path(data_path).open(encoding='utf-8') as source:
        data = json.load(source)
    
    for table, _ in TABLE_COLUMNS.items():
        rows = data[table]
        ids = set()
        for _ , row in enumerate(rows):
            record_id = row['id']
            ids.add(record_id)

    return data


def seed_database(database_path, data_path):

    data = load_dataset(data_path)
    connection = connect(database_path)
    try:
        initialize_database(connection)
        inserted = {}
        with connection:
            for table, columns in TABLE_COLUMNS.items():
                placeholders = ', '.join('?' for _ in columns)
                cursor = connection.executemany(
                    f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({placeholders}) '
                    'ON CONFLICT(id) DO NOTHING',
                    [tuple(row[column] for column in columns) for row in data[table]],
                )
                inserted[table] = cursor.rowcount
        return inserted
    finally:
        connection.close()


def main():
    
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=DEFAULT_DATABASE_PATH)
    parser.add_argument('--data', type=Path, default=DEFAULT_DATA_PATH, help='JSON dataset to populate (default: storage/synthetic_data.json).')
    args = parser.parse_args()
    try:
        inserted = seed_database(args.database, data_path=args.data)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Database population failed: {error}\n')
    print(f'Synthetic billing data is ready at {args.database.resolve()}')
    print('Inserted: ' + ', '.join(f'{count} {table}' for table, count in inserted.items()))


if __name__ == '__main__':
    main()
