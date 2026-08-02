from __future__ import annotations

import json
from urllib import request
from typing import Dict, Iterable, List, Sequence

import chromadb

from local_gate_agent.config import Settings
from local_gate_agent.schemas import ChunkRecord


class LocalVectorStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.collection = self.client.get_or_create_collection(name=settings.collection_name)

    @staticmethod
    def deterministic_chunk_id(source: str, chunk_index: int, text: str) -> str:
        _ = text  # Signature kept stable for callers; ID is source+index by design.
        return f"{source}:{chunk_index}"

    def delete_chunks_for_source(self, source_filename: str) -> None:
        existing = self.collection.get(where={"source": source_filename}, include=[])
        ids = existing.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)

    def _embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        payload = json.dumps(
            {
                "model": self.settings.embedding_model,
                "input": list(texts),
            }
        ).encode("utf-8")
        req = request.Request(
            url=f"{self.settings.ollama_host.rstrip('/')}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        if "embeddings" in body:
            return body["embeddings"]
        if "embedding" in body:
            return [body["embedding"]]
        raise RuntimeError("Ollama /api/embed response missing embeddings field.")

    def upsert_chunks(self, chunks: Iterable[ChunkRecord]) -> int:
        chunk_list = list(chunks)
        if not chunk_list:
            return 0

        texts = [c.text for c in chunk_list]
        embeddings = self._embed_texts(texts)
        self.collection.upsert(
            ids=[c.chunk_id for c in chunk_list],
            documents=texts,
            metadatas=[c.metadata for c in chunk_list],
            embeddings=embeddings,
        )
        return len(chunk_list)

    def query(
        self,
        query_text: str,
        top_k: int,
        where: Dict[str, str] | None = None,
    ) -> Dict[str, List]:
        embedding = self._embed_texts([query_text])[0]
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
