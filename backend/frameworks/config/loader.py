"""Framework configuration loader.

Discovers, parses, validates and normalises control-library files. Supports
both ``.json`` and ``.yaml``/``.yml`` so frameworks can be authored in whichever
format an organisation prefers (spec: "Future frameworks must require only
JSON/YAML additions").

The loader is pure and deterministic: given the same files it always yields the
same normalised structures and the same ``config_hash``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml
from django.conf import settings

from common.exceptions import ConfigValidationError
from common.hashing import sha256_of_obj

from .schema import validate_config

# Files beginning with these prefixes are ignored (e.g. ``_schema.json``).
_IGNORE_PREFIXES = ("_", ".")
_SUPPORTED_SUFFIXES = (".json", ".yaml", ".yml")


@dataclass(frozen=True)
class NormalizedRequirement:
    identifier: str
    title: str
    description: str
    control: str
    weight: int
    category: str
    risk_domain: str
    control_group: str
    control_group_title: str
    evidence_expectations: list[str]
    pass_criteria: str
    partial_criteria: str
    fail_criteria: str
    references: list[str]
    order: int


@dataclass(frozen=True)
class NormalizedFramework:
    id: str
    name: str
    version: str
    publisher: str
    category: str
    description: str
    source_url: str
    scoring_config: dict
    raw_config: dict
    config_hash: str
    control_count: int
    requirements: list[NormalizedRequirement] = field(default_factory=list)

    @property
    def requirement_count(self) -> int:
        return len(self.requirements)


def _read_file(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(
                {"source": str(path), "errors": [{"location": "(file)", "message": f"Invalid JSON: {exc}"}]}
            ) from exc
    # YAML (also parses JSON).
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigValidationError(
            {"source": str(path), "errors": [{"location": "(file)", "message": f"Invalid YAML: {exc}"}]}
        ) from exc


def normalize(config: dict, *, source: str = "<config>") -> NormalizedFramework:
    """Validate a raw config dict and flatten it into a NormalizedFramework.

    Flattening assigns each requirement a stable ``order`` (document order) and
    records the parent control group, so the DB projection is a faithful,
    ordered mirror of the config.
    """
    validate_config(config, source=source)
    fw = config["framework"]

    requirements: list[NormalizedRequirement] = []
    seen_ids: set[str] = set()
    order = 0
    for control in fw["controls"]:
        for req in control["requirements"]:
            ident = req["identifier"]
            if ident in seen_ids:
                raise ConfigValidationError(
                    {
                        "source": source,
                        "errors": [
                            {
                                "location": f"controls/{control['id']}",
                                "message": f"Duplicate requirement identifier '{ident}'.",
                            }
                        ],
                    }
                )
            seen_ids.add(ident)
            requirements.append(
                NormalizedRequirement(
                    identifier=ident,
                    title=req["title"],
                    description=req["description"],
                    control=req["control"],
                    weight=int(req["weight"]),
                    category=req["category"],
                    risk_domain=req.get("risk_domain", ""),
                    control_group=control["id"],
                    control_group_title=control["title"],
                    evidence_expectations=list(req["evidence_expectations"]),
                    pass_criteria=req["pass_criteria"],
                    partial_criteria=req["partial_criteria"],
                    fail_criteria=req["fail_criteria"],
                    references=list(req["references"]),
                    order=order,
                )
            )
            order += 1

    return NormalizedFramework(
        id=fw["id"],
        name=fw["name"],
        version=fw.get("version", ""),
        publisher=fw.get("publisher", ""),
        category=fw.get("category", ""),
        description=fw.get("description", ""),
        source_url=fw.get("source_url", ""),
        scoring_config=fw["scoring"],
        raw_config=config,
        config_hash=sha256_of_obj(config),
        control_count=len(fw["controls"]),
        requirements=requirements,
    )


def load_file(path: str | Path) -> NormalizedFramework:
    """Load + normalise a single config file."""
    path = Path(path)
    return normalize(_read_file(path), source=str(path))


def config_dir() -> Path:
    return Path(settings.GOVERNANCE["FRAMEWORKS_DATA_DIR"])


def iter_config_paths(directory: str | Path | None = None) -> list[Path]:
    """Return the sorted list of framework config files in ``directory``."""
    base = Path(directory) if directory else config_dir()
    if not base.exists():
        return []
    paths = [
        p
        for p in base.iterdir()
        if p.is_file()
        and p.suffix.lower() in _SUPPORTED_SUFFIXES
        and not p.name.startswith(_IGNORE_PREFIXES)
    ]
    return sorted(paths, key=lambda p: p.name)


def load_all(directory: str | Path | None = None) -> Iterator[NormalizedFramework]:
    """Yield every valid, normalised framework config in ``directory``."""
    for path in iter_config_paths(directory):
        yield load_file(path)
