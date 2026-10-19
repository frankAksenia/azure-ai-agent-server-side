from uuid import uuid4

from services.conversation_service import ConversationService
from storage.conversation_store import ConversationStore
from storage.database import DEFAULT_DATABASE_PATH


class ConversationManager:
    def __init__(self, database_path=DEFAULT_DATABASE_PATH, max_history_turns: int = 20):
        self.store = ConversationStore(database_path, max_history_turns)

    @staticmethod
    def _validate_customer(customer_id):
        if not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("Customer ID must not be empty.")

    def create(self, customer_id):
        self._validate_customer(customer_id)
        conversation_id = str(uuid4())
        self.store.create(conversation_id, customer_id)
        return conversation_id, ConversationService(self.store, conversation_id, customer_id)

    def get_conversation(self, conversation_id, customer_id):
        self._validate_customer(customer_id)
        self.store.require_owner(conversation_id, customer_id)
        return ConversationService(self.store, conversation_id, customer_id)

    def get_or_create_conversation(self, conversation_id, customer_id):
        if conversation_id is None:
            return self.create(customer_id)
        return conversation_id, self.get_conversation(conversation_id, customer_id)

    def delete_conversation(self, conversation_id, customer_id):
        self._validate_customer(customer_id)
        self.store.delete(conversation_id, customer_id)
