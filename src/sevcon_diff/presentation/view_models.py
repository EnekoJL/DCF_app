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
GROUP_MOTOR = "__motor__"


@dataclass(frozen=True, slots=True)
class ChangeRow:
    iid: str
    key: str
    name: str
    group: str
    value_a: str
    value_b: str
    delta: str
    units: str
    kind: str
    motor_control: bool
    is_noise: bool
    out_of_limits: bool
    sort_key: tuple[int, int]


@dataclass(frozen=True, slots=True)
class GroupItem:
    id: str
    label: str
    count: int
    motor_control: bool = False


@dataclass(frozen=True, slots=True)
class FileCaption:
    name: str
    details: str


@dataclass(frozen=True, slots=True)
class SummaryViewModel:
    relevant: str
    motor: str
    noise: str
    checksum: str
    checksum_differs: bool
    firmware: str
    firmware_mismatch: bool


@dataclass(frozen=True, slots=True)
class BitRow:
    name: str
    value_a: str
    value_b: str


@dataclass(frozen=True, slots=True)
class DetailViewModel:
    title: str
    subtitle: str
    motor_control: bool
    fields: tuple[tuple[str, str], ...]
    description: str
    bits: tuple[BitRow, ...]
    warnings: tuple[str, ...]


def _value(value: DecodedValue | None) -> str:
    return value.display if value is not None else s.MISSING_VALUE


def delta_text(change: ParameterChange) -> str:
    if not change.delta_display:
        return ""
    if change.delta_percent is None:
        return change.delta_display
    return f"{change.delta_display} ({change.delta_percent:+.1f} %)"


def to_row(change: ParameterChange) -> ChangeRow:
    name = change.full_name
    if change.kind is ChangeKind.ADDED:
        name = f"[{s.KIND_ADDED}] {name}"
    elif change.kind is ChangeKind.REMOVED:
        name = f"[{s.KIND_REMOVED}] {name}"
    return ChangeRow(
        iid=change.key.section,
        key=change.key.label,
        name=name,
        group=change.group.display_label,
        value_a=_value(change.old),
        value_b=_value(change.new),
        delta=delta_text(change),
        units=change.units,
        kind=change.kind.value,
        motor_control=change.is_motor_control,
        is_noise=change.is_noise,
        out_of_limits=change.out_of_limits,
        sort_key=change.key.sort_key,
    )


def to_rows(changes: Iterable[ParameterChange]) -> list[ChangeRow]:
    return [to_row(c) for c in changes]


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


def build_summary(result: DiffResult) -> SummaryViewModel:
    a, b = result.file_a, result.file_b
    summary = result.summary
    checksum_state = s.CHECKSUM_DIFFERS if result.checksum_differs else s.CHECKSUM_EQUAL
    firmware = (
        s.FIRMWARE_WARNING.format(a=a.revision_number, b=b.revision_number)
        if result.firmware_mismatch
        else s.FIRMWARE_OK.format(rev=a.revision_number or "—")
    )
    return SummaryViewModel(
        relevant=str(summary.relevant),
        motor=str(summary.motor_control),
        noise=str(summary.noise),
        checksum=f"{a.checksum or '—'} / {b.checksum or '—'} ({checksum_state})",
        checksum_differs=result.checksum_differs,
        firmware=firmware,
        firmware_mismatch=result.firmware_mismatch,
    )


def build_groups(result: DiffResult, visible: Iterable[ParameterChange]) -> list[GroupItem]:
    """Sidebar entries; counts reflect ``visible`` (changes passing all but the group filter)."""
    visible = list(visible)
    counts: dict[str, int] = {}
    for change in visible:
        counts[change.group.id] = counts.get(change.group.id, 0) + 1
    items = [
        GroupItem(GROUP_ALL, s.GROUP_ALL, len(visible)),
        GroupItem(
            GROUP_MOTOR, s.GROUP_MOTOR, sum(1 for c in visible if c.is_motor_control), True
        ),
    ]
    items.extend(
        GroupItem(g.id, g.display_label, counts.get(g.id, 0), g.motor_control)
        for g in result.groups
    )
    return items


def _limits(change: ParameterChange) -> str:
    if change.low_limit is None and change.high_limit is None:
        return "—"
    low = change.low_limit.display if change.low_limit else "—"
    high = change.high_limit.display if change.high_limit else "—"
    return f"[{low}, {high}] {change.units}".rstrip()


def build_detail(change: ParameterChange) -> DetailViewModel:
    units = f" {change.units}" if change.units else ""
    fields: list[tuple[str, str]] = [
        (s.DETAIL_GROUP, change.group.display_label),
        (s.DETAIL_KIND, s.KIND_LABELS.get(change.kind.value, change.kind.value)),
        (s.DETAIL_VALUE_A, _value(change.old) + (units if change.old else "")),
        (s.DETAIL_VALUE_B, _value(change.new) + (units if change.new else "")),
    ]
    if change.delta_display:
        fields.append((s.DETAIL_DELTA, delta_text(change) + units))
    fields += [
        (s.DETAIL_RAW_A, _raw(change.old)),
        (s.DETAIL_RAW_B, _raw(change.new)),
        (s.DETAIL_DATA_TYPE, f"{change.data_type_name} ({change.data_type})"),
        (s.DETAIL_ACCESS, change.access_type or "—"),
        (
            s.DETAIL_ACCESS_LEVEL,
            s.ACCESS_LEVELS.get(change.access_level, str(change.access_level))
            if change.access_level is not None
            else "—",
        ),
        (s.DETAIL_LIMITS, _limits(change)),
        (s.DETAIL_DEFAULT, (change.default.display + units) if change.default else "—"),
        (s.DETAIL_CATEGORY, change.category or "—"),
        (s.DETAIL_PREOP, s.YES if change.write_in_preop_only else s.NO),
        (s.DETAIL_NOISE, change.noise_reason or s.NO),
    ]
    warnings: list[str] = []
    low = change.low_limit.display if change.low_limit else "—"
    high = change.high_limit.display if change.high_limit else "—"
    if change.old_out_of_limits:
        warnings.append(s.WARN_OUT_OF_LIMITS.format(which="A", low=low, high=high))
    if change.new_out_of_limits:
        warnings.append(s.WARN_OUT_OF_LIMITS.format(which="B", low=low, high=high))
    if change.is_noise:
        warnings.append(s.WARN_NOISE.format(reason=change.noise_reason))
    return DetailViewModel(
        title=change.name,
        subtitle=" · ".join(p for p in (change.key.label, change.key.hex, change.parent_name) if p),
        motor_control=change.is_motor_control,
        fields=tuple(fields),
        description=change.description or s.DETAIL_NO_DESCRIPTION,
        bits=tuple(BitRow(b.name, b.old_display, b.new_display) for b in change.bit_changes),
        warnings=tuple(warnings),
    )


def _raw(value: DecodedValue | None) -> str:
    if value is None:
        return s.MISSING_VALUE
    if value.raw_hex:
        return value.raw_hex
    raw = (value.raw_text or "").strip()
    return raw if len(raw) <= 40 else f"{raw[:37]}…"
