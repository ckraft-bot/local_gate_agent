from __future__ import annotations

from typing import Dict, List, TypedDict


class GraphState(TypedDict):
    messages: List[Dict[str, str]]
    user_query: str
    routed_specialists: List[str]
    specialist_findings: Dict[str, str]
    specialist_sources: Dict[str, List[str]]
    aggregated_context: str
    draft_answer: str
    self_check_feedback: str
    retries: int
    final_answer: str
