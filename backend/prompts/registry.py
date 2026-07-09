"""File-based prompt registry.

Prompts are treated as configuration, not code: each lives as a ``.txt`` file
under ``prompts/templates/`` and is versioned in git. This module discovers,
caches and renders them. Placeholders use ``$name`` / ``${name}`` syntax
(:class:`string.Template`) so JSON braces in a template are never mistaken for
substitution tokens — important because our auditor prompts embed a strict JSON
schema (Rule 3).

Fully implemented in Phase 1; the LLM invocation that consumes these prompts
lands in Phase 3.
"""
from __future__ import annotations

from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_SUFFIXES = (".txt", ".md", ".prompt")


class MissingPromptError(KeyError):
    pass


class PromptTemplate:
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text
        self._template = Template(text)

    def render(self, **context) -> str:
        """Render with ``$placeholder`` substitution. Unknown placeholders are
        left intact (safe_substitute) so a partially-populated prompt never
        raises mid-pipeline."""
        return self._template.safe_substitute(**context)

    def placeholders(self) -> set[str]:
        import re

        pattern = re.compile(r"\$\{?(\w+)\}?")
        return set(pattern.findall(self.text))


class PromptRegistry:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or TEMPLATES_DIR
        self._cache: dict[str, PromptTemplate] | None = None

    def _load(self) -> dict[str, PromptTemplate]:
        if self._cache is not None:
            return self._cache
        templates: dict[str, PromptTemplate] = {}
        if self.directory.exists():
            for path in sorted(self.directory.iterdir()):
                if path.is_file() and path.suffix.lower() in _SUFFIXES:
                    templates[path.stem] = PromptTemplate(
                        path.stem, path.read_text(encoding="utf-8")
                    )
        self._cache = templates
        return templates

    def names(self) -> list[str]:
        return sorted(self._load().keys())

    def get(self, name: str) -> PromptTemplate:
        templates = self._load()
        if name not in templates:
            raise MissingPromptError(
                f"Prompt '{name}' not found. Available: {', '.join(self.names()) or '(none)'}"
            )
        return templates[name]

    def render(self, name: str, **context) -> str:
        return self.get(name).render(**context)

    def reload(self) -> None:
        self._cache = None


# Module-level singleton used across the platform.
registry = PromptRegistry()
