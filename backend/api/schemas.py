from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: str | None = Field(None, min_length=1, max_length=36)

    @field_validator("message")
    @classmethod
    def meaningful_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank.")
        return value


class TicketProposal(BaseModel):
    id: str
    invoice_id: str
    issue: str
    status: Literal["pending", "cancelled", "consumed"]


class TicketResponse(BaseModel):
    id: str
    invoice_id: str
    issue: str
    status: Literal["open", "in_progress", "closed"]
    proposal_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    pending_proposals: list[TicketProposal] = Field(default_factory=list)
