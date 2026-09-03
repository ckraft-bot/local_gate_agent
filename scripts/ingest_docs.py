from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from local_gate_agent.config import load_settings
from local_gate_agent.ingestion.docling_ingest import DoclingIngestor
from local_gate_agent.ingestion.source_registry import flightaware_metadata
from local_gate_agent.ingestion.web_ingest import WebIngestor
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


FLIGHTAWARE_URL = "https://www.flightaware.com/"


def discover_pdf_sources(project_root: Path, source_dir: Path) -> List[Path]:
    source_dir.mkdir(parents=True, exist_ok=True)

    in_source_dir = sorted(source_dir.glob("*.pdf"))
    if in_source_dir:
        return in_source_dir

    # Fallback to repo root PDFs to support existing files already added by user.
    in_root = sorted(project_root.glob("*.pdf"))
    return in_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local PDFs and approved web sources into Chroma.")
    parser.add_argument("--source", type=str, default="", help="Optional specific source file or directory")
    parser.add_argument("--flightaware", action="store_true", help="Ingest the public FlightAware homepage")
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

    if not paths and not args.flightaware:
        raise SystemExit("No sources selected. Put PDFs in data/sources, or pass --flightaware.")

    total = ingestor.ingest_files(paths)
    if args.flightaware:
        total += WebIngestor(store).ingest_url(FLIGHTAWARE_URL, flightaware_metadata())
    print(f"Ingested {total} chunks from {len(paths)} PDF file(s){' and FlightAware' if args.flightaware else ''}.")


if __name__ == "__main__":
    main()
