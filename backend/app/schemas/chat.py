from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    document_id: str | None = None


class SourceChunk(BaseModel):
    chunk_index: int
    page: int | None = None
    text: str
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    used_rag: bool
    sources: list[SourceChunk] = []
