from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str
    page: int | None


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int,
    overlap: int,
) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    chunks: list[TextChunk] = []
    for page_number, page_text in pages:
        for piece in _split_text(page_text, chunk_size, overlap):
            chunks.append(TextChunk(index=len(chunks), text=piece, page=page_number))
    return chunks


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            end = _prefer_natural_break(text, start, end)
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return pieces


def _prefer_natural_break(text: str, start: int, end: int) -> int:
    window = text[start:end]
    minimum = max(len(window) // 2, 1)
    for separator in (". ", "? ", "! ", "\n", " "):
        index = window.rfind(separator)
        if index >= minimum:
            return start + index + len(separator)
    return end

