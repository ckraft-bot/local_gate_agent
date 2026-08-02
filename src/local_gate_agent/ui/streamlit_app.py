from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow running this file directly with Streamlit while using src-layout packaging.
SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_gate_agent.agents.graph import build_graph
from local_gate_agent.config import SPECIALISTS, load_settings
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


INQUIRY_BUCKETS = {
    "Booking & Account": [
        "Book a new flight / price a fare",
        "Change or modify an existing booking",
        "Refunds and travel credits/vouchers",
        "Loyalty program (miles/points balance, redemptions, status match)",
        "Upgrades (paid or mileage-based)",
    ],
    "Check-in, Boarding & Documents": [
        "Online/kiosk check-in",
        "Boarding pass issues",
        "Boarding group/zone and seat assignment",
        "ID/passport/visa requirements, TSA PreCheck/Global Entry",
        "Denied boarding due to document issues",
    ],
    "Flight Status & Baggage": [
        "Flight/gate status and gate changes",
        "Checked bag fees and allowance",
        "Lost, delayed, or damaged bags",
        "Gate-checking carry-ons",
        "Connections and missed-connection handling",
    ],
    "Disruptions & Special Situations": [
        "Delays, cancellations, and rebooking",
        "Denied boarding / oversold flights (compensation and rights)",
        "Special assistance (wheelchair, unaccompanied minor, service animal, medical equipment)",
        "Pet travel policy (cabin/cargo)",
        "Lost & found (items left on plane or at gate)",
    ],
}


st.set_page_config(page_title="Local Gate Agent RAG", page_icon="🛫", layout="wide")

settings = load_settings()
store = LocalVectorStore(settings)

if "graph" not in st.session_state:
    st.session_state.graph = build_graph(settings, store)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_bucket" not in st.session_state:
    st.session_state.active_bucket = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "pending_bucket" not in st.session_state:
    st.session_state.pending_bucket = None

st.title("Virtual Gate Agent")
st.caption("Fully local: Ollama + Chroma + LangGraph + Streamlit")

with st.sidebar:
    st.subheader("Setup Checklist")
    st.write("1. Start Ollama")
    st.write("2. Pull chat and embedding models")
    st.write("3. Run ingestion script")
    st.write("4. Ask questions in chat")

    st.subheader("Inquiry Buckets")
    st.caption("Choose a bucket to load common customer follow-up questions.")

    for bucket_name in INQUIRY_BUCKETS:
        if st.button(bucket_name, key=f"bucket_{bucket_name}", use_container_width=True):
            st.session_state.active_bucket = bucket_name
            st.rerun()

    if st.session_state.active_bucket:
        active_bucket = st.session_state.active_bucket
        st.markdown(f"**Selected:** {active_bucket}")

        for idx, followup in enumerate(INQUIRY_BUCKETS[active_bucket]):
            if st.button(followup, key=f"followup_{active_bucket}_{idx}", use_container_width=True):
                st.session_state.pending_query = followup
                st.session_state.pending_bucket = active_bucket
                st.rerun()

    with st.expander("Specialists (auto-routed by supervisor)"):
        for spec in SPECIALISTS.values():
            st.write(f"- {spec.label}")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.active_bucket = None
        st.session_state.pending_query = None
        st.session_state.pending_bucket = None
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.session_state.pending_query
selected_bucket = st.session_state.pending_bucket

typed_query = st.chat_input("Ask a gate operations question...")
if typed_query:
    query = typed_query
    selected_bucket = None

if query:
    st.session_state.pending_query = None
    st.session_state.pending_bucket = None

    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    graph_query = query
    if selected_bucket:
        graph_query = f"Bucket context: {selected_bucket}. User inquiry: {query}"

    initial_state = {
        "messages": st.session_state.messages,
        "user_query": graph_query,
        "routed_specialists": [],
        "specialist_findings": {},
        "specialist_sources": {},
        "specialist_evidence_docs": {},
        "aggregated_context": "",
        "draft_answer": "",
        "self_check_feedback": "",
        "retries": 0,
        "final_answer": "",
    }

    with st.chat_message("assistant"):
        with st.spinner("Thinking across specialists..."):
            result = st.session_state.graph.invoke(initial_state)
            answer = result.get("final_answer", "No answer generated.")
            st.markdown(answer)

            with st.expander("Sources used"):
                routed = result.get("routed_specialists", [])
                sources = result.get("specialist_sources", {})
                if not routed:
                    st.write("No specialists were routed.")
                for key in routed:
                    label = SPECIALISTS[key].label
                    st.markdown(f"**{label}**")
                    for source_id in sources.get(key, []):
                        st.write(f"- {source_id}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
