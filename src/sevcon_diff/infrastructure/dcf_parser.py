"""Line-based parser for Sevcon DCF files (INI-like, with ;SEVCONFIELD metadata comments).

configparser is not used on purpose: keys repeat (DESCRIPTION), comments carry data and the
parser must never fail on an odd line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from sevcon_diff.application.value_decoder import parse_int
from sevcon_diff.domain.models import (
    BitField,
    DcfDocument,
    DcfParameter,
    ObjectKey,
    ParameterMetadata,
)
from sevcon_diff.domain.ports import DcfReadError

ENCODING = "cp1252"
SEVCON_PREFIX = ";SEVCONFIELD"
RECORD_OBJECT_TYPES = frozenset({8, 9})  # ARRAY / RECORD headers carry no value

_SECTION_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\s*$")
_OBJECT_RE = re.compile(r"^(?P<index>[0-9A-Fa-f]{4})(?:sub(?P<sub>[0-9A-Fa-f]+))?$")
_ENUM_RE = re.compile(r"^(?P<value>-?0[xX][0-9A-Fa-f]+|-?\d+)\s*=\s*(?P<label>.*)$")
_SPLIT_KEYS = frozenset(
    {"PARAMETERNAME", "BITMASK", "BITSHIFT", "LOW_LIMIT", "HIGH_LIMIT", "NUMBERFORMAT", "UNITS"}
)


@dataclass(slots=True)
class _SplitBuilder:
    split: int
    values: dict[str, str] = field(default_factory=dict)
    enum: dict[int, str] = field(default_factory=dict)

    def build(self) -> BitField | None:
        mask = parse_int(self.values.get("BITMASK"))
        if mask is None:
            return None
        return BitField(
            split=self.split,
            name=self.values.get("PARAMETERNAME", f"Split {self.split}"),
            mask=mask,
            shift=parse_int(self.values.get("BITSHIFT")) or 0,
            low_limit=parse_int(self.values.get("LOW_LIMIT")),
            high_limit=parse_int(self.values.get("HIGH_LIMIT")),
            number_format=self.values.get("NUMBERFORMAT", ""),
            units=self.values.get("UNITS", ""),
            enum=dict(self.enum),
        )


@dataclass(slots=True)
class _Section:
    name: str
    keys: dict[str, str] = field(default_factory=dict)
    fields: dict[str, list[str]] = field(default_factory=dict)
    enum: dict[int, str] = field(default_factory=dict)
    splits: list[_SplitBuilder] = field(default_factory=list)

    def add_key(self, line: str) -> None:
        if "=" not in line:
            return
        key, value = line.split("=", 1)
        self.keys.setdefault(key.strip(), value.strip())

    def add_sevcon(self, body: str) -> None:
        body = body.strip()
        enum_match = _ENUM_RE.match(body)
        if enum_match:
            number = parse_int(enum_match["value"])
            if number is not None:
                target = self.splits[-1].enum if self.splits else self.enum
                target.setdefault(number, enum_match["label"].strip())
            return
        if "=" not in body:
            return
        key, value = (part.strip() for part in body.split("=", 1))
        key = key.upper()
        if key == "SPLIT":
            self.splits.append(_SplitBuilder(split=parse_int(value) or len(self.splits)))
        elif self.splits and key in _SPLIT_KEYS:
            self.splits[-1].values.setdefault(key, value)
        else:
            self.fields.setdefault(key, []).append(value)

    def field(self, key: str) -> str:
        values = self.fields.get(key)
        return values[0] if values else ""

    def metadata(self, inherited_category: str) -> ParameterMetadata:
        scaling: float | None
        try:
            scaling = float(self.field("SCALING")) if self.field("SCALING") else None
        except ValueError:
            scaling = None
        bit_fields = tuple(b for b in (s.build() for s in self.splits) if b is not None)
        return ParameterMetadata(
            scaling=scaling,
            units=self.field("UNITS"),
            description="\n".join(self.fields.get("DESCRIPTION", [])),
            category=(self.field("CATEGORY") or inherited_category).upper(),
            access_level=parse_int(self.field("ACCESS_LEVEL")),
            write_in_preop_only=self.field("WRITE_IN_PREOPERATIONAL_ONLY").upper() == "TRUE",
            number_formats=tuple(v.upper() for v in self.fields.get("NUMBER_FORMAT", [])),
            enum=dict(self.enum),
            bit_fields=bit_fields,
        )


class SevconDcfReader:
    """Implements the ``DcfReader`` port."""

    def read(self, path: Path) -> DcfDocument:
        try:
            text = Path(path).read_text(encoding=ENCODING, errors="replace")
        except OSError as exc:
            raise DcfReadError(f"{path}: {exc}") from exc
        document = self.parse(text, source=str(path))
        if not document.parameters:
            raise DcfReadError(f"{path}: no object dictionary entries found")
        return document

    def parse(self, text: str, source: str = "<memory>") -> DcfDocument:
        sections = _split_sections(text)
        records: dict[int, _Section] = {}
        objects: list[tuple[ObjectKey, _Section]] = []
        for section in sections:
            match = _OBJECT_RE.match(section.name)
            if not match:
                continue
            index = int(match["index"], 16)
            sub = int(match["sub"], 16) if match["sub"] is not None else None
            object_type = parse_int(section.keys.get("ObjectType"))
            if sub is None and object_type in RECORD_OBJECT_TYPES:
                records[index] = section
            else:
                objects.append((ObjectKey(index, sub), section))

        parameters: dict[ObjectKey, DcfParameter] = {}
        for key, section in objects:
            parent = records.get(key.index) if key.sub is not None else None
            parent_category = parent.field("CATEGORY") if parent is not None else ""
            parameters.setdefault(key, _build_parameter(key, section, parent, parent_category))

        by_name = {s.name: s for s in sections}
        return DcfDocument(
            source=source,
            file_info=dict(by_name["FileInfo"].keys) if "FileInfo" in by_name else {},
            device_info=dict(by_name["DeviceInfo"].keys) if "DeviceInfo" in by_name else {},
            parameters=parameters,
        )


def _build_parameter(
    key: ObjectKey, section: _Section, parent: _Section | None, parent_category: str
) -> DcfParameter:
    keys = section.keys
    return DcfParameter(
        key=key,
        name=keys.get("ParameterName", key.section),
        raw_value=keys.get("ParameterValue"),
        data_type=parse_int(keys.get("DataType")),
        access_type=keys.get("AccessType", "").lower(),
        parent_name=parent.keys.get("ParameterName") if parent is not None else None,
        low_limit=keys.get("LowLimit"),
        high_limit=keys.get("HighLimit"),
        default_value=keys.get("DefaultValue"),
        metadata=section.metadata(parent_category),
    )


def _split_sections(text: str) -> list[_Section]:
    sections: list[_Section] = []
    current: _Section | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        header = _SECTION_RE.match(line)
        if header:
            current = _Section(name=header["name"].strip())
            sections.append(current)
        elif current is None:
            continue
        elif line.startswith(SEVCON_PREFIX):
            current.add_sevcon(line[len(SEVCON_PREFIX) :])
        elif line.startswith(";"):
            continue
        else:
            current.add_key(line)
    return sections
