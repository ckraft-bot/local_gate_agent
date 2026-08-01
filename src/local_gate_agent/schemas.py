from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ChunkRecord:
    chunk_id: str
    text: str
    metadata: Dict[str, str]


@dataclass
class SpecialistOutput:
    specialist_key: str
    specialist_label: str
    finding: str
    source_ids: List[str]
