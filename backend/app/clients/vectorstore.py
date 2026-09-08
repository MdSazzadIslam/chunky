import logging
from dataclasses import dataclass
from typing import Any

import chromadb

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_client: Any = None
_client_path: str | None = None
COLLECTION_NAME = "document_chunks"


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_index: int
    page: int | None
    text: str
    score: float


def get_collection(settings: Settings | None = None) -> Any:
    global _client, _client_path
    config = settings or get_settings()
    chroma_path = str(config.chroma_dir)
    if _client is None or _client_path != chroma_path:
        _client = chromadb.PersistentClient(path=chroma_path)
        _client_path = chroma_path
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(
    document_id: str,
    user_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    pages: list[int | None],
) -> None:
    collection = get_collection()
    ids = [f"{document_id}:{index}" for index in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "user_id": user_id,
            "chunk_index": index,
            "page": page if page is not None else -1,
        }
        for index, page in enumerate(pages)
    ]
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def query_chunks(document_id: str, query_embedding: list[float], k: int) -> list[RetrievedChunk]:
    collection = get_collection()
    try:
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(k, 1),
            where={"document_id": document_id},
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        logger.exception("Vector query failed for document_id=%s", document_id)
        return []

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    retrieved: list[RetrievedChunk] = []
    for text, metadata, distance in zip(documents, metadatas, distances, strict=False):
        page_value = metadata.get("page")
        page = None if page_value in (None, -1) else int(page_value)
        retrieved.append(
            RetrievedChunk(
                chunk_index=int(metadata.get("chunk_index", 0)),
                page=page,
                text=text,
                score=1 - float(distance),
            )
        )
    return retrieved
