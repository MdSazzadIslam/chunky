from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, document_id: str, user_id: str) -> Document | None:
        return self.db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        ).scalar_one_or_none()

    def get_by_hash(self, user_id: str, file_hash: str) -> Document | None:
        return self.db.execute(
            select(Document).where(Document.user_id == user_id, Document.file_hash == file_hash)
        ).scalar_one_or_none()

    def add(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def save(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
