import re

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.document import DocumentRepository
from app.services.chat import ChatService
from app.services.documents import DocumentService

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    user_id = x_user_id.strip()
    if not USER_ID_PATTERN.fullmatch(user_id):
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")
    return user_id


def get_document_repository(db: Session = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentService:
    return DocumentService(repository)


def get_chat_service(
    repository: DocumentRepository = Depends(get_document_repository),
) -> ChatService:
    return ChatService(repository)
