from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def load_markdown_documents(root: str | Path) -> list[Document]:
    base = Path(root)
    if not base.exists():
        return []
    documents: list[Document] = []
    for path in sorted(base.rglob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        title = text.splitlines()[0].lstrip("# ").strip() or path.stem
        documents.append(Document(
            document_id=str(path.relative_to(base)),
            title=title,
            text=text,
            metadata={"path": str(path), "type": "markdown"},
        ))
    return documents


def load_pdf_documents(root: str | Path) -> list[Document]:
    base = Path(root)
    if not base.exists():
        return []
    pdfs = sorted(base.rglob("*.pdf"))
    if not pdfs:
        return []
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required to ingest PDF research papers") from exc

    documents: list[Document] = []
    for path in pdfs:
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        text = "\n\n".join(page for page in pages if page).strip()
        if not text:
            continue
        title = (reader.metadata.title if reader.metadata else None) or path.stem
        documents.append(Document(
            document_id=str(path.relative_to(base)),
            title=str(title),
            text=text,
            metadata={"path": str(path), "type": "pdf", "pages": len(reader.pages)},
        ))
    return documents


def load_documents(root: str | Path) -> list[Document]:
    return load_markdown_documents(root) + load_pdf_documents(root)
