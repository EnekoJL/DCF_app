"""Decode DCF raw values: hex text -> integer (signed by DataType) -> physical -> label."""

from __future__ import annotations

import hashlib
import math
import string

from sevcon_diff.domain.diff_models import BitFieldChange, DecodedValue, ValueKind
from sevcon_diff.domain.models import DataType, DcfParameter

EMPTY_DISPLAY = "—"
_HEX_DIGITS = frozenset(string.hexdigits)


def parse_int(text: str | None) -> int | None:
    """Parse ``0x..`` hex or decimal integers; None if the text is not an integer."""
    if text is None:
        return None
    value = text.strip()
    if not value:
        return None
    try:
        if value.lower().startswith(("0x", "-0x")):
            return int(value, 16)
        return int(value, 10)
    except ValueError:
        return None


def format_number(value: float) -> str:
    """Compact human formatting: integers without decimals, otherwise 6 significant digits."""
    if math.isnan(value) or math.isinf(value):
        return str(value)
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    text = f"{value:.6g}"
    if "e" in text:
        text = f"{value:.9f}".rstrip("0").rstrip(".")
    return text


def format_signed(value: float) -> str:
    text = format_number(value)
    return text if text.startswith("-") else f"+{text}"


def to_signed(value: int, width: int) -> int:
    value &= (1 << width) - 1
    return value - (1 << width) if value >= 1 << (width - 1) else value


class ValueDecoder:
    """Turns the textual values of a :class:`DcfParameter` into :class:`DecodedValue`."""

    def decode(self, param: DcfParameter) -> DecodedValue:
        return self.decode_literal(param.raw_value, param)

    def decode_literal(self, text: str | None, param: DcfParameter) -> DecodedValue:
        """Decode any literal (value, limit or default) with the parameter's type and scaling."""
        data_type = param.data_type_enum
        if data_type is DataType.VISIBLE_STRING:
            return DecodedValue(
                kind=ValueKind.STRING, raw_text=text, display=text or EMPTY_DISPLAY, text=text or ""
            )
        if text is None or not text.strip():
            return DecodedValue(kind=ValueKind.EMPTY, raw_text=text, display=EMPTY_DISPLAY)
        if data_type is DataType.DOMAIN:
            return self._decode_domain(text)
        return self._decode_integer(text, param, data_type)

    def _decode_domain(self, text: str) -> DecodedValue:
        digits = text.strip().lower().removeprefix("0x")
        if not all(c in _HEX_DIGITS for c in digits):
            return DecodedValue(kind=ValueKind.INVALID, raw_text=text, display=text.strip())
        size = (len(digits) + 1) // 2
        digest = hashlib.sha1(digits.encode("ascii"), usedforsecurity=False)
        short = digest.hexdigest()[:8]
        return DecodedValue(
            kind=ValueKind.DOMAIN,
            raw_text=text,
            display=f"blob ({size} bytes, #{short})",
            blob_size=size,
            blob_hash=short,
        )

    def _decode_integer(
        self, text: str, param: DcfParameter, data_type: DataType | None
    ) -> DecodedValue:
        number = parse_int(text)
        if number is None:
            return DecodedValue(kind=ValueKind.INVALID, raw_text=text, display=text.strip())
        width = data_type.bit_width if data_type else None
        if width is not None:
            if data_type is not None and data_type.is_signed:
                number = to_signed(number, width) if number >= 0 else number
            elif number >= 0:
                number &= (1 << width) - 1
        hex_width = (width or max(8, number.bit_length())) // 4
        unsigned = number & ((1 << (hex_width * 4)) - 1)
        raw_hex = f"0x{unsigned:0{hex_width}X}"

        meta = param.metadata
        enum_label = meta.enum.get(number)
        physical = number * meta.scaling if meta.scaling is not None else None
        if enum_label is not None:
            display = f"{enum_label} ({number})"
        elif physical is not None:
            display = format_number(physical)
        elif meta.is_hex_format or meta.is_bit_split:
            display = raw_hex
        else:
            display = str(number)
        return DecodedValue(
            kind=ValueKind.INTEGER,
            raw_text=text,
            display=display,
            raw_hex=raw_hex,
            integer=number,
            physical=physical,
            enum_label=enum_label,
        )

    @staticmethod
    def numeric(value: DecodedValue | None) -> float | None:
        """Physical value if scaled, otherwise the raw integer."""
        if value is None or value.integer is None:
            return None
        return value.physical if value.physical is not None else float(value.integer)

    def bit_changes(
        self, param: DcfParameter, old: DecodedValue | None, new: DecodedValue | None
    ) -> tuple[BitFieldChange, ...]:
        """Only the BIT_SPLIT fields whose value differs."""
        old_int = old.integer if old is not None else None
        new_int = new.integer if new is not None else None
        if old_int is None and new_int is None:
            return ()
        changes: list[BitFieldChange] = []
        for bit_field in param.metadata.bit_fields:
            old_field = bit_field.extract(old_int) if old_int is not None else None
            new_field = bit_field.extract(new_int) if new_int is not None else None
            if old_field == new_field:
                continue
            changes.append(
                BitFieldChange(
                    name=bit_field.name,
                    mask=bit_field.mask,
                    old_value=old_field,
                    new_value=new_field,
                    old_label=bit_field.enum.get(old_field) if old_field is not None else None,
                    new_label=bit_field.enum.get(new_field) if new_field is not None else None,
                    units=bit_field.units,
                    hex_format=bit_field.number_format.upper() == "BASE16",
                )
            )
        return tuple(changes)
