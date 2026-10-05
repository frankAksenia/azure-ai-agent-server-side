from agent_framework import AgentSession, InMemoryHistoryProvider, Message


class ConversationService:

    def __init__(self):
        self.session = AgentSession()

        self.history_provider = InMemoryHistoryProvider(
            source_id="conversation_history",
            load_messages=False,
        )

    def get_history(self):

        provider_state = self.session.state.get(
            "conversation_history",
            {},
        )

        return provider_state.get("messages", [])

    def build_task(self, user_input):

        history = self.get_history()

        if not history:
            return user_input

        history_text = []

        for message in history:
            role = getattr(message, "role", "unknown")
            text = getattr(message, "text", "")

            history_text.append(f"{role}: {text}")

        conversation = "\n".join(history_text)

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

        provider_state = self.session.state.setdefault("conversation_history", {})

        messages = provider_state.setdefault("messages", [])

        messages.extend(
            [
                Message(
                    role="user",
                    contents=user_input,
                ),
                Message(
                    role="assistant",
                    contents=assistant_output,
                ),
            ]
        )