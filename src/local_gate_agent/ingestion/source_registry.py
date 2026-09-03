from __future__ import annotations

from pathlib import Path
from typing import Dict


FILE_METADATA_OVERRIDES: Dict[str, Dict[str, str]] = {
    "routine_at_gate.md": {
        "procedure_category": "gate_routine",
        "source_type": "internal",
        "confidentiality": "internal_use_only",
        "version": "1.0",
    },
    "routine_at_counter.md": {
        "procedure_category": "ticket_counter_routine",
        "source_type": "internal",
        "confidentiality": "internal_use_only",
        "version": "1.0",
    },
    "airport_operation_agent.pdf": {
        "procedure_category": "boarding_documents",
        "source_type": "internal",
        "confidentiality": "internal_use_only",
        "version": "2026-07",
    },
    "airport_codes.pdf": {
        "procedure_category": "boarding_documents",
        "source_type": "public_reference",
        "confidentiality": "internal_use_only",
        "version": "unknown",
    },
    "IATA_code_list.pdf": {
        "procedure_category": "boarding_documents",
        "source_type": "public_reference",
        "confidentiality": "internal_use_only",
        "version": "2021-07",
    },
    "aviation_abbreviations.pdf": {
        "procedure_category": "boarding_documents",
        "source_type": "public_reference",
        "confidentiality": "internal_use_only",
        "version": "unknown",
    },
    "aviation_alphabet.pdf": {
        "procedure_category": "boarding_documents",
        "source_type": "public_reference",
        "confidentiality": "internal_use_only",
        "version": "unknown",
    },
    "cabin_safety_compendium.pdf": {
        "procedure_category": "safety_security",
        "source_type": "internal",
        "confidentiality": "internal_use_only",
        "version": "unknown",
    },
    "EATC_ground_operations_manual_2022.pdf": {
        "procedure_category": "baggage_ramp",
        "source_type": "internal",
        "confidentiality": "internal_use_only",
        "version": "2022",
    },
}


def infer_metadata_for_source(path: Path) -> Dict[str, str]:
    filename = path.name
    base = {
        "source": filename,
        "procedure_category": "boarding_documents",
        "source_type": "internal",
        "confidentiality": "internal_use_only",
        "effective_date": "unknown",
        "version": "unknown",
        "station": "default",
        "airline": "default",
    }
    override = FILE_METADATA_OVERRIDES.get(filename, {})
    return {**base, **override}


def flightaware_metadata() -> Dict[str, str]:
    return {
        "procedure_category": "irops",
        "source_type": "public_web",
        "confidentiality": "public",
        "effective_date": "live",
        "version": "live",
        "station": "default",
        "airline": "default",
    }
