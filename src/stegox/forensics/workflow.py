"""Workflow helpers for common DFIR tasks."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from stegox.forensics.case import Case, init_case
from stegox.forensics.chain_of_custody import ChainOfCustody
from stegox.forensics.hashing import evidence_hash
from stegox.utils.hashing import FileHashes


@dataclass(slots=True)
class AcquisitionPlan:
    """Describes how to acquire an evidence file into a case."""

    source: Path
    case_root: Path
    operator: str
    description: str = ""


def run_acquisition(plan: AcquisitionPlan) -> tuple[Case, FileHashes, Path]:
    """Acquire ``plan.source`` into a new case and return case + hashes + dest."""
    case = init_case(plan.case_root, operator=plan.operator, description=plan.description)
    dest = case.root / "inputs" / plan.source.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan.source, dest)
    hashes = evidence_hash(dest)
    custody = ChainOfCustody(case.root / "logs" / "custody.jsonl")
    custody.append(
        ChainOfCustody.now_event(
            operator=plan.operator,
            action="acquire",
            target=str(dest.relative_to(case.root)),
            sha256=hashes.sha256,
            args={"description": plan.description, "size": hashes.size},
        )
    )
    case.add_file(plan.source)
    return case, hashes, dest


__all__ = ["AcquisitionPlan", "run_acquisition"]
