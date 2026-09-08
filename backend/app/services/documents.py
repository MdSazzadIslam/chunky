import logging
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.clients.llm import embed_texts
from app.clients.vectorstore import upsert_chunks
from app.core.config import Settings, get_settings
from app.core.enums import DocumentStatus
from app.core.exceptions import AppError, NotFoundError
from app.ingest.chunking import chunk_pages
from app.ingest.hashing import sha256_bytes
from app.ingest.pdf import extract_pages, validate_pdf_upload
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.storage.files import save_pdf

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadResult:
    document: Document
    duplicate: bool


class DocumentService:
    def __init__(self, repository: DocumentRepository, settings: Settings | None = None) -> None:
        self.repository = repository
        self.settings = settings or get_settings()

    def get(self, document_id: str, user_id: str) -> Document:
        document = self.repository.get_by_id(document_id, user_id)
        if document is None:
            raise NotFoundError("Document not found")
        return document

    def upload(
        self,
        *,
        user_id: str,
        filename: str | None,
        content_type: str | None,
        pdf_bytes: bytes,
    ) -> UploadResult:
        safe_name = validate_pdf_upload(
            filename=filename,
            content_type=content_type,
            pdf_bytes=pdf_bytes,
            max_upload_bytes=self.settings.max_upload_bytes,
        )
        file_hash = sha256_bytes(pdf_bytes)
        existing = self.repository.get_by_hash(user_id, file_hash)

        if existing and existing.status == DocumentStatus.READY:
            logger.info("Returning existing document %s for user %s", existing.id, user_id)
            return UploadResult(document=existing, duplicate=True)

        document = existing
        if document is None:
            document = Document(
                user_id=user_id,
                file_hash=file_hash,
                filename=safe_name,
                status=DocumentStatus.PROCESSING,
                storage_path="",
            )
            try:
                document = self.repository.add(document)
            except IntegrityError:
                self.repository.db.rollback()
                raced = self.repository.get_by_hash(user_id, file_hash)
                if raced and raced.status == DocumentStatus.READY:
                    return UploadResult(document=raced, duplicate=True)
                if raced is None:
                    raise
                document = raced
        document.status = DocumentStatus.PROCESSING
        document.filename = safe_name
        document.error_message = None
        document = self.repository.save(document)

        storage_path = save_pdf(user_id, document.id, pdf_bytes, self.settings)
        document.storage_path = str(storage_path)
        document = self.repository.save(document)

        try:
            self._ingest(document, pdf_bytes)
        except AppError as exc:
            logger.exception("Failed to process document %s", document.id)
            return self._mark_error(document, exc.detail, duplicate=existing is not None)
        except Exception:
            logger.exception("Failed to process document %s", document.id)
            return self._mark_error(
                document,
                "Failed to process this PDF",
                duplicate=existing is not None,
            )

        document.status = DocumentStatus.READY
        document.error_message = None
        document = self.repository.save(document)
        logger.info("Document %s is ready", document.id)
        return UploadResult(document=document, duplicate=existing is not None)

    def _mark_error(self, document: Document, message: str, *, duplicate: bool) -> UploadResult:
        document.status = DocumentStatus.ERROR
        document.error_message = message
        document = self.repository.save(document)
        return UploadResult(document=document, duplicate=duplicate)

    def _ingest(self, document: Document, pdf_bytes: bytes) -> None:
        pages = extract_pages(pdf_bytes, max_pdf_pages=self.settings.max_pdf_pages)
        if not pages:
            raise AppError("No extractable text found in this PDF")

        chunks = chunk_pages(pages, self.settings.chunk_size, self.settings.chunk_overlap)
        if not chunks:
            raise AppError("PDF text could not be chunked")

        embeddings = embed_texts([chunk.text for chunk in chunks], self.settings)
        upsert_chunks(
            document_id=document.id,
            user_id=document.user_id,
            chunks=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            pages=[chunk.page for chunk in chunks],
        )
