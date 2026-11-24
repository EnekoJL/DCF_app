"""Display-ready data for the widgets (all strings already formatted, in Spanish)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from sevcon_diff.application.value_decoder import format_number
from sevcon_diff.domain.diff_models import (
    ChangeKind,
    DecodedValue,
    DiffResult,
    FileSummary,
    ParameterChange,
)
from sevcon_diff.domain.models import ObjectKey
from sevcon_diff.domain.motor_profile import (
    LineStyle,
    MotorConstant,
    MotorProfile,
    TorqueSpeedCurve,
)
from sevcon_diff.presentation import strings_es as s

GROUP_ALL = "__all__"
SLOT_A = "A"
SLOT_B = "B"


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


# --- torque-speed chart --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChartSeries:
    """One torque-speed map of one file, with its theoretical power per point."""

    slot: str
    file_name: str
    curve_id: str
    curve_label: str
    style: LineStyle
    speeds: tuple[float, ...]
    torques: tuple[float, ...]
    powers_kw: tuple[float, ...]
    annotations: tuple[str, ...]  # "" where there is nothing worth labelling (0 kW)
    max_power_kw: float
    legend: str
    power_legend: str


@dataclass(frozen=True, slots=True)
class ChartReference:
    slot: str
    label: str
    torque_nm: float
    text: str


@dataclass(frozen=True, slots=True)
class ConstantRow:
    label: str
    key_label: str
    value_a: str
    value_b: str
    units: str
    changed: bool


@dataclass(frozen=True, slots=True)
class MotorChartViewModel:
    title: str
    slots: tuple[str, ...]  # files present, e.g. ("A", "B") or ("B",)
    series: tuple[ChartSeries, ...]
    references: tuple[ChartReference, ...] = ()
    constants: tuple[ConstantRow, ...] = ()
    file_names: Mapping[str, str] = field(default_factory=dict)

    @property
    def empty(self) -> bool:
        return not self.series


def format_kw(value: float) -> str:
    return f"{value:.1f} kW"


def _series(slot: str, profile: MotorProfile, curve: TorqueSpeedCurve) -> ChartSeries:
    powers = tuple(p.power_kw for p in curve.points)
    peak = max(powers, default=0.0)
    return ChartSeries(
        slot=slot,
        file_name=profile.display_name,
        curve_id=curve.id,
        curve_label=curve.label,
        style=curve.style,
        speeds=tuple(p.speed_rpm for p in curve.points),
        torques=tuple(p.torque_nm for p in curve.points),
        powers_kw=powers,
        annotations=tuple(format_kw(kw) if round(kw, 1) != 0 else "" for kw in powers),
        max_power_kw=peak,
        legend=s.CHART_LEGEND.format(
            slot=slot, file=profile.display_name, curve=curve.label, power=format_kw(peak)
        ),
        power_legend=s.CHART_POWER_LEGEND.format(slot=slot, curve=curve.label),
    )


def _constant_value(const: MotorConstant | None) -> str:
    if const is None or const.value is None:
        return s.MISSING_VALUE
    return const.value.display


def _constant_rows(
    profile_a: MotorProfile | None, profile_b: MotorProfile | None
) -> tuple[ConstantRow, ...]:
    by_slot = [
        {c.key: c for c in p.constants} if p is not None else {} for p in (profile_a, profile_b)
    ]
    ordered = [c for p in (profile_a, profile_b) if p is not None for c in p.constants]
    rows: list[ConstantRow] = []
    seen: set[ObjectKey] = set()
    for const in ordered:
        if const.key in seen:
            continue
        seen.add(const.key)
        a, b = (mapping.get(const.key) for mapping in by_slot)
        both = (
            a is not None and a.value is not None and b is not None and b.value is not None
        )
        value_a, value_b = _constant_value(a), _constant_value(b)
        rows.append(
            ConstantRow(
                label=const.label,
                key_label=const.key.label,
                value_a=value_a,
                value_b=value_b,
                units=(a.units if a is not None else "") or (b.units if b is not None else ""),
                changed=both and value_a != value_b,
            )
        )
    return tuple(rows)


def build_motor_chart(
    profile_a: MotorProfile | None, profile_b: MotorProfile | None
) -> MotorChartViewModel:
    """Overlay of the torque-speed maps of A and/or B plus the motor constants table."""
    present = [(slot, p) for slot, p in ((SLOT_A, profile_a), (SLOT_B, profile_b)) if p]
    if len(present) == 2:
        title = s.CHART_TITLE_TWO.format(a=present[0][1].display_name, b=present[1][1].display_name)
    elif present:
        title = s.CHART_TITLE_ONE.format(name=present[0][1].display_name)
    else:
        title = s.CHART_TITLE
    return MotorChartViewModel(
        title=title,
        slots=tuple(slot for slot, _ in present),
        series=tuple(_series(slot, p, c) for slot, p in present for c in p.curves),
        references=tuple(
            ChartReference(
                slot=slot,
                label=ref.label,
                torque_nm=ref.torque_nm,
                text=s.CHART_REFERENCE.format(
                    slot=slot, label=ref.label, value=format_number(ref.torque_nm)
                ),
            )
            for slot, p in present
            for ref in p.references
        ),
        constants=_constant_rows(profile_a, profile_b),
        file_names={slot: p.display_name for slot, p in present},
    )
