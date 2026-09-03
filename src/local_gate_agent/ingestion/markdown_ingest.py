from __future__ import annotations

from pathlib import Path
from typing import Iterable

from local_gate_agent.ingestion.source_registry import infer_metadata_for_source
from local_gate_agent.ingestion.web_ingest import chunk_text
from local_gate_agent.retrieval.chroma_store import LocalVectorStore
from local_gate_agent.schemas import ChunkRecord


class MarkdownIngestor:
    """Persists local Markdown documents as source-attributed Chroma chunks."""

    def __init__(self, vector_store: LocalVectorStore):
        self.vector_store = vector_store

    def ingest_files(self, paths: Iterable[Path]) -> int:
        total = 0
        for path in paths:
            source_name = path.name
            self.vector_store.delete_chunks_for_source(source_name)
            records = [
                ChunkRecord(
                    chunk_id=self.vector_store.deterministic_chunk_id(source_name, index, text),
                    text=text,
                    metadata={**infer_metadata_for_source(path), "chunk_index": str(index)},
                )
                for index, text in enumerate(chunk_text(path.read_text(encoding="utf-8")))
            ]
            total += self.vector_store.upsert_chunks(records)
        return total