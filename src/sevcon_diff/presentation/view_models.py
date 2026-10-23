"""Display-ready data for the widgets (all strings already formatted, in Spanish)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sevcon_diff.domain.diff_models import (
    ChangeKind,
    DecodedValue,
    DiffResult,
    FileSummary,
    ParameterChange,
)
from sevcon_diff.presentation import strings_es as s

GROUP_ALL = "__all__"


@dataclass(frozen=True, slots=True)
class BitRow:
    name: str
    value_a: str
    value_b: str


@dataclass(frozen=True, slots=True)
class ChangeRow:
    iid: str
    name: str
    value_a: str
    value_b: str
    trend: str
    units: str
    kind: str
    out_of_limits: bool
    bits: tuple[BitRow, ...] = ()


@dataclass(frozen=True, slots=True)
class GroupSection:
    id: str
    label: str
    rows: tuple[ChangeRow, ...]


@dataclass(frozen=True, slots=True)
class GroupOption:
    id: str
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class FileCaption:
    name: str
    details: str


@dataclass(frozen=True, slots=True)
class SummaryViewModel:
    headline: str
    scope: str
    firmware: str
    firmware_mismatch: bool
    other_count: int


def _value(value: DecodedValue | None) -> str:
    return value.display if value is not None else s.MISSING_VALUE


def _trend(change: ParameterChange) -> str:
    if change.kind is ChangeKind.MODIFIED and change.delta:
        return s.TREND_UP if change.delta > 0 else s.TREND_DOWN
    return s.TREND_CHANGED


def to_row(change: ParameterChange) -> ChangeRow:
    name = change.full_name
    if change.kind is ChangeKind.ADDED:
        name = f"{name}  ({s.KIND_ADDED})"
    elif change.kind is ChangeKind.REMOVED:
        name = f"{name}  ({s.KIND_REMOVED})"
    if change.out_of_limits:
        name = f"{s.OUT_OF_LIMITS} {name}"
    return ChangeRow(
        iid=change.key.section,
        name=name,
        value_a=_value(change.old),
        value_b=_value(change.new),
        trend=_trend(change),
        units=change.units,
        kind=change.kind.value,
        out_of_limits=change.out_of_limits,
        bits=tuple(BitRow(b.name, b.old_display, b.new_display) for b in change.bit_changes),
    )


def build_sections(result: DiffResult) -> list[GroupSection]:
    """Table content: one section per group with changes, focus areas first."""
    return [
        GroupSection(group.id, group.label, tuple(to_row(c) for c in changes))
        for group, changes in result.grouped()
    ]


def build_group_options(
    result: DiffResult, scope: Iterable[ParameterChange]
) -> list[GroupOption]:
    """Area filter entries: only groups that actually have changes in ``scope``."""
    scope = list(scope)
    options = [GroupOption(GROUP_ALL, s.GROUP_ALL, len(scope))]
    options.extend(
        GroupOption(group.id, group.label, len(changes))
        for group, changes in result.with_changes(tuple(scope)).grouped()
    )
    return options


def file_caption(info: FileSummary | None) -> FileCaption:
    if info is None:
        return FileCaption(s.FILE_NONE, "")
    details = " · ".join(
        part
        for part in (
            f"{info.modification_date} {info.modification_time}".strip(),
            info.revision_number and f"FW {info.revision_number}",
        )
        if part
    )
    return FileCaption(info.display_name, details)


def _headline(count: int) -> str:
    if count == 0:
        return s.HEADLINE_NONE
    return s.HEADLINE_ONE if count == 1 else s.HEADLINE.format(count=count)


def build_summary(result: DiffResult, in_scope: int, include_other: bool) -> SummaryViewModel:
    a, b = result.file_a, result.file_b
    firmware = (
        s.FIRMWARE_WARNING.format(a=a.revision_number, b=b.revision_number)
        if result.firmware_mismatch
        else s.FIRMWARE_OK.format(rev=a.revision_number or "—")
    )
    return SummaryViewModel(
        headline=_headline(in_scope),
        scope=s.HEADLINE_SCOPE_ALL if include_other else s.HEADLINE_SCOPE_FOCUS,
        firmware=firmware,
        firmware_mismatch=result.firmware_mismatch,
        other_count=sum(
            1 for c in result.changes if not c.is_noise and not c.is_motor_control
        ),
    )


def build_hint(change: ParameterChange) -> str:
    parts = [change.key.label, change.description.strip() or change.full_name]
    if change.out_of_limits:
        low = change.low_limit.display if change.low_limit else "—"
        high = change.high_limit.display if change.high_limit else "—"
        parts.append(s.HINT_OUT_OF_LIMITS.format(low=low, high=high))
    return "  ·  ".join(parts)
