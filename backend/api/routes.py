from fastapi import APIRouter, HTTPException, Request
from api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:

    chat_service = request.app.state.chat_service

    try:
        conversation_id, assistant_output = await chat_service.chat(
            user_input=body.message,
            conversation_id=body.conversation_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ChatResponse(
        message=assistant_output,
        conversation_id=conversation_id,
    )