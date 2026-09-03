# Local Gate Agent: Multi-Agent RAG (Fully Local)

This repository implements a fully local, multi-agent RAG assistant for gate-agent training and support.

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
			markdown_ingest.py
			source_registry.py
			web_ingest.py
		retrieval/
			chroma_store.py
		ui/
			streamlit_app.py
		config.py
		schemas.py
	tests/
		test_source_registry.py
		test_web_ingest.py
	.env.example
	requirements.txt
```

## Sources

Ingestion scans `data/sources/` for PDFs and Markdown files. If it has no local sources, it falls back to PDF files in the repository root.

Current PDFs in `data/sources/`:
- `airport_codes.pdf`
- `airport_operation_agent.pdf`
- `aviation_abbreviations.pdf`
- `aviation_alphabet.pdf`
- `cabin_safety_compendium.pdf`
- `EATC_ground_operations_manual_2022.pdf`
- `gate_agent_script.pdf`
- `gate_agent_script_2.pdf`
- `gate_agent_script_3.pdf`
- `IATA_code_list.pdf`

Known PDFs are mapped in `source_registry.py` to procedure categories and metadata fields. Unmapped PDFs use the default boarding-documents metadata.

Routine Markdown sources have dedicated, source-bound specialists:
- `routine_at_gate.md` is used only by the Gate Routine specialist.
- `routine_at_counter.md` is used only by the Ticket Counter Routine specialist.

Run ingestion after creating or changing either routine file so its updated content is available to the matching specialist.

FlightAware is also supported as an opt-in public web source. It fetches only the public homepage at `https://www.flightaware.com/`, extracts readable page text, and stores the source URL with each chunk. It is a point-in-time snapshot after ingestion, not a live operational flight-status integration.

## Quick Start

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy env template:

```powershell
copy .env.example .env
```

4. Start Ollama and pull models:

```powershell
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

5. Ingest local PDFs and Markdown sources:

```powershell
python scripts/ingest_docs.py
```

   To ingest the PDFs and refresh the FlightAware snapshot in the same run:

```powershell
python scripts/ingest_docs.py --flightaware
```

6. Launch app:

```powershell
streamlit run src/local_gate_agent/ui/streamlit_app.py
```

## Notes

- Chroma persistence is under `data/chroma/`.
- Chunk IDs are deterministic so re-ingesting updates chunks instead of blind duplication.
- FlightAware ingestion fetches only `https://www.flightaware.com/`; re-run it to refresh the stored snapshot. Observe FlightAware's terms and access limits.
- The graph supports self-check retries via `SELF_CHECK_MAX_RETRIES`.
- To ingest a specific PDF, Markdown file, or directory:

```powershell
python scripts/ingest_docs.py --source path/to/file-or-folder
```

- To run the focused ingestion tests, first install `pytest` in the virtual environment, then run:

```powershell
pip install pytest
$env:PYTHONPATH = "src"
python -m pytest tests/test_source_registry.py tests/test_web_ingest.py -q
```

## Current Limitations

- FlightAware's public homepage may not contain specific flight results; use an approved FlightAware API or other authorized live-data integration for real-time operational decisions.
- Docling's first ingestion run can take longer while OCR models initialize.
- The application has no authentication or role-based access controls.