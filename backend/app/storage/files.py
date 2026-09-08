from pathlib import Path

from app.core.config import Settings, get_settings


def save_pdf(user_id: str, document_id: str, pdf_bytes: bytes, settings: Settings | None = None) -> Path:
    config = settings or get_settings()
    user_dir = config.uploads_dir / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{document_id}.pdf"
    path.write_bytes(pdf_bytes)
    return path
