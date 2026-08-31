from pathlib import Path

from src.rag.documents import load_markdown_documents


def test_markdown_loader(tmp_path: Path):
    (tmp_path / "note.md").write_text("# Test Note\nMomentum research text.", encoding="utf-8")
    docs = load_markdown_documents(tmp_path)
    assert len(docs) == 1
    assert docs[0].title == "Test Note"
    assert docs[0].metadata["type"] == "markdown"
