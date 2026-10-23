"""Domain model of a parsed Sevcon DCF file."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum

NAME_SEPARATOR = " \u203a "  # single right-pointing angle quotation mark


class DataType(IntEnum):
    """CANopen data types used by Sevcon DCF files."""

    BOOLEAN = 1
    INTEGER8 = 2
    INTEGER16 = 3
    INTEGER32 = 4
    UNSIGNED8 = 5
    UNSIGNED16 = 6
    UNSIGNED32 = 7
    VISIBLE_STRING = 9
    DOMAIN = 15

    @property
    def bit_width(self) -> int | None:
        return _BIT_WIDTHS.get(self)

    @property
    def is_signed(self) -> bool:
        return self in (DataType.INTEGER8, DataType.INTEGER16, DataType.INTEGER32)

    @property
    def is_integer(self) -> bool:
        return self.bit_width is not None


_BIT_WIDTHS: dict[DataType, int] = {
    DataType.BOOLEAN: 8,
    DataType.INTEGER8: 8,
    DataType.INTEGER16: 16,
    DataType.INTEGER32: 32,
    DataType.UNSIGNED8: 8,
    DataType.UNSIGNED16: 16,
    DataType.UNSIGNED32: 32,
}


@dataclass(frozen=True, slots=True)
class ObjectKey:
    """Object dictionary address: index plus optional sub-index (None for plain objects)."""

    index: int
    sub: int | None = None

    @property
    def sort_key(self) -> tuple[int, int]:
        return (self.index, -1 if self.sub is None else self.sub)

    @property
    def section(self) -> str:
        """Section name as written in the DCF, e.g. ``4641sub2`` or ``6076``."""
        base = f"{self.index:04X}"
        return base if self.sub is None else f"{base}sub{self.sub:X}"

    @property
    def label(self) -> str:
        """Human label, e.g. ``4641h sub2`` or ``6076h``."""
        base = f"{self.index:04X}h"
        return base if self.sub is None else f"{base} sub{self.sub:X}"

    @property
    def hex(self) -> str:
        """CANopen notation, e.g. ``0x4641.02``."""
        base = f"0x{self.index:04X}"
        return base if self.sub is None else f"{base}.{self.sub:02X}"

    def __str__(self) -> str:
        return self.section

    @classmethod
    def parse(cls, text: str) -> ObjectKey:
        """Parse ``4641``, ``4641sub2`` or ``0x4641.02`` (case-insensitive)."""
        raw = text.strip().lower().removeprefix("0x")
        if "sub" in raw:
            index_text, sub_text = raw.split("sub", 1)
            return cls(int(index_text, 16), int(sub_text, 16))
        if "." in raw:
            index_text, sub_text = raw.split(".", 1)
            return cls(int(index_text, 16), int(sub_text, 16))
        return cls(int(raw, 16))


@dataclass(frozen=True, slots=True)
class BitField:
    """One field of a ``NUMBER_FORMAT=BIT_SPLIT`` object: ``(raw & mask) >> shift``."""

    split: int
    name: str
    mask: int
    shift: int
    low_limit: int | None = None
    high_limit: int | None = None
    number_format: str = ""
    units: str = ""
    enum: Mapping[int, str] = field(default_factory=dict)

    def extract(self, raw: int) -> int:
        return (raw & self.mask) >> self.shift


@dataclass(frozen=True, slots=True)
class ParameterMetadata:
    """Information carried by the ``;SEVCONFIELD`` comment lines."""

    scaling: float | None = None
    units: str = ""
    description: str = ""
    category: str = ""
    access_level: int | None = None
    write_in_preop_only: bool = False
    number_formats: tuple[str, ...] = ()
    enum: Mapping[int, str] = field(default_factory=dict)
    bit_fields: tuple[BitField, ...] = ()

    @property
    def is_hex_format(self) -> bool:
        return "BASE16" in self.number_formats

    @property
    def is_bit_split(self) -> bool:
        return "BIT_SPLIT" in self.number_formats


@dataclass(frozen=True, slots=True)
class DcfParameter:
    """A value-carrying entry of the object dictionary (plain object or record sub-index)."""

    key: ObjectKey
    name: str
    raw_value: str | None
    data_type: int | None
    access_type: str = ""
    parent_name: str | None = None
    low_limit: str | None = None
    high_limit: str | None = None
    default_value: str | None = None
    metadata: ParameterMetadata = field(default_factory=ParameterMetadata)

    @property
    def data_type_enum(self) -> DataType | None:
        try:
            return DataType(self.data_type) if self.data_type is not None else None
        except ValueError:
            return None

    @property
    def full_name(self) -> str:
        return f"{self.parent_name}{NAME_SEPARATOR}{self.name}" if self.parent_name else self.name


@dataclass(frozen=True, slots=True)
class DcfDocument:
    """A parsed DCF: metadata sections plus the object dictionary parameters."""

    source: str
    file_info: Mapping[str, str]
    device_info: Mapping[str, str]
    parameters: Mapping[ObjectKey, DcfParameter]

    @property
    def file_name(self) -> str:
        return self.file_info.get("FileName", "")

    @property
    def modification_date(self) -> str:
        return self.file_info.get("ModificationDate", "")

    @property
    def modification_time(self) -> str:
        return self.file_info.get("ModificationTime", "")

    @property
    def product_number(self) -> str:
        return self.device_info.get("ProductNumber", "")

    @property
    def revision_number(self) -> str:
        return self.device_info.get("RevisionNumber", "")

    def get(self, key: ObjectKey) -> DcfParameter | None:
        return self.parameters.get(key)
