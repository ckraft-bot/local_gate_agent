from __future__ import annotations

from html.parser import HTMLParser
from typing import TYPE_CHECKING, List
from urllib import request
from urllib.parse import urlparse

from local_gate_agent.schemas import ChunkRecord

if TYPE_CHECKING:
    from local_gate_agent.retrieval.chroma_store import LocalVectorStore


class _TextExtractor(HTMLParser):
    _SKIPPED_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self._skipped_depth = 0
        self.parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]) -> None:
        _ = attrs
        if tag in self._SKIPPED_TAGS:
            self._skipped_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIPPED_TAGS and self._skipped_depth:
            self._skipped_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skipped_depth and data.strip():
            self.parts.append(data.strip())


def extract_html_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(parser.parts)


def chunk_text(text: str, chunk_size: int = 1_200) -> List[str]:
    words = text.split()
    chunks: List[str] = []
    current: List[str] = []
    current_length = 0
    for word in words:
        word_length = len(word) + (1 if current else 0)
        if current and current_length + word_length > chunk_size:
            chunks.append(" ".join(current))
            current = []
            current_length = 0
        current.append(word)
        current_length += word_length
    if current:
        chunks.append(" ".join(current))
    return chunks


class WebIngestor:
    """Fetches an approved public web page and persists readable text in Chroma."""

    def __init__(self, vector_store: LocalVectorStore):
        self.vector_store = vector_store

    @staticmethod
    def _source_name(url: str) -> str:
        return f"web:{urlparse(url).netloc}"

    def ingest_url(self, url: str, metadata: dict[str, str]) -> int:
        source_name = self._source_name(url)
        self.vector_store.delete_chunks_for_source(source_name)

        req = request.Request(url, headers={"User-Agent": "local-gate-agent/1.0"})
        with request.urlopen(req, timeout=30) as response:
            html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")

        chunks = chunk_text(extract_html_text(html))
        records = [
            ChunkRecord(
                chunk_id=self.vector_store.deterministic_chunk_id(source_name, index, text),
                text=text,
                metadata={**metadata, "source": source_name, "source_url": url, "chunk_index": str(index)},
            )
            for index, text in enumerate(chunks)
        ]
        return self.vector_store.upsert_chunks(records)