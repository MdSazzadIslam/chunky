import pytest

from app.core.exceptions import AppError, PayloadTooLargeError, UnsupportedMediaError
from app.ingest.pdf import extract_pages, validate_pdf_upload
from tests.fixtures import SAMPLE_PDF


def test_extracts_text_from_pdf() -> None:
    pages = extract_pages(SAMPLE_PDF)
    assert pages
    assert pages[0][0] == 1
    assert "Chunky" in pages[0][1]


def test_rejects_non_pdf_filename() -> None:
    with pytest.raises(AppError, match="Only PDF files"):
        validate_pdf_upload(
            filename="notes.txt",
            content_type="application/pdf",
            pdf_bytes=SAMPLE_PDF,
            max_upload_bytes=10_000,
        )


def test_rejects_text_plain() -> None:
    with pytest.raises(UnsupportedMediaError, match="application/pdf"):
        validate_pdf_upload(
            filename="doc.pdf",
            content_type="text/plain",
            pdf_bytes=SAMPLE_PDF,
            max_upload_bytes=10_000,
        )


def test_rejects_octet_stream() -> None:
    with pytest.raises(UnsupportedMediaError, match="application/pdf"):
        validate_pdf_upload(
            filename="doc.pdf",
            content_type="application/octet-stream",
            pdf_bytes=SAMPLE_PDF,
            max_upload_bytes=10_000,
        )


def test_rejects_missing_content_type() -> None:
    with pytest.raises(UnsupportedMediaError, match="application/pdf"):
        validate_pdf_upload(
            filename="doc.pdf",
            content_type=None,
            pdf_bytes=SAMPLE_PDF,
            max_upload_bytes=10_000,
        )


def test_rejects_oversized_file() -> None:
    with pytest.raises(PayloadTooLargeError):
        validate_pdf_upload(
            filename="doc.pdf",
            content_type="application/pdf",
            pdf_bytes=SAMPLE_PDF,
            max_upload_bytes=10,
        )


def test_sanitizes_path_in_filename() -> None:
    name = validate_pdf_upload(
        filename="../secret.pdf",
        content_type="application/pdf",
        pdf_bytes=SAMPLE_PDF,
        max_upload_bytes=10_000,
    )
    assert name == "secret.pdf"
