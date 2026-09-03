from __future__ import annotations

import re
from typing import Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from local_gate_agent.agents.prompts import (
    SELF_CHECK_PROMPT,
    SUPERVISOR_PROMPT,
    SYNTHESIZER_PROMPT,
)
from local_gate_agent.agents.state import GraphState
from local_gate_agent.agents.tools import retrieve_for_specialist
from local_gate_agent.config import SPECIALISTS, Settings
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


def _build_llm(settings: Settings) -> ChatOllama:
    return ChatOllama(model=settings.chat_model, base_url=settings.ollama_host, temperature=0)


def _keyword_route_fallback(query: str) -> List[str]:
    q = query.lower()
    routes = []
    if any(
        k in q
        for k in [
            "ticket counter",
            "check-in",
            "check in",
            "baggage tag",
            "baggage receipt",
            "ticket change",
            "amend reservation",
            "codeshare",
            "destination requirement",
            "entry requirement",
            "outstation",
        ]
    ):
        routes.append("routine_at_counter")
    if any(
        k in q
        for k in [
            "gate routine",
            "open gate",
            "boarding groups",
            "jet bridge",
            "jetbridge",
            "crew check-in",
            "crew check in",
            "load closeout",
            "load-closeout",
            "standby",
            "gate upgrade",
        ]
    ):
        routes.append("routine_at_gate")
    if any(k in q for k in ["wheelchair", "service animal", "disability", "accommodation"]):
        routes.append("special_assistance")
    if any(k in q for k in ["cancel", "delay", "rebook", "weather", "irops"]):
        routes.append("irops")
    if any(k in q for k in ["security", "tsa", "badge", "hazmat", "safety"]):
        routes.append("safety_security")
    if any(k in q for k in ["bag", "baggage", "ramp", "gate-check", "carry-on"]):
        routes.append("baggage_ramp")
    if any(k in q for k in ["boarding", "document", "oversold", "iata", "airport code"]):
        routes.append("boarding_documents")

    if not routes:
        routes.append("boarding_documents")
    return routes[:3]


def supervisor_node(state: GraphState, settings: Settings) -> GraphState:
    llm = _build_llm(settings)
    query = state["user_query"]
    response = llm.invoke(
        [
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=f"Question: {query}"),
        ]
    )
    text = str(response.content).strip().lower()
    routed = [x.strip() for x in re.split(r"[,\n]", text) if x.strip() in SPECIALISTS]

    if not routed:
        routed = _keyword_route_fallback(query)

    if not settings.allow_multi_route and routed:
        routed = routed[:1]

    state["routed_specialists"] = list(dict.fromkeys(routed))
    return state


def specialists_node(state: GraphState, settings: Settings, store: LocalVectorStore) -> GraphState:
    llm = _build_llm(settings)

    findings: Dict[str, str] = {}
    sources: Dict[str, List[str]] = {}
    evidence_docs: Dict[str, List[str]] = {}

    for specialist_key in state["routed_specialists"]:
        specialist = SPECIALISTS[specialist_key]
        docs, source_ids = retrieve_for_specialist(
            query=state["user_query"], specialist_key=specialist_key, store=store, settings=settings
        )

        # A second retrieval pass gives specialists a chance to refine search scope.
        refine_query = f"{state['user_query']} {specialist.label} procedures"
        docs_refined, source_ids_refined = retrieve_for_specialist(
            query=refine_query, specialist_key=specialist_key, store=store, settings=settings
        )

        merged_docs = list(dict.fromkeys(docs + docs_refined))
        merged_source_ids = list(dict.fromkeys(source_ids + source_ids_refined))

        context = "\n\n".join(merged_docs[: settings.top_k]) if merged_docs else "No retrieved context."
        prompt = (
            f"{specialist.system_prompt}\n\n"
            f"User question:\n{state['user_query']}\n\n"
            f"Retrieved context:\n{context}\n\n"
            "Write a brief domain-specific finding with the most relevant details and caveats when context is weak."
        )
        result = llm.invoke([HumanMessage(content=prompt)])

        findings[specialist_key] = str(result.content).strip()
        sources[specialist_key] = merged_source_ids
        evidence_docs[specialist_key] = merged_docs

    state["specialist_findings"] = findings
    state["specialist_sources"] = sources
    state["specialist_evidence_docs"] = evidence_docs
    return state


def aggregator_node(state: GraphState) -> GraphState:
    lines = []
    for specialist_key in state["routed_specialists"]:
        finding = state["specialist_findings"].get(specialist_key, "")
        source_ids = state["specialist_sources"].get(specialist_key, [])
        evidence = state.get("specialist_evidence_docs", {}).get(specialist_key, [])
        evidence_text = "\n\n".join(evidence[:3])
        lines.append(
            f"[{SPECIALISTS[specialist_key].label}]\n"
            f"Finding: {finding}\n"
            f"Sources: {', '.join(source_ids)}\n"
            f"Evidence:\n{evidence_text}"
        )

    state["aggregated_context"] = "\n\n".join(lines)
    return state


def synthesizer_node(state: GraphState, settings: Settings) -> GraphState:
    llm = _build_llm(settings)
    prompt = (
        f"{SYNTHESIZER_PROMPT}\n\n"
        f"User question:\n{state['user_query']}\n\n"
        f"Specialist findings:\n{state['aggregated_context']}"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    state["draft_answer"] = str(result.content).strip()
    return state


def self_check_node(state: GraphState, settings: Settings) -> GraphState:
    llm = _build_llm(settings)
    prompt = (
        f"{SELF_CHECK_PROMPT}\n\n"
        f"Question:\n{state['user_query']}\n\n"
        f"Aggregated context (specialist findings + retrieved evidence):\n{state['aggregated_context']}\n\n"
        f"Draft answer:\n{state['draft_answer']}"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    text = str(result.content).strip()

    if text.upper().startswith("SUPPORTED|"):
        state["final_answer"] = state["draft_answer"]
        state["self_check_feedback"] = text
        return state

    state["retries"] += 1
    state["self_check_feedback"] = text

    if state["retries"] > settings.max_self_check_retries:
        state["final_answer"] = (
            state["draft_answer"]
            + "\n\nNote: self-check could not fully verify all claims from retrieved context."
        )
    return state


def should_retry(state: GraphState, settings: Settings) -> str:
    if state.get("final_answer"):
        return "done"

    feedback = state.get("self_check_feedback", "")
    if feedback.upper().startswith("UNSUPPORTED|") and state["retries"] <= settings.max_self_check_retries:
        return "retry"

    state["final_answer"] = state.get("draft_answer", "")
    return "done"
