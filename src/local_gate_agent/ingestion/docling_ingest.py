from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from local_gate_agent.ingestion.source_registry import infer_metadata_for_source
from local_gate_agent.retrieval.chroma_store import LocalVectorStore
from local_gate_agent.schemas import ChunkRecord


class DoclingIngestor:
    """Converts docs to chunks with Docling, then persists embeddings in Chroma."""

    def __init__(self, vector_store: LocalVectorStore):
        self.vector_store = vector_store

    def _chunk_with_docling(self, source_path: Path) -> List[str]:
        # Docling APIs evolve quickly; this import pattern keeps failures explicit.
        try:
            from docling.document_converter import DocumentConverter
            from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
        except ImportError as exc:
            raise RuntimeError(
                "Docling packages are missing. Install requirements and retry ingestion."
            ) from exc

        converter = DocumentConverter()
        result = converter.convert(source_path)
        document = result.document

        chunker = HybridChunker()
        chunks = []
        for chunk in chunker.chunk(document):
            text = getattr(chunk, "text", "") or str(chunk)
            if text.strip():
                chunks.append(text.strip())
        return chunks

    def ingest_files(self, paths: Iterable[Path]) -> int:
        total = 0
        for path in paths:
            source_metadata = infer_metadata_for_source(path)
            chunk_texts = self._chunk_with_docling(path)

            chunk_records = []
            for idx, text in enumerate(chunk_texts):
                chunk_id = self.vector_store.deterministic_chunk_id(path.name, idx, text)
                metadata = {
                    **source_metadata,
                    "chunk_index": str(idx),
                }
                chunk_records.append(ChunkRecord(chunk_id=chunk_id, text=text, metadata=metadata))

            total += self.vector_store.upsert_chunks(chunk_records)
        return total
