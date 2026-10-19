from starlette.concurrency import run_in_threadpool

from orchestration.magentic_workflow import create_workflow
from services.conversation_manager import ConversationManager
from services.ticket_service import (
    ProposalConflictError,
    approve_and_create_ticket,
    cancel_proposal,
    get_proposal,
    list_pending_proposals,
)
from storage.database import DEFAULT_DATABASE_PATH


class ChatService:
    def __init__(self, agent_factory, conversation_manager: ConversationManager, content_safety_service=None,
                 database_path=DEFAULT_DATABASE_PATH, workflow_factory=create_workflow):
        self.agent_factory = agent_factory
        self.conversation_manager = conversation_manager
        self.content_safety = content_safety_service
        self.database_path = database_path
        self.workflow_factory = workflow_factory

    async def _is_safe(self, text):
        if self.content_safety is None:
            return True
        moderation = await run_in_threadpool(self.content_safety.analyze_text, text)
        return moderation["safe"]

    async def chat(self, user_input, conversation_id, customer_id):
        if not user_input.strip():
            raise ValueError("Message cannot be blank.")
        if not await self._is_safe(user_input):
            raise ValueError("Message blocked by Content Safety.")

        conversation_id, conversation = await run_in_threadpool(
            self.conversation_manager.get_or_create_conversation, conversation_id, customer_id,
        )

        task = await run_in_threadpool(conversation.build_task, user_input)

        async with self.agent_factory(customer_id, conversation_id) as agents:
            workflow = self.workflow_factory(agents)
            workflow_agent = workflow.as_agent(
                name="Magentic Workflow", description="Customer support multi-agent workflow.",
            )
            result = await workflow_agent.run(task)

        assistant_output = getattr(result, "text", None) or str(result)

        if not await self._is_safe(assistant_output):
            assistant_output = "The generated response was blocked by Content Safety."

        pending, blocked = await self._safe_pending_proposals(conversation)

        if blocked:
            assistant_output = "A ticket proposal was blocked by Content Safety and cancelled."
        await conversation.add_turn(user_input, assistant_output)

        return conversation_id, assistant_output, pending

    async def list_proposals(self, customer_id, conversation_id):
        conversation = await run_in_threadpool(
            self.conversation_manager.get_conversation, conversation_id, customer_id,
        )
        pending, _ = await self._safe_pending_proposals(conversation)
        return pending

    async def _safe_pending_proposals(self, conversation):
        pending = await run_in_threadpool(
            list_pending_proposals, conversation.customer_id, conversation.conversation_id, self.database_path,
        )
        safe = []
        blocked = False
        for proposal in pending:
            summary = f"Proposed ticket for invoice {proposal['invoice_id']}: {proposal['issue']}"
            if await self._is_safe(summary):
                safe.append(proposal)
            else:
                await self._cancel_proposal(conversation.customer_id, conversation.conversation_id, proposal["id"])
                blocked = True
        return safe, blocked

    async def approve_proposal(self, customer_id, conversation_id, proposal_id):
        await run_in_threadpool(
            self.conversation_manager.get_conversation, conversation_id, customer_id,
        )
        
        proposal = await run_in_threadpool(
            get_proposal, customer_id, conversation_id, proposal_id, self.database_path,
        )

        if proposal["status"] == "cancelled":
            raise ProposalConflictError("A cancelled proposal cannot be approved.")
        
        if proposal["status"] == "pending" and not await self._is_safe(
            f"Proposed ticket for invoice {proposal['invoice_id']}: {proposal['issue']}"
        ):
            await self._cancel_proposal(customer_id, conversation_id, proposal_id)
            raise ValueError("Ticket proposal was blocked by Content Safety and cancelled.")
        
        return await run_in_threadpool(
            approve_and_create_ticket, customer_id, conversation_id, proposal_id, self.database_path,
        )

    async def cancel_proposal(self, customer_id, conversation_id, proposal_id):
        await run_in_threadpool(
            self.conversation_manager.get_conversation, conversation_id, customer_id,
        )

        cancelled = await self._cancel_proposal(customer_id, conversation_id, proposal_id)

        if not await self._is_safe(cancelled["issue"]):
            cancelled = {**cancelled, "issue": "Issue hidden by Content Safety."}
            
        return cancelled

    async def _cancel_proposal(self, customer_id, conversation_id, proposal_id):
        return await run_in_threadpool(
            cancel_proposal, customer_id, conversation_id, proposal_id, self.database_path,
        )
