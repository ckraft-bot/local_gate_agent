# Local Gate Agent: Multi-Agent RAG (Fully Local)

This repository is scaffolded from your architecture in `agentic-rag-architecture.md`.

Stack:
- Ingestion: Docling
- Vector store: Chroma (persistent, local)
- Models: Ollama (chat + embeddings)
- Orchestration: LangGraph (supervisor -> specialists -> synthesizer -> self-check)
- UI: Streamlit

## Current Project Layout

```text
local_gate_agent/
	data/
		chroma/
		sources/
	scripts/
		ingest_docs.py
		run_app.py
	src/local_gate_agent/
		agents/
			graph.py
			nodes.py
			prompts.py
			state.py
			tools.py
		ingestion/
			docling_ingest.py
			source_registry.py
		retrieval/
			chroma_store.py
		ui/
			streamlit_app.py
		config.py
		schemas.py
	tests/
		test_source_registry.py
	.env.example
	requirements.txt
```

## Your Existing PDFs

The ingestion script will first look in `data/sources/`.
If none are there yet, it automatically falls back to PDFs in the repo root.

Detected root PDFs:
- `airport_codes.pdf`
- `airport_operation_agent.pdf`
- `aviation_abbreviations.pdf`
- `aviation_alphabet.pdf`
- `cabin_safety_compendium.pdf`
- `EATC_ground_operations_manual_2022.pdf`
- `IATA_code_list.pdf`

These are pre-mapped in `source_registry.py` to procedure categories and metadata fields
(`source_type`, `confidentiality`, `version`, etc.).

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy env template:

```bash
copy .env.example .env
```

4. Start Ollama and pull models:

```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

5. Ingest PDFs:

```bash
python scripts/ingest_docs.py
```

6. Launch app:

```bash
streamlit run src/local_gate_agent/ui/streamlit_app.py
```

## Notes

- Chroma persistence is under `data/chroma/`.
- Chunk IDs are deterministic so re-ingesting updates chunks instead of blind duplication.
- The graph supports self-check retries via `SELF_CHECK_MAX_RETRIES`.
- To ingest a specific path:

```bash
python scripts/ingest_docs.py --source path/to/file-or-folder
```

## Next Improvements

- Add richer citations (page/section) from Docling chunk metadata.
- Add parallel specialist execution node(s) in graph.
- Add authentication and role-based access if this becomes multi-user.