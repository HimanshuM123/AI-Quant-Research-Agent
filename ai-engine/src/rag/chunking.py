from src.rag.documents import Chunk, Document


def chunk_document(document: Document, *, chunk_size: int = 900, overlap: int = 120) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    normalized = " ".join(document.text.split())
    if not normalized:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary

        text = normalized[start:end].strip()
        if text:
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}#chunk-{index}",
                    document_id=document.document_id,
                    title=document.title,
                    text=text,
                    metadata={**document.metadata, "chunk_index": index},
                )
            )
            index += 1

        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)

    return chunks
