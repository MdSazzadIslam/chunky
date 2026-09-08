from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.core.exceptions import AppError, PayloadTooLargeError, UnsupportedMediaError

PDF_CONTENT_TYPE = "application/pdf"


def sanitize_filename(filename: str | None) -> str:
    if not filename or not filename.strip():
        raise AppError("A file is required")
    name = Path(filename).name
    if name in {"", ".", ".."}:
        raise AppError("A file is required")
    return name


def is_pdf_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    return content_type.split(";", 1)[0].strip().lower() == PDF_CONTENT_TYPE


def validate_pdf_upload(
    *,
    filename: str | None,
    content_type: str | None,
    pdf_bytes: bytes,
    max_upload_bytes: int,
) -> str:
    safe_name = sanitize_filename(filename)
    if not safe_name.lower().endswith(".pdf"):
        raise AppError("Only PDF files are allowed")
    if not is_pdf_content_type(content_type):
        raise UnsupportedMediaError("Only application/pdf is allowed")
    if not pdf_bytes:
        raise AppError("The uploaded file is empty")
    if len(pdf_bytes) > max_upload_bytes:
        raise PayloadTooLargeError(f"File exceeds the {max_upload_bytes} byte limit")
    if not pdf_bytes.startswith(b"%PDF"):
        raise AppError("File is not a valid PDF")
    return safe_name


def extract_pages(data: bytes, max_pdf_pages: int | None = None) -> list[tuple[int, str]]:
    reader = _open_pdf(data, max_pdf_pages)
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = " ".join(text.split())
        if cleaned:
            pages.append((index, cleaned))
    return pages


def _open_pdf(data: bytes, max_pdf_pages: int | None) -> PdfReader:
    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:
        raise AppError("File is not a valid PDF") from exc
    if reader.is_encrypted:
        raise AppError("Encrypted PDFs are not allowed")
    if max_pdf_pages is not None and len(reader.pages) > max_pdf_pages:
        raise AppError(f"PDF exceeds the {max_pdf_pages} page limit")
    return reader
