"""Query applied to an existing DiffResult (no re-computation of the diff)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sevcon_diff.domain.diff_models import DiffResult, ParameterChange


@dataclass(frozen=True, slots=True)
class DiffQuery:
    """View filter. ``group_ids`` None means every group."""

    text: str = ""
    group_ids: frozenset[str] | None = None
    show_noise: bool = False
    motor_only: bool = False

    def matches(self, change: ParameterChange) -> bool:
        if change.is_noise and not self.show_noise:
            return False
        if self.motor_only and not change.is_motor_control:
            return False
        if self.group_ids is not None and change.group.id not in self.group_ids:
            return False
        return self._matches_text(change)

    def _matches_text(self, change: ParameterChange) -> bool:
        needle = self.text.strip().lower()
        if not needle:
            return True
        haystack = " ".join(
            (
                change.key.section,
                change.key.label,
                change.key.hex,
                change.name,
                change.parent_name or "",
                change.description,
                change.group.label,
            )
        ).lower()
        return all(term in haystack for term in needle.split())

    def apply(self, changes: Iterable[ParameterChange]) -> tuple[ParameterChange, ...]:
        return tuple(c for c in changes if self.matches(c))

    def apply_to(self, result: DiffResult) -> DiffResult:
        return result.with_changes(self.apply(result.changes))
