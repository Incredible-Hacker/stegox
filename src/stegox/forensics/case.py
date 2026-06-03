"""Case management.

A case is a directory the analyst creates. StegoX does not maintain a
separate database; the case directory holds the manifest, evidence
copies, working files, and reports.
"""

from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from stegox.core.errors import ConfigError
from stegox.utils.hashing import hash_file

CASE_LAYOUT: tuple[str, ...] = (
    "inputs",
    "work",
    "reports",
    "logs",
)


@dataclass(slots=True)
class CaseFile:
    path: str
    sha256: str
    md5: str
    sha1: str
    size: int
    media_type: str
    format: str


@dataclass(slots=True)
class Case:
    root: Path
    manifest: dict[str, Any] = field(default_factory=dict)
    files: list[CaseFile] = field(default_factory=list)

    def save(self) -> None:
        manifest_path = self.root / "manifest.yaml"
        manifest_path.write_text(yaml.safe_dump(self.manifest, sort_keys=False), encoding="utf-8")
        files_path = self.root / "files.yaml"
        files_path.write_text(yaml.safe_dump([asdict(f) for f in self.files], sort_keys=False), encoding="utf-8")

    def add_file(self, source: Path) -> CaseFile:
        """Copy ``source`` into inputs/ and register it in the case."""
        if not source.exists():
            raise FileNotFoundError(source)
        dest = self.root / "inputs" / source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            raise FileExistsError(f"file already in case: {dest}")
        shutil.copy2(source, dest)
        hashes = hash_file(dest)
        cf = CaseFile(
            path=str(dest.relative_to(self.root)),
            sha256=hashes.sha256,
            md5=hashes.md5,
            sha1=hashes.sha1,
            size=hashes.size,
            media_type="",
            format="",
        )
        self.files.append(cf)
        return cf


def init_case(path: Path, *, operator: str, description: str = "") -> Case:
    """Initialize a new case at ``path``."""
    if (path / "manifest.yaml").exists():
        raise FileExistsError(f"case already exists at {path}")
    path.mkdir(parents=True, exist_ok=True)
    for sub in CASE_LAYOUT:
        (path / sub).mkdir(exist_ok=True)
    manifest = {
        "case": {
            "root": str(path),
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "operator": operator,
            "description": description,
            "stegox_version": "0.1.0",
        }
    }
    case = Case(root=path, manifest=manifest)
    case.save()
    return case


def load_case(path: Path) -> Case:
    """Load an existing case from ``path``."""
    manifest_path = path / "manifest.yaml"
    if not manifest_path.exists():
        raise ConfigError(f"no manifest at {manifest_path}")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    files_path = path / "files.yaml"
    files_data = yaml.safe_load(files_path.read_text(encoding="utf-8")) if files_path.exists() else []
    files = [CaseFile(**f) for f in (files_data or [])]
    return Case(root=path, manifest=manifest, files=files)


__all__ = ["CASE_LAYOUT", "Case", "CaseFile", "init_case", "load_case"]
