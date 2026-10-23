"""Flattened, already formatted data shared by the HTML and PDF exporters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sevcon_diff.domain.diff_models import ChangeKind, DiffResult, ParameterChange

MISSING = "(no existe)"
KIND_LABELS = {
    ChangeKind.MODIFIED: "Modificado",
    ChangeKind.ADDED: "Añadido",
    ChangeKind.REMOVED: "Eliminado",
}


@dataclass(frozen=True, slots=True)
class ReportRow:
    key: str
    name: str
    parent: str
    value_a: str
    value_b: str
    delta: str
    units: str
    kind: str
    kind_label: str
    description: str
    bits: tuple[str, ...]
    out_of_limits: bool
    is_noise: bool
    noise_reason: str


@dataclass(frozen=True, slots=True)
class ReportGroup:
    label: str
    motor_control: bool
    rows: tuple[ReportRow, ...]


def delta_text(change: ParameterChange) -> str:
    if not change.delta_display:
        return ""
    if change.delta_percent is None:
        return change.delta_display
    return f"{change.delta_display} ({change.delta_percent:+.1f} %)"


def to_row(change: ParameterChange) -> ReportRow:
    return ReportRow(
        key=change.key.label,
        name=change.name,
        parent=change.parent_name or "",
        value_a=change.old.display if change.old else MISSING,
        value_b=change.new.display if change.new else MISSING,
        delta=delta_text(change),
        units=change.units,
        kind=change.kind.value,
        kind_label=KIND_LABELS[change.kind],
        description=change.description,
        bits=tuple(f"{b.name}: {b.old_display} → {b.new_display}" for b in change.bit_changes),
        out_of_limits=change.out_of_limits,
        is_noise=change.is_noise,
        noise_reason=change.noise_reason or "",
    )


def build_groups(result: DiffResult) -> tuple[ReportGroup, ...]:
    return tuple(
        ReportGroup(g.label, g.motor_control, tuple(to_row(c) for c in changes))
        for g, changes in result.grouped()
    )


def generated_at() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")
