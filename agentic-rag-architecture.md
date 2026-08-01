# Local Multi-Agent RAG — Architecture & Wiring Plan

A fully local, multi-agent RAG chatbot. No cloud dependencies, no API costs.

**Stack:** Docling (ingestion) → Chroma (vector store) → LangGraph multi-agent system on Ollama (supervisor + domain specialists + synthesizer, with self-check) → Streamlit (UI)

---

## 1. High-Level Flow

```mermaid
flowchart TD
    subgraph Ingestion["Ingestion Pipeline (offline / on-demand)"]
        A[Source documents<br/>PDF, DOCX, PPTX, URLs] --> B[Docling<br/>DocumentConverter]
        B --> C[Docling HybridChunker<br/>structure-aware chunks]
        C --> D[Ollama Embedding Model<br/>nomic-embed-text]
        D --> E[(Chroma<br/>persistent vector store<br/>chunks tagged with domain metadata)]
    end

    subgraph ChatLoop["Multi-Agent Chat Loop (per user turn)"]
        F[User question<br/>Streamlit chat input] --> S[Supervisor Agent<br/>classifies question, routes to 1+ specialists]

        S --> R1[Specialist Agent A<br/>e.g. Regulatory/Operations]
        S --> R2[Specialist Agent B<br/>e.g. Maintenance]
        S --> R3[Specialist Agent C<br/>e.g. Airspace/Procedures]
        S --> R4[Specialist Agent D<br/>e.g. UAS/Drones]

        R1 -->|tool call| T1[Retrieve Tool<br/>Chroma filtered by domain]
        R2 -->|tool call| T2[Retrieve Tool<br/>Chroma filtered by domain]
        R3 -->|tool call| T3[Retrieve Tool<br/>Chroma filtered by domain]
        R4 -->|tool call| T4[Retrieve Tool<br/>Chroma filtered by domain]
        T1 --> R1
        T2 --> R2
        T3 --> R3
        T4 --> R4

        R1 --> AG[Aggregator]
        R2 --> AG
        R3 --> AG
        R4 --> AG

        AG --> Y[Synthesizer Agent<br/>merges specialist findings,<br/>resolves conflicts, drafts answer]
        Y --> I[Self-Check Node<br/>LLM judges groundedness<br/>vs. all retrieved context]
        I -->|unsupported, retries left| S
        I -->|supported / retries exhausted| J[Final Answer]
        J --> K[Streamlit renders answer<br/>+ sources used per specialist]
    end

    E -.retrieval reads from.-> T1
    E -.retrieval reads from.-> T2
    E -.retrieval reads from.-> T3
    E -.retrieval reads from.-> T4
```

Only specialists the supervisor actually routes to are invoked for a given question — the diagram shows all four as the general shape, not every query hitting every specialist.

---

## 2. Components

### 2.1 Ingestion: Docling

- Converts raw source documents (PDF, DOCX, PPTX, and URLs) into structured data, preserving text, tables, section headers, and formulas rather than flattening everything to plain text.
- `HybridChunker` splits the structured document into chunks that respect document boundaries (won't split a table mid-row) while staying within a token budget suitable for the embedding model.
- Output of this stage: a list of text chunks, each tagged with metadata (source file, chunk index, and optionally section/page).
- Runs offline / on-demand — this is not part of the live chat request path. It's triggered whenever new documents are added or existing ones change.

### 2.2 Storage: Chroma

- Persistent vector store, embedded directly in the Python process — no separate server to run or manage.
- Each chunk is embedded (via an Ollama-hosted embedding model) and stored with its metadata, enabling both semantic similarity search and metadata filtering (e.g., "only search chunks from report_2025.pdf," or — in the multi-agent design — "only search chunks tagged to the Maintenance specialist's domain").
- One shared collection, not one per specialist: each specialist's `retrieve` tool just applies a different metadata filter (e.g., a `domain` or `far_part_group` field) over the same underlying store. Simpler to maintain than separate collections, and still gives each specialist an isolated view of the corpus.
- Chunk IDs are derived deterministically from `source + chunk_index`, so re-ingesting an updated document overwrites the old chunks instead of duplicating them.
- Storage lives on local disk in a persistent directory — no ongoing cost, no external dependency.

### 2.3 Embedding & Chat Models: Ollama

- **Embedding model** (e.g. `nomic-embed-text`): converts chunk text and user queries into vectors for similarity search. Runs locally via Ollama.
- **Chat model** (e.g. `qwen2.5` or `llama3.1`): the reasoning engine for the agent. Needs solid tool-calling support, since the agent's core behavior (deciding when to retrieve) depends on it.
- Both models are pulled once via Ollama and run entirely on local hardware — no per-token API cost.

### 2.4 Orchestration: LangGraph Multi-Agent System

Instead of one agent doing everything, responsibility is split across specialized roles. This is the **supervisor pattern**: one routing agent, several domain specialists, one synthesizer, one quality gate.

| Role | Responsibility |
|---|---|
| **Supervisor agent** | Reads the user's question and decides which specialist(s) are relevant (one, several, or — for narrow-scope questions — just one). Routes the question to those specialists. Also the re-entry point if self-check fails. |
| **Specialist agents** (2–4, domain-scoped) | Each is a small retrieve-capable agent focused on one subject area, with its own system prompt and its own `retrieve` tool pre-scoped to that domain's slice of the corpus (via metadata filtering, not a separate vector store). Each can call `retrieve` more than once to refine its query, same as the single-agent version did. |
| **Aggregator** | Simple merge step — collects each invoked specialist's findings (draft notes + the chunks they retrieved) into one shared state, no LLM call needed. |
| **Synthesizer agent** | Takes the aggregated specialist findings and produces one coherent final answer — resolving overlaps, flagging disagreement between specialists if it exists, and consolidating citations. |
| **Self-check node** | Judges whether the synthesized answer is actually supported by the full set of retrieved context across all specialists. If not, and retries remain, routes back to the supervisor with a critique so it can adjust routing or ask a specialist to re-retrieve. Capped at a small max-retries count. |

**Why multi-agent vs. one agent with one tool:**
- **Focused prompts beat one generalist prompt.** A specialist scoped to "maintenance guidance" can have a system prompt and retrieval scope tuned to that vocabulary, instead of one prompt trying to cover every domain adequately.
- **Parallelizable.** When a question spans domains (e.g., "what maintenance signoffs affect part 91 operating limits"), specialists can run concurrently instead of one agent serially reasoning through both areas.
- **Cleaner scaling.** Adding a new domain (e.g., airport/Part 150 guidance) means adding one new specialist node, not re-tuning one large prompt that's already covering several domains.
- **Trade-off to know going in:** more LLM calls per turn than the single-agent version (supervisor routing + N specialists + synthesis + self-check), so latency and local-compute load go up. Worth it once domain scope is broad enough that one generalist agent starts giving inconsistent answers across topics — not necessary for a narrow corpus.

### 2.5 Interface: Streamlit

- Standard chat UI: message history, chat input box, streaming/spinner while the agent runs.
- Displays the final answer, and an expandable "Sources used" section pulled from whichever chunks were retrieved during that turn.
- Sidebar for setup checklist and a "clear conversation" control to reset session state.
- Runs as a single local web app — no external hosting required.

---

## 3. Wiring Plan (data & control flow)

**Ingestion path (run when documents are added/updated):**

```
Source files/URLs
   → Docling DocumentConverter
   → Docling HybridChunker
   → Ollama embedding model
   → Chroma (persistent collection)
```

**Query path (run per user message):**

```
Streamlit chat input
   → LangGraph graph invoked with full message history
   → Supervisor agent classifies the question → routes to relevant specialist(s)
   → Each routed specialist (runs independently, in parallel where the graph allows):
        ├── decides to call `retrieve` (domain-filtered) → results appended to its own working notes → may re-query
        └── produces a domain-scoped draft finding + list of chunks it used
   → Aggregator merges all invoked specialists' findings + retrieved chunks into shared state
   → Synthesizer agent combines aggregated findings into one final draft answer
   → Self-check node (Ollama chat model judges groundedness against the full aggregated context)
        ├── UNSUPPORTED + retries remaining → critique appended → back to Supervisor (may re-route or ask a specialist to re-retrieve)
        └── SUPPORTED or retries exhausted → finalize
   → Streamlit renders final answer + source list grouped by specialist
```

**State carried across the loop:**
- Full message history — passed to the graph each turn so context persists across the conversation.
- Per-specialist working state (which specialists were invoked, what each retrieved, each one's draft finding) — collected by the aggregator, consumed by the synthesizer.
- Retry counter — reset each new user turn, incremented only by the self-check node.

---

## 4. Key Configuration Points

| Setting | Where it lives | Notes |
|---|---|---|
| Chat model name | Agent config | Must support tool calling reliably; test a couple of models if retrieval seems inconsistent |
| Embedding model name | Ingestion + agent config (must match) | Same model must be used for both ingesting and querying, or similarity search breaks |
| Chunk size / overlap | Ingestion config | Tune based on document density; denser technical docs may want smaller chunks |
| Top-K retrieved chunks | Retrieve tool config | Controls how much context feeds each answer — tradeoff between completeness and noise |
| Max self-check retries | Agent config | Caps latency/cost of the self-check loop; 1–2 is usually enough |
| Chroma persistence directory | Storage config | Where the vector collection lives on disk |
| Specialist domain definitions | Supervisor + specialist config | Which domains exist, their metadata filter values, and each specialist's system prompt |
| Routing strategy | Supervisor config | Whether the supervisor can route to multiple specialists per question (parallel) or only one (simpler, less coverage for cross-domain questions) |

---

## 5. Setup Sequence (no code, just order of operations)

1. Install Ollama and pull the chat model and embedding model.
2. Point the ingestion process at a folder of source documents (or individual URLs).
3. Run ingestion — produces a populated, persistent Chroma collection.
4. Launch the Streamlit app — it builds the LangGraph agent on startup and connects to the existing Chroma collection.
5. Chat. Re-run ingestion any time new or updated documents need to be added; existing chunks for a changed file are overwritten rather than duplicated.

---

## 6. Use Case: Gate Agent Training Assistant

**Data source:** Internal gate agent training manuals and materials (boarding procedures, customer service SOPs, irregular operations handling, special assistance policies, etc.) — typically **proprietary/internal airline or airport-operator documents**, not public data like the FAA ACs from the earlier draft of this plan.

This changes a few things vs. a public-regulation use case:

- **Confidentiality**: these documents likely shouldn't be treated as freely shareable. Worth tagging metadata with an internal confidentiality/sensitivity level, and being deliberate about who has access to the chat interface itself (this is squarely a case where "fully local, no cloud calls" is a real advantage, not just a cost saver).
- **Supplementary public regulation**: some of what a gate agent needs traces back to public federal rules that can be ingested alongside the internal manuals for grounding, e.g. [14 CFR Part 250](https://www.ecfr.gov/current/title-14/chapter-II/subchapter-D/part-250) (oversales/denied boarding), [14 CFR Part 382](https://www.ecfr.gov/current/title-14/chapter-II/subchapter-D/part-382) (nondiscrimination on the basis of disability — wheelchair service, service animals), and TSA screening/security procedures relevant to gate operations. Keeping these separate from internal SOPs in metadata (`source_type: internal` vs `source_type: public_regulation`) matters, since internal policy sometimes goes beyond the regulatory floor and the agent shouldn't blur the two when citing.
- **Document lifecycle**: training manuals get revised (new procedures, updated seasonal policies like holiday travel rules); an `effective_date` / `version` field matters here just as much as it did for AC revisions.

### Specialist mapping for this domain

| Specialist | Covers | Example question it'd handle |
|---|---|---|
| **Boarding & Documents** | Boarding procedures, ID/document verification, oversold flights & denied boarding (14 CFR Part 250), gate changes | "What's the process when a flight is oversold at boarding?" |
| **Special Assistance & Accommodations** | Wheelchair service, service animals, unaccompanied minors, ADA/Part 382 compliance | "What's the procedure for a passenger requesting wheelchair assistance at the gate?" |
| **Irregular Operations (IROPS)** | Delays, cancellations, misconnections, rebooking, weather holds | "What's the rebooking policy when a flight is cancelled for weather?" |
| **Safety & Security** | TSA/SIDA badge procedures, security protocols at the gate, basic hazmat awareness | "What are the gate security procedures during a ramp closure?" |
| **Baggage & Ramp Coordination** | Checked-bag policies, gate-checking carry-ons, communicating with ramp/baggage crews | "When does a carry-on get gate-checked instead of boarded?" |

Same note as before applies: start with fewer specialists (2–3) if the training material doesn't clearly separate into all five; merge or split based on where questions actually cluster once the assistant is in use.

### Additional metadata fields for this use case

| Field | Why it matters |
|---|---|
| `source_type` (`internal` / `public_regulation`) | Keeps proprietary SOPs distinct from cited public rules in answers |
| `confidentiality` (e.g. `internal_use_only`) | Signals sensitivity; supports access-control decisions outside the RAG system itself |
| `procedure_category` | Maps to the specialist table above for retrieval filtering |
| `effective_date` / `version` | Surfaces which revision of a procedure is current, same role AC revision dates played before |
| `station` / `airline` (if materials cover more than one) | Relevant if training content varies by airport station or carrier |

### A note on scope

FAA and DOT public regulations (14 CFR Part 250, Part 382, TSA requirements) set a floor, but internal training manuals often add airline- or station-specific procedure on top of that floor. This system is well suited to help a gate agent find and understand the right procedure quickly — it's not a substitute for verifying against the current internal manual or a supervisor's guidance for anything unusual, high-stakes, or where the manual itself seems out of date.

---

## 7. Things to Revisit as This Grows

- **Model choice**: if the chat model under- or over-triggers retrieval, that's the first thing to swap/tune.
- **Scale**: Chroma is well-suited to personal/small-team knowledge bases (up to roughly a few million vectors); a migration path to something like Qdrant or pgvector is worth planning for if the corpus grows well beyond that.
- **Self-check cost**: each self-check adds one extra LLM call per turn — worth an on/off toggle if latency becomes more important than answer verification.
- **Multi-user / production concerns** (auth, concurrent access, backups) are out of scope for this personal-use architecture and would need to be layered in separately if requirements change.
- **Specialist count**: start with the fewest specialists that cover distinct domains well (2–3, not necessarily all 4 from §6). Each additional specialist adds routing complexity and per-turn LLM calls — only split further once a single specialist's prompt is visibly straining to cover too much ground.
- **Routing accuracy**: the supervisor's classification is itself a place errors can creep in (misrouting a maintenance question to Regulatory & Operations, for instance). Worth spot-checking routing decisions early, since a wrong route means the right specialist never even ran.
