from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_document_service, get_user_id
from app.core.config import get_settings
from app.core.exceptions import PayloadTooLargeError, UnsupportedMediaError
from app.ingest.pdf import is_pdf_content_type
from app.schemas.document import DocumentResponse
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


async def _read_pdf_upload(file: UploadFile, max_bytes: int) -> bytes:
    if not is_pdf_content_type(file.content_type):
        raise UnsupportedMediaError("Only application/pdf is allowed")
    chunks = bytearray()
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        if len(chunks) + len(chunk) > max_bytes:
            raise PayloadTooLargeError(f"File exceeds the {max_bytes} byte limit")
        chunks.extend(chunk)
    return bytes(chunks)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    pdf_bytes = await _read_pdf_upload(file, get_settings().max_upload_bytes)
    result = service.upload(
        user_id=user_id,
        filename=file.filename,
        content_type=file.content_type,
        pdf_bytes=pdf_bytes,
    )
    return DocumentResponse.from_document(result.document, duplicate=result.duplicate)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    user_id: str = Depends(get_user_id),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    document = service.get(document_id, user_id)
    return DocumentResponse.from_document(document)
