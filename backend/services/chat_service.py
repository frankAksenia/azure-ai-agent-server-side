from services.conversation_manager import ConversationManager
from orchestration.magentic_workflow import create_workflow


class ChatService:
    def __init__(self, agents, conversation_manager: ConversationManager, content_safety_service=None):
        
        self.agents = agents
        self.conversation_manager = conversation_manager
        self.content_safety = content_safety_service

    async def chat(self, user_input, conversation_id):

        conversation_id, conversation = (self.conversation_manager.get_or_create_conversation(conversation_id))

        if self.content_safety:
            moderation = self.content_safety.analyze_text(user_input)

            if not moderation["safe"]:
                raise ValueError("Message blocked by Content Safety.")

        task = conversation.build_task(user_input)

        workflow = create_workflow(self.agents)

        workflow_agent = workflow.as_agent(
            name="Magentic Workflow",
            description="Customer support multi-agent workflow.",
        )

        result = await workflow_agent.run(task)

        assistant_output = getattr(result, "text", str(result),)

        if self.content_safety:
            moderation = self.content_safety.analyze_text(assistant_output)

            if not moderation["safe"]:
                assistant_output = (
                    "The generated response was blocked "
                    "by Content Safety."
                )

        await conversation.add_turn(
            user_input,
            assistant_output,
        )

        return conversation_id, assistant_output