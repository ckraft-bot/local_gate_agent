from __future__ import annotations

import hashlib
from typing import Dict, Iterable, List, Sequence

import chromadb
import ollama
from chromadb.api.models.Collection import Collection

from local_gate_agent.config import Settings
from local_gate_agent.schemas import ChunkRecord


class LocalVectorStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.collection = self.client.get_or_create_collection(name=settings.collection_name)

    @staticmethod
    def deterministic_chunk_id(source: str, chunk_index: int, text: str) -> str:
        seed = f"{source}:{chunk_index}:{text[:120]}".encode("utf-8")
        digest = hashlib.sha1(seed).hexdigest()
        return f"{source}:{chunk_index}:{digest[:10]}"

    def _embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        response = ollama.embed(
            model=self.settings.embedding_model,
            input=list(texts),
            host=self.settings.ollama_host,
        )
        return response["embeddings"]

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
