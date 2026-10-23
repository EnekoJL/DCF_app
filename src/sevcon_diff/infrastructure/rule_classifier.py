"""Group classification and noise detection driven by the TOML files in ``knowledge/``."""

from __future__ import annotations

import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib import resources
from typing import Any, Generic, TypeVar

from sevcon_diff.domain.groups import FunctionalGroup
from sevcon_diff.domain.models import DcfParameter, ObjectKey

KNOWLEDGE_PACKAGE = "sevcon_diff.infrastructure"
KNOWLEDGE_DIR = "knowledge"
GROUPS_FILE = "parameter_groups.toml"
NOISE_FILE = "noise_rules.toml"

# Specificity ranks: index+subs > index > range.
_SPEC_SUBS = 3
_SPEC_INDEX = 2
_SPEC_RANGE = 1

T = TypeVar("T")


class RuleError(ValueError):
    """Malformed rule in a knowledge TOML file."""


def load_knowledge(file_name: str) -> dict[str, Any]:
    """Load a TOML from the packaged knowledge directory (works when installed)."""
    resource = resources.files(KNOWLEDGE_PACKAGE).joinpath(KNOWLEDGE_DIR).joinpath(file_name)
    text = resource.read_text(encoding="utf-8")
    return tomllib.loads(text)


def _hex(value: object) -> int:
    try:
        return int(str(value).strip().lower().removeprefix("0x"), 16)
    except ValueError as exc:
        raise RuleError(f"invalid hex value: {value!r}") from exc


def _hex_range(text: str) -> tuple[int, int]:
    if "-" in text:
        low, high = text.split("-", 1)
        return _hex(low), _hex(high)
    value = _hex(text)
    return value, value


@dataclass(frozen=True, slots=True)
class Rule:
    """``{index, subs?}`` or ``{range}`` rule. Ranges are inclusive, everything hex."""

    specificity: int
    index_low: int
    index_high: int
    sub_ranges: tuple[tuple[int, int], ...] = ()

    @classmethod
    def from_toml(cls, raw: Mapping[str, Any]) -> Rule:
        if "range" in raw:
            bounds = raw["range"]
            if not isinstance(bounds, list) or len(bounds) != 2:
                raise RuleError(f"range must be [low, high]: {raw!r}")
            return cls(_SPEC_RANGE, _hex(bounds[0]), _hex(bounds[1]))
        if "index" not in raw:
            raise RuleError(f"rule needs 'index' or 'range': {raw!r}")
        index = _hex(raw["index"])
        subs = raw.get("subs")
        if subs:
            ranges = tuple(_hex_range(str(s)) for s in subs)
            return cls(_SPEC_SUBS, index, index, ranges)
        return cls(_SPEC_INDEX, index, index)

    def matches(self, key: ObjectKey) -> bool:
        if not self.index_low <= key.index <= self.index_high:
            return False
        if not self.sub_ranges:
            return True
        return key.sub is not None and any(lo <= key.sub <= hi for lo, hi in self.sub_ranges)


class _RuleSet(Generic[T]):
    """Ordered (rule, payload) pairs resolved by specificity, ties by file order."""

    def __init__(self, entries: Iterable[tuple[Rule, T]]) -> None:
        self._entries = list(entries)

    def resolve(self, key: ObjectKey) -> T | None:
        best: tuple[Rule, T] | None = None
        for rule, payload in self._entries:
            if rule.matches(key) and (best is None or rule.specificity > best[0].specificity):
                best = (rule, payload)
        return best[1] if best is not None else None


class TomlRuleClassifier:
    """Implements ``ParameterClassifier`` from ``parameter_groups.toml``."""

    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        data = data if data is not None else load_knowledge(GROUPS_FILE)
        groups: list[FunctionalGroup] = []
        entries: list[tuple[Rule, FunctionalGroup]] = []
        for raw in data.get("group", []):
            group = FunctionalGroup(
                id=str(raw["id"]),
                label=str(raw.get("label", raw["id"])),
                motor_control=bool(raw.get("motor_control", False)),
                order=int(raw.get("order", 999)),
            )
            groups.append(group)
            entries.extend((Rule.from_toml(r), group) for r in raw.get("rules", []))
        by_id = {g.id: g for g in groups}
        fallback_id = str(data.get("fallback", "other"))
        self._fallback = by_id.get(fallback_id) or FunctionalGroup(fallback_id, fallback_id)
        if fallback_id not in by_id:
            groups.append(self._fallback)
        self._groups = tuple(sorted(groups, key=lambda g: (not g.motor_control, g.order)))
        self._rules = _RuleSet(entries)

    def classify(self, param: DcfParameter) -> FunctionalGroup:
        return self.classify_key(param.key)

    def classify_key(self, key: ObjectKey) -> FunctionalGroup:
        return self._rules.resolve(key) or self._fallback

    def groups(self) -> tuple[FunctionalGroup, ...]:
        return self._groups


class TomlNoiseFilter:
    """Implements ``NoiseFilter`` from ``noise_rules.toml``. ``[[keep]]`` always wins."""

    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        data = data if data is not None else load_knowledge(NOISE_FILE)
        self._categories = frozenset(str(c).upper() for c in data.get("categories", []))
        self._access_types = frozenset(str(a).lower() for a in data.get("access_types", []))
        self._noise = _RuleSet(self._entries(data.get("noise", [])))
        self._keep = _RuleSet(self._entries(data.get("keep", [])))
        checksum = data.get("indicators", {}).get("checksum")
        self._checksum = ObjectKey.parse(str(checksum)) if checksum else None

    @staticmethod
    def _entries(blocks: Iterable[Mapping[str, Any]]) -> list[tuple[Rule, str]]:
        return [
            (Rule.from_toml(rule), str(block.get("reason", "")))
            for block in blocks
            for rule in block.get("rules", [])
        ]

    @property
    def checksum_key(self) -> ObjectKey | None:
        return self._checksum

    def noise_reason(self, param: DcfParameter) -> str | None:
        if self._keep.resolve(param.key) is not None:
            return None
        explicit = self._noise.resolve(param.key)
        if explicit is not None:
            return explicit
        category = param.metadata.category.upper()
        if category in self._categories:
            return f"CATEGORY={category}"
        if param.access_type.lower() in self._access_types:
            return f"AccessType={param.access_type}"
        return None
