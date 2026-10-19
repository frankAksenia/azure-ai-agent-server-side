"""Persistent, customer-owned conversation history."""

from contextlib import closing
from pathlib import Path
import sqlite3
import time


class ConversationNotFoundError(LookupError):
    pass


class ConversationStore:
    def __init__(self, database_path: Path | str, max_history_turns: int = 20):
        if max_history_turns < 1:
            raise ValueError("max_history_turns must be at least one.")
        self.database_path = Path(database_path).resolve()
        self.max_history_turns = max_history_turns
        with closing(self._connect()) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL
                        REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    text TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS conversation_message_order
                    ON conversation_messages(conversation_id, sequence);
            """)

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _owned(connection, conversation_id: str, customer_id: str):
        row = connection.execute(
            "SELECT * FROM conversations WHERE id = ? AND customer_id = ?",
            (conversation_id, customer_id),
        ).fetchone()
        if row is None:
            raise ConversationNotFoundError("Conversation not found.")
        return row

    def create(self, conversation_id: str, customer_id: str):
        now = time.time()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO conversations (id, customer_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (conversation_id, customer_id, now, now),
            )

    def require_owner(self, conversation_id: str, customer_id: str):
        with closing(self._connect()) as connection:
            self._owned(connection, conversation_id, customer_id)

    def history(self, conversation_id: str, customer_id: str) -> list[dict]:
        with closing(self._connect()) as connection:
            self._owned(connection, conversation_id, customer_id)
            rows = connection.execute(
                "SELECT role, text FROM conversation_messages "
                "WHERE conversation_id = ? ORDER BY sequence",
                (conversation_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def append_turn(
        self,
        conversation_id: str,
        customer_id: str,
        user_input: str,
        assistant_output: str,
    ):
        with closing(self._connect()) as connection, connection:
            self._owned(connection, conversation_id, customer_id)
            connection.executemany(
                "INSERT INTO conversation_messages (conversation_id, role, text) VALUES (?, ?, ?)",
                [
                    (conversation_id, "user", user_input),
                    (conversation_id, "assistant", assistant_output),
                ],
            )
            connection.execute(
                "DELETE FROM conversation_messages WHERE conversation_id = ? "
                "AND sequence NOT IN (SELECT sequence FROM conversation_messages "
                "WHERE conversation_id = ? ORDER BY sequence DESC LIMIT ?)",
                (conversation_id, conversation_id, self.max_history_turns * 2),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (time.time(), conversation_id),
            )

    def delete(self, conversation_id: str, customer_id: str):
        with closing(self._connect()) as connection, connection:
            self._owned(connection, conversation_id, customer_id)
            connection.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
