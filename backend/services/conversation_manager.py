from uuid import uuid4

from services.conversation_service import ConversationService


class ConversationManager:
    def __init__(self):

        self._conversations = {}

    def create(self):

        conversation_id = str(uuid4())

        conversation = ConversationService()

        self._conversations[conversation_id] = conversation

        return conversation_id, conversation

    def get_conversation(self, conversation_id):

        return self._conversations.get(conversation_id)

    def get_or_create_conversation(self, conversation_id):

        if conversation_id:
            conversation = self.get_conversation(conversation_id)

            if conversation:
                return conversation_id, conversation

        return self.create()

    def delete_conversation(self, conversation_id):
        
        self._conversations.pop(conversation_id, None)