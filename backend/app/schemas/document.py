from app.core.enums import DocumentStatus
from app.models.document import Document
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    duplicate: bool = False
    error_message: str | None = None

    @classmethod
    def from_document(cls, document: Document, *, duplicate: bool = False) -> "DocumentResponse":
        return cls(
            document_id=document.id,
            filename=document.filename,
            status=DocumentStatus(document.status),
            duplicate=duplicate,
            error_message=document.error_message,
        )
