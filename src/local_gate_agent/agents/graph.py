from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from local_gate_agent.agents.nodes import (
    aggregator_node,
    self_check_node,
    should_retry,
    specialists_node,
    supervisor_node,
    synthesizer_node,
)
from local_gate_agent.agents.state import GraphState
from local_gate_agent.config import Settings
from local_gate_agent.retrieval.chroma_store import LocalVectorStore


def build_graph(settings: Settings, store: LocalVectorStore):
    graph = StateGraph(GraphState)

    graph.add_node("supervisor", lambda s: supervisor_node(s, settings))
    graph.add_node("specialists", lambda s: specialists_node(s, settings, store))
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("synthesizer", lambda s: synthesizer_node(s, settings))
    graph.add_node("self_check", lambda s: self_check_node(s, settings))

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "specialists")
    graph.add_edge("specialists", "aggregator")
    graph.add_edge("aggregator", "synthesizer")
    graph.add_edge("synthesizer", "self_check")

    graph.add_conditional_edges(
        "self_check",
        lambda s: should_retry(s, settings),
        {
            "retry": "supervisor",
            "done": END,
        },
    )

    return graph.compile()
