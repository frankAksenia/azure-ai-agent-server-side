from fastapi import APIRouter, HTTPException, Request

from api.schemas import ChatRequest, ChatResponse, TicketProposal, TicketResponse
from services.ticket_service import ProposalConflictError, ProposalNotFoundError
from storage.conversation_store import ConversationNotFoundError


router = APIRouter(prefix="/api", tags=["chat"])


async def service_call(awaitable):
    try:
        return await awaitable
    except (ConversationNotFoundError, ProposalNotFoundError) as error:
        raise HTTPException(404, str(error)) from error
    except ProposalConflictError as error:
        raise HTTPException(409, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    conversation_id, output, pending = await service_call(request.app.state.chat_service.chat(
        user_input=body.message, conversation_id=body.conversation_id, customer_id=request.app.state.customer_id,
    ))
    return ChatResponse(message=output, conversation_id=conversation_id, pending_proposals=pending)


@router.get("/conversations/{conversation_id}/proposals", response_model=list[TicketProposal])
async def list_proposals(conversation_id: str, request: Request):
    return await service_call(request.app.state.chat_service.list_proposals(request.app.state.customer_id, conversation_id))


@router.post("/conversations/{conversation_id}/proposals/{proposal_id}/approve", response_model=TicketResponse)
async def approve_proposal(conversation_id: str, proposal_id: str, request: Request):
    return await service_call(request.app.state.chat_service.approve_proposal(
        request.app.state.customer_id, conversation_id, proposal_id,
    ))


@router.post("/conversations/{conversation_id}/proposals/{proposal_id}/cancel", response_model=TicketProposal)
async def cancel_proposal(conversation_id: str, proposal_id: str, request: Request):
    return await service_call(request.app.state.chat_service.cancel_proposal(
        request.app.state.customer_id, conversation_id, proposal_id,
    ))
