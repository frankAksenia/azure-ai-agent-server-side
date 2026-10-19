import asyncio

from agent_framework import Message

from storage.conversation_store import ConversationStore


class ConversationService:
    def __init__(self, store: ConversationStore, conversation_id: str, customer_id: str):
        self.store = store
        self.conversation_id = conversation_id
        self.customer_id = customer_id

    def get_history(self):
        return [
            Message(role=row["role"], contents=[row["text"]])
            for row in self.store.history(self.conversation_id, self.customer_id)
        ]

    def build_task(self, user_input):
        history = self.get_history()

        if not history:
            return user_input

        conversation = "\n".join(f"{message.role}: {message.text}" for message in history)

        return (
            "Use the following previous conversation only as context "
            "for understanding the user's current request.\n\n"
            "Previous conversation:\n"
            f"{conversation}\n\n"
            "Current user request:\n"
            f"{user_input}\n\n"
            "Answer the current user request. Do not repeat the "
            "conversation history unless it is relevant."
        )

    async def add_turn(self, user_input, assistant_output):
        await asyncio.to_thread(
            self.store.append_turn,
            self.conversation_id,
            self.customer_id,
            user_input,
            assistant_output,
        )
