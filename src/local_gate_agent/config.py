from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class SpecialistDefinition:
    key: str
    label: str
    procedure_categories: List[str]
    system_prompt: str
    source_names: List[str] | None = None


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    source_dir: Path
    chroma_dir: Path
    collection_name: str
    ollama_host: str
    chat_model: str
    embedding_model: str
    top_k: int
    max_self_check_retries: int
    allow_multi_route: bool


SPECIALISTS: Dict[str, SpecialistDefinition] = {
    "routine_at_gate": SpecialistDefinition(
        key="routine_at_gate",
        label="Gate Routine",
        procedure_categories=["gate_routine"],
        source_names=["routine_at_gate.md"],
        system_prompt=(
            "You are the gate-routine specialist. Answer only from the documented gate "
            "workflow. Cover gate preparation, crew check-in, boarding, standby and upgrades, "
            "carry-on handling, passenger accommodations, jetbridge operation, disruptions, "
            "oversales, and load-closeout coordination. State when airline-specific procedures "
            "or ownership are not established by the source."
        ),
    ),
    "routine_at_counter": SpecialistDefinition(
        key="routine_at_counter",
        label="Ticket Counter Routine",
        procedure_categories=["ticket_counter_routine"],
        source_names=["routine_at_counter.md"],
        system_prompt=(
            "You are the ticket-counter routine specialist. Answer only from the documented "
            "counter workflow. Cover check-in, reservations, ticket changes, destination entry "
            "requirements, codeshares, seat assignment, flight loads, checked baggage, fees, "
            "and rebooking. Note that cross-trained outstation agents may also work at the gate. "
            "Do not invent airline-specific rules or system commands."
        ),
    ),
    "boarding_documents": SpecialistDefinition(
        key="boarding_documents",
        label="Boarding & Documents",
        procedure_categories=["boarding_documents"],
        system_prompt=(
            "You are a boarding and travel-document specialist. Focus on gate procedures, "
            "documents, boarding order, and denied boarding policy references."
        ),
    ),
    "special_assistance": SpecialistDefinition(
        key="special_assistance",
        label="Special Assistance & Accommodations",
        procedure_categories=["special_assistance"],
        system_prompt=(
            "You are an accommodations specialist. Focus on accessibility, wheelchair support, "
            "service-animal handling, and compliance-oriented guidance."
        ),
    ),
    "irops": SpecialistDefinition(
        key="irops",
        label="Irregular Operations (IROPS)",
        procedure_categories=["irops"],
        system_prompt=(
            "You are an irregular operations specialist. Focus on delay/cancellation workflows, "
            "rebooking, and disruption handling."
        ),
    ),
    "safety_security": SpecialistDefinition(
        key="safety_security",
        label="Safety & Security",
        procedure_categories=["safety_security"],
        system_prompt=(
            "You are a safety and security specialist. Focus on gate security controls, "
            "safety procedures, and hazard awareness."
        ),
    ),
    "baggage_ramp": SpecialistDefinition(
        key="baggage_ramp",
        label="Baggage & Ramp Coordination",
        procedure_categories=["baggage_ramp"],
        system_prompt=(
            "You are a baggage and ramp coordination specialist. Focus on baggage handling, "
            "gate-check rules, and coordination with ramp teams."
        ),
    ),
}


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    source_dir = data_dir / "sources"
    chroma_dir = data_dir / "chroma"

    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        source_dir=source_dir,
        chroma_dir=chroma_dir,
        collection_name=os.getenv("CHROMA_COLLECTION", "gate_agent_docs"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        chat_model=os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b-instruct"),
        embedding_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        top_k=int(os.getenv("RETRIEVE_TOP_K", "5")),
        max_self_check_retries=int(os.getenv("SELF_CHECK_MAX_RETRIES", "1")),
        allow_multi_route=os.getenv("ALLOW_MULTI_ROUTE", "true").lower() == "true",
    )
