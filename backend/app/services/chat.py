from app.clients.llm import complete_chat, embed_texts
from app.clients.vectorstore import query_chunks
from app.core.config import Settings, get_settings
from app.core.enums import DocumentStatus
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.repositories.document import DocumentRepository
from app.schemas.chat import ChatResponse, SourceChunk

DIRECT_SYSTEM = (
    "You are a helpful assistant. Answer the user's question clearly and directly. "
    "If you are unsure, say so."
)

RAG_SYSTEM = (
    "You are a helpful assistant that answers using the provided document excerpts. "
    "Use only the excerpts for factual claims. If the excerpts do not contain the answer, "
    "say that the document does not contain enough information. Cite page numbers when present."
)


class ChatService:
    def __init__(self, repository: DocumentRepository, settings: Settings | None = None) -> None:
        self.repository = repository
        self.settings = settings or get_settings()

    def answer(self, *, user_id: str, question: str, document_id: str | None) -> ChatResponse:
        cleaned = question.strip()
        if not cleaned:
            raise AppError("Question cannot be empty")

        if not document_id:
            return ChatResponse(answer=complete_chat(DIRECT_SYSTEM, cleaned, self.settings), used_rag=False)

        document = self.repository.get_by_id(document_id, user_id)
        if document is None:
            raise NotFoundError("Document not found")
        if document.status == DocumentStatus.PROCESSING:
            raise ConflictError("Document is still processing")
        if document.status != DocumentStatus.READY:
            raise AppError(document.error_message or "Document is not ready for retrieval")

        return self._answer_with_rag(cleaned, document.id)

    def _answer_with_rag(self, question: str, document_id: str) -> ChatResponse:
        query_embedding = embed_texts([question], self.settings)[0]
        retrieved = query_chunks(document_id, query_embedding, self.settings.retrieval_k)
        if not retrieved:
            return ChatResponse(
                answer="I could not find relevant passages in the uploaded PDF for this question.",
                used_rag=True,
            )

        context_blocks = []
        sources: list[SourceChunk] = []
        for item in retrieved:
            page_label = f"page {item.page}" if item.page is not None else "unknown page"
            context_blocks.append(f"[{page_label}]\n{item.text}")
            sources.append(
                SourceChunk(
                    chunk_index=item.chunk_index,
                    page=item.page,
                    text=item.text,
                    score=item.score,
                )
            )

        user_prompt = (
            "Document excerpts:\n\n"
            + "\n\n---\n\n".join(context_blocks)
            + f"\n\nQuestion:\n{question}"
        )
        answer = complete_chat(RAG_SYSTEM, user_prompt, self.settings)
        return ChatResponse(answer=answer, used_rag=True, sources=sources)
