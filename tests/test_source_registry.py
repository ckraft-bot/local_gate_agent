from pathlib import Path

from local_gate_agent.config import SPECIALISTS
from local_gate_agent.ingestion.source_registry import infer_metadata_for_source


def test_known_file_metadata_override():
    meta = infer_metadata_for_source(Path("cabin_safety_compendium.pdf"))
    assert meta["procedure_category"] == "safety_security"
    assert meta["source_type"] == "internal"


def test_default_metadata_for_unknown_file():
    meta = infer_metadata_for_source(Path("unknown.pdf"))
    assert meta["procedure_category"] == "boarding_documents"
    assert meta["confidentiality"] == "internal_use_only"


def test_routine_sources_have_dedicated_metadata_and_specialists():
    gate_metadata = infer_metadata_for_source(Path("routine_at_gate.md"))
    counter_metadata = infer_metadata_for_source(Path("routine_at_counter.md"))

    assert gate_metadata["procedure_category"] == "gate_routine"
    assert counter_metadata["procedure_category"] == "ticket_counter_routine"
    assert SPECIALISTS["routine_at_gate"].source_names == ["routine_at_gate.md"]
    assert SPECIALISTS["routine_at_counter"].source_names == ["routine_at_counter.md"]
