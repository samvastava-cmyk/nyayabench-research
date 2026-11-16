"""Loading and querying the hetvābhāsa taxonomy.

The taxonomy JSON is the scholarly artifact: 13 categories, each carrying its
Sanskrit term, IAST transliteration, source citation, verbatim source quote,
and an explicit confidence basis (VERIFIED vs INFERRED). It is released in
full under CC-BY-4.0 because it is the part of this project that is meant to
be reused and cited.

What is *not* here is the calibrated judge prompt — the exemplar set and
conditional rules that turn these definitions into a working classifier.
See prompts/README.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

from .schemas import RFCode

_DEFAULT_TAXONOMY = Path(__file__).resolve().parents[2] / "taxonomy" / "hetvabhasa_v2.2.json"


@dataclass(frozen=True)
class Category:
    """One hetvābhāsa category."""

    id: str
    parent: str
    sanskrit: str
    iast: str
    english: str
    source_text: str
    source_quote_sanskrit: str
    source_quote_english: str
    source_verification: str
    confidence: str
    confidence_basis: str
    definitions: dict[str, str]
    raw: dict[str, Any]

    @property
    def is_verified(self) -> bool:
        """True only when the category is verbatim-attested in a primary source.

        Categories whose basis mentions INFERRED are extensions we made, not
        readings of the Tarka-Saṃgraha. The paper says so; so does this.
        """
        status = self.raw.get("textual_status")
        if status is not None:  # v2.2+: explicit status, verified = defined in the root text
            return status == "VERIFIED_ROOT_TEXT"
        return "INFERRED" not in (self.confidence_basis or "").upper()

    @property
    def short_definition(self) -> str:
        return self.definitions.get("intuitive") or self.definitions.get("formal", "")


class Taxonomy:
    """An immutable view over a taxonomy JSON document."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._categories: dict[str, Category] = {}
        for c in data.get("categories", []):
            cat = Category(
                id=c["id"],
                parent=c.get("parent", ""),
                sanskrit=c.get("sanskrit", ""),
                iast=c.get("iast", ""),
                english=c.get("english", ""),
                source_text=c.get("source_text", ""),
                source_quote_sanskrit=c.get("source_passage_verbatim") or c.get("source_quote_sanskrit", "") or "",
                source_quote_english=c.get("source_quote_english", ""),
                source_verification=c.get("source_verification", ""),
                confidence=c.get("confidence", ""),
                confidence_basis=c.get("confidence_basis", ""),
                definitions=c.get("definitions", {}) or {},
                raw=c,
            )
            self._categories[cat.id] = cat

    # -- construction ------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Taxonomy":
        p = Path(path) if path else _DEFAULT_TAXONOMY
        if not p.exists():
            raise FileNotFoundError(f"taxonomy not found at {p}")
        return cls(json.loads(p.read_text(encoding="utf-8")))

    # -- metadata ----------------------------------------------------------

    @property
    def version(self) -> str:
        return str(self._data.get("schema_version", "unknown"))

    @property
    def primary_sources(self) -> list[dict[str, Any]]:
        return list(self._data.get("primary_sources", []))

    @property
    def parent_categories(self) -> list[dict[str, Any]]:
        return list(self._data.get("parent_categories", []))

    # -- access ------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._categories)

    def __iter__(self) -> Iterator[Category]:
        return iter(self._categories.values())

    def __getitem__(self, rf_id: str | RFCode) -> Category:
        key = rf_id.value if isinstance(rf_id, RFCode) else rf_id
        return self._categories[key]

    def get(self, rf_id: str | RFCode) -> Category | None:
        key = rf_id.value if isinstance(rf_id, RFCode) else rf_id
        return self._categories.get(key)

    @property
    def ids(self) -> list[str]:
        return list(self._categories)

    def verified(self) -> list[Category]:
        return [c for c in self._categories.values() if c.is_verified]

    def inferred(self) -> list[Category]:
        return [c for c in self._categories.values() if not c.is_verified]

    # -- rendering ---------------------------------------------------------

    def definition_block(self, ids: list[str] | None = None) -> str:
        """A compact definition list suitable for inclusion in any prompt.

        This is the *public* rendering: definitions only. It is deliberately
        not the calibrated block used by the production profile.
        """
        chosen = ids or self.ids
        lines = []
        for i in chosen:
            c = self._categories.get(i)
            if c is None:
                continue
            lines.append(f"{c.id} — {c.english}: {c.short_definition}")
        return "\n".join(lines)

    def validate(self) -> list[str]:
        """Structural self-check. Returns a list of problems; empty is good."""
        problems: list[str] = []
        declared = self._data.get("total_categories")
        if declared is not None and declared != len(self._categories):
            problems.append(
                f"total_categories says {declared} but {len(self._categories)} are present"
            )
        parents = {p["id"] for p in self.parent_categories}
        # "Extended" is a documented pseudo-parent for the three categories
        # that reach beyond the classical five-fold division (RF-09, RF-10,
        # RF-11). It is described in `extended_categories_note` but has no
        # object in `parent_categories` — a schema gap slated for v2.2.
        if self._data.get("extended_categories_note"):
            parents.add("Extended")
        for c in self._categories.values():
            if c.parent and c.parent not in parents:
                problems.append(f"{c.id}: parent {c.parent!r} not in parent_categories")
            if not c.source_text:
                problems.append(f"{c.id}: no source_text")
            if not c.definitions:
                problems.append(f"{c.id}: no definitions block")
            if c.is_verified and not c.source_quote_english:
                problems.append(f"{c.id}: marked VERIFIED but carries no source quote")
        for p in self.parent_categories:
            for child in p.get("children", []):
                if child not in self._categories:
                    problems.append(f"parent {p['id']}: child {child} not defined")
        return problems


@lru_cache(maxsize=4)
def load_taxonomy(path: str | None = None) -> Taxonomy:
    """Cached loader for the default taxonomy."""
    return Taxonomy.load(path)
