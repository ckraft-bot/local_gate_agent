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
from local_gate_agent.ingestion.markdown_ingest import MarkdownIngestor
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


def discover_sources(project_root: Path, source_dir: Path) -> List[Path]:
    source_dir.mkdir(parents=True, exist_ok=True)

    in_source_dir = sorted(path for pattern in ("*.pdf", "*.md") for path in source_dir.glob(pattern))
    if in_source_dir:
        return in_source_dir

    # Fallback to repo root PDFs to support existing files already added by user.
    in_root = sorted(project_root.glob("*.pdf"))
    return in_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local PDFs, Markdown, and approved web sources into Chroma.")
    parser.add_argument("--source", type=str, default="", help="Optional specific source file or directory")
    args = parser.parse_args()

    settings = load_settings()
    store = LocalVectorStore(settings)
    ingestor = DoclingIngestor(store)

    if args.source:
        source_path = Path(args.source)
        if source_path.is_dir():
            paths = sorted(path for pattern in ("*.pdf", "*.md") for path in source_path.glob(pattern))
        else:
            paths = [source_path]
    else:
        paths = discover_sources(settings.project_root, settings.source_dir)

    if not paths:
        raise SystemExit("No sources selected. Put PDFs or Markdown in data/sources.")

    pdf_paths = [path for path in paths if path.suffix.lower() == ".pdf"]
    markdown_paths = [path for path in paths if path.suffix.lower() == ".md"]
    total = ingestor.ingest_files(pdf_paths)
    total += MarkdownIngestor(store).ingest_files(markdown_paths)
    print(f"Ingested {total} chunks from {len(pdf_paths)} PDF file(s), {len(markdown_paths)} Markdown file(s).")


if __name__ == "__main__":
    main()
