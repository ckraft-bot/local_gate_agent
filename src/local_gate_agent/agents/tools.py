from __future__ import annotations

from typing import Dict, List, Tuple

from local_gate_agent.config import SPECIALISTS, Settings
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


def retrieve_for_specialist(
    query: str,
    specialist_key: str,
    store: LocalVectorStore,
    settings: Settings,
) -> Tuple[List[str], List[str]]:
    specialist = SPECIALISTS[specialist_key]
    documents: List[str] = []
    source_ids: List[str] = []

    source_names = specialist.source_names or []
    if source_names:
        for source_name in source_names:
            results = store.query(
                query_text=query,
                top_k=settings.top_k,
                where={"source": source_name},
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            for doc, meta in zip(docs, metas):
                source = meta.get("source", "unknown")
                chunk_index = meta.get("chunk_index", "?")
                documents.append(doc)
                source_ids.append(f"{source}#chunk_{chunk_index}")
    else:
        for category in specialist.procedure_categories:
            results = store.query(
                query_text=query,
                top_k=settings.top_k,
                where={"procedure_category": category},
            )

            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]

            for doc, meta in zip(docs, metas):
                source = meta.get("source", "unknown")
                chunk_index = meta.get("chunk_index", "?")
                source_id = f"{source}#chunk_{chunk_index}"
                documents.append(doc)
                source_ids.append(source_id)

    dedup_sources = list(dict.fromkeys(source_ids))
    return documents, dedup_sources
