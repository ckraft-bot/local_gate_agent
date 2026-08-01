from __future__ import annotations

import streamlit as st

from local_gate_agent.agents.graph import build_graph
from local_gate_agent.config import SPECIALISTS, load_settings
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


st.set_page_config(page_title="Local Gate Agent RAG", page_icon="🛫", layout="wide")

settings = load_settings()
store = LocalVectorStore(settings)

if "graph" not in st.session_state:
    st.session_state.graph = build_graph(settings, store)
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Local Gate Agent Training Assistant")
st.caption("Fully local: Ollama + Chroma + LangGraph + Streamlit")

with st.sidebar:
    st.subheader("Setup Checklist")
    st.write("1. Start Ollama")
    st.write("2. Pull chat and embedding models")
    st.write("3. Run ingestion script")
    st.write("4. Ask questions in chat")

    st.subheader("Specialists")
    for spec in SPECIALISTS.values():
        st.write(f"- {spec.label}")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("Ask a gate operations question...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    initial_state = {
        "messages": st.session_state.messages,
        "user_query": query,
        "routed_specialists": [],
        "specialist_findings": {},
        "specialist_sources": {},
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
