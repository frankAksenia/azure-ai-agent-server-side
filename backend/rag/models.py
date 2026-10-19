from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    text: str
    source: str
    page: int
    domain: str


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    content: str
    source: str
    page: int
    domain: str
    score: float
