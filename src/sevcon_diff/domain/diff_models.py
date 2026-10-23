"""Result model of comparing two DCF documents."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any

from sevcon_diff.domain.groups import FunctionalGroup
from sevcon_diff.domain.models import NAME_SEPARATOR, DcfDocument, ObjectKey


class ChangeKind(StrEnum):
    MODIFIED = "modified"
    ADDED = "added"
    REMOVED = "removed"


class ValueKind(StrEnum):
    EMPTY = "empty"
    INTEGER = "integer"
    STRING = "string"
    DOMAIN = "domain"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class DecodedValue:
    """A DCF value decoded to raw integer / physical value / label."""

    kind: ValueKind
    raw_text: str | None
    display: str
    raw_hex: str | None = None
    integer: int | None = None
    physical: float | None = None
    text: str | None = None
    enum_label: str | None = None
    blob_size: int | None = None
    blob_hash: str | None = None

    @property
    def identity(self) -> tuple[object, ...]:
        """What makes two values equal (independent of hex padding or case)."""
        if self.kind is ValueKind.INTEGER:
            return (self.kind, self.integer)
        if self.kind is ValueKind.STRING:
            return (self.kind, self.text)
        if self.kind is ValueKind.DOMAIN:
            return (self.kind, self.blob_hash, self.blob_size)
        if self.kind is ValueKind.EMPTY:
            return (self.kind,)
        return (self.kind, (self.raw_text or "").strip().lower())

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "raw": self.raw_text,
            "raw_hex": self.raw_hex,
            "integer": self.integer,
            "physical": self.physical,
            "text": self.text,
            "enum_label": self.enum_label,
            "blob_size": self.blob_size,
            "blob_hash": self.blob_hash,
            "display": self.display,
        }


@dataclass(frozen=True, slots=True)
class BitFieldChange:
    """A BIT_SPLIT field whose value differs between A and B."""

    name: str
    mask: int
    old_value: int | None
    new_value: int | None
    old_label: str | None = None
    new_label: str | None = None
    units: str = ""
    hex_format: bool = False

    @property
    def old_display(self) -> str:
        return _field_display(self.old_value, self.old_label, self.hex_format)

    @property
    def new_display(self) -> str:
        return _field_display(self.new_value, self.new_label, self.hex_format)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mask": f"0x{self.mask:X}",
            "old": self.old_value,
            "new": self.new_value,
            "old_label": self.old_label,
            "new_label": self.new_label,
            "units": self.units,
        }


def _field_display(value: int | None, label: str | None, hex_format: bool) -> str:
    if value is None:
        return "—"
    text = f"0x{value:X}" if hex_format else str(value)
    return f"{label} ({text})" if label else text


@dataclass(frozen=True, slots=True)
class ParameterChange:
    """One parameter that differs between file A (base) and file B (new)."""

    key: ObjectKey
    kind: ChangeKind
    name: str
    parent_name: str | None
    group: FunctionalGroup
    old: DecodedValue | None
    new: DecodedValue | None
    units: str = ""
    is_noise: bool = False
    noise_reason: str | None = None
    delta: float | None = None
    delta_percent: float | None = None
    delta_display: str = ""
    bit_changes: tuple[BitFieldChange, ...] = ()
    description: str = ""
    category: str = ""
    data_type: int | None = None
    data_type_name: str = ""
    access_type: str = ""
    access_level: int | None = None
    write_in_preop_only: bool = False
    low_limit: DecodedValue | None = None
    high_limit: DecodedValue | None = None
    default: DecodedValue | None = None
    old_out_of_limits: bool = False
    new_out_of_limits: bool = False

    @property
    def full_name(self) -> str:
        return f"{self.parent_name}{NAME_SEPARATOR}{self.name}" if self.parent_name else self.name

    @property
    def is_motor_control(self) -> bool:
        return self.group.motor_control

    @property
    def out_of_limits(self) -> bool:
        return self.old_out_of_limits or self.new_out_of_limits

    def to_dict(self) -> dict[str, Any]:
        def dv(value: DecodedValue | None) -> dict[str, Any] | None:
            return value.to_dict() if value is not None else None

        return {
            "key": self.key.section,
            "key_hex": self.key.hex,
            "kind": self.kind.value,
            "name": self.name,
            "parent_name": self.parent_name,
            "group": {
                "id": self.group.id,
                "label": self.group.label,
                "motor_control": self.group.motor_control,
            },
            "is_noise": self.is_noise,
            "noise_reason": self.noise_reason,
            "old": dv(self.old),
            "new": dv(self.new),
            "units": self.units,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
            "bit_changes": [b.to_dict() for b in self.bit_changes],
            "description": self.description,
            "category": self.category,
            "data_type": self.data_type,
            "data_type_name": self.data_type_name,
            "access_type": self.access_type,
            "access_level": self.access_level,
            "write_in_preop_only": self.write_in_preop_only,
            "low_limit": dv(self.low_limit),
            "high_limit": dv(self.high_limit),
            "default": dv(self.default),
            "old_out_of_limits": self.old_out_of_limits,
            "new_out_of_limits": self.new_out_of_limits,
        }


@dataclass(frozen=True, slots=True)
class FileSummary:
    """Header information of one compared file."""

    path: str
    original_file_name: str
    modification_date: str
    modification_time: str
    product_number: str
    revision_number: str
    parameter_count: int
    checksum: str | None = None

    @classmethod
    def from_document(cls, doc: DcfDocument, checksum: str | None) -> FileSummary:
        return cls(
            path=doc.source,
            original_file_name=doc.file_name,
            modification_date=doc.modification_date,
            modification_time=doc.modification_time,
            product_number=doc.product_number,
            revision_number=doc.revision_number,
            parameter_count=len(doc.parameters),
            checksum=checksum,
        )

    @property
    def display_name(self) -> str:
        return self.path.replace("\\", "/").rsplit("/", 1)[-1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "original_file_name": self.original_file_name,
            "modification_date": self.modification_date,
            "modification_time": self.modification_time,
            "product_number": self.product_number,
            "revision_number": self.revision_number,
            "parameter_count": self.parameter_count,
            "checksum": self.checksum,
        }


@dataclass(frozen=True, slots=True)
class DiffSummary:
    total: int
    relevant: int
    motor_control: int
    noise: int
    modified: int
    added: int
    removed: int
    by_group: Mapping[str, int] = field(default_factory=dict)

    @classmethod
    def from_changes(cls, changes: tuple[ParameterChange, ...]) -> DiffSummary:
        relevant = [c for c in changes if not c.is_noise]
        by_group: dict[str, int] = {}
        for change in relevant:
            by_group[change.group.id] = by_group.get(change.group.id, 0) + 1
        return cls(
            total=len(changes),
            relevant=len(relevant),
            motor_control=sum(1 for c in relevant if c.is_motor_control),
            noise=len(changes) - len(relevant),
            modified=sum(1 for c in relevant if c.kind is ChangeKind.MODIFIED),
            added=sum(1 for c in relevant if c.kind is ChangeKind.ADDED),
            removed=sum(1 for c in relevant if c.kind is ChangeKind.REMOVED),
            by_group=by_group,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "relevant": self.relevant,
            "motor_control": self.motor_control,
            "noise": self.noise,
            "modified": self.modified,
            "added": self.added,
            "removed": self.removed,
            "by_group": dict(self.by_group),
        }


@dataclass(frozen=True, slots=True)
class DiffResult:
    """Full comparison of A (base) against B (new)."""

    file_a: FileSummary
    file_b: FileSummary
    changes: tuple[ParameterChange, ...]
    summary: DiffSummary
    groups: tuple[FunctionalGroup, ...] = ()

    @property
    def checksum_differs(self) -> bool:
        return self.file_a.checksum != self.file_b.checksum

    @property
    def firmware_mismatch(self) -> bool:
        return self.file_a.revision_number != self.file_b.revision_number

    def with_changes(self, changes: tuple[ParameterChange, ...]) -> DiffResult:
        """Same comparison restricted to ``changes`` (e.g. after applying a filter)."""
        return replace(self, changes=changes)

    def grouped(self) -> list[tuple[FunctionalGroup, list[ParameterChange]]]:
        """Changes bucketed by group, motor-control groups first, then by group order."""
        buckets: dict[str, list[ParameterChange]] = {}
        known: dict[str, FunctionalGroup] = {g.id: g for g in self.groups}
        for change in self.changes:
            buckets.setdefault(change.group.id, []).append(change)
            known.setdefault(change.group.id, change.group)
        ordered = sorted(
            (known[gid] for gid in buckets),
            key=lambda g: (not g.motor_control, g.order, g.label),
        )
        return [(g, sorted(buckets[g.id], key=lambda c: c.key.sort_key)) for g in ordered]

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation (input for reports or an AI agent)."""
        return {
            "file_a": self.file_a.to_dict(),
            "file_b": self.file_b.to_dict(),
            "checksum_differs": self.checksum_differs,
            "firmware_mismatch": self.firmware_mismatch,
            "summary": self.summary.to_dict(),
            "groups": [
                {"id": g.id, "label": g.label, "motor_control": g.motor_control, "order": g.order}
                for g in self.groups
            ],
            "changes": [c.to_dict() for c in self.changes],
        }
