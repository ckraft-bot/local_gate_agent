from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from local_gate_agent.config import load_settings
from local_gate_agent.ingestion.docling_ingest import DoclingIngestor
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


def discover_pdf_sources(project_root: Path, source_dir: Path) -> List[Path]:
    source_dir.mkdir(parents=True, exist_ok=True)

    in_source_dir = sorted(source_dir.glob("*.pdf"))
    if in_source_dir:
        return in_source_dir

    # Fallback to repo root PDFs to support existing files already added by user.
    in_root = sorted(project_root.glob("*.pdf"))
    return in_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local PDFs into Chroma.")
    parser.add_argument("--source", type=str, default="", help="Optional specific source file or directory")
    args = parser.parse_args()

    settings = load_settings()
    store = LocalVectorStore(settings)
    ingestor = DoclingIngestor(store)

    if args.source:
        source_path = Path(args.source)
        if source_path.is_dir():
            paths = sorted(source_path.glob("*.pdf"))
        else:
            paths = [source_path]
    else:
        paths = discover_pdf_sources(settings.project_root, settings.source_dir)

    if not paths:
        raise SystemExit("No PDF files found. Put PDFs in data/sources or repo root.")

    total = ingestor.ingest_files(paths)
    print(f"Ingested {total} chunks from {len(paths)} file(s).")


if __name__ == "__main__":
    main()
