from __future__ import annotations

import pytest

from sevcon_diff.application.value_decoder import (
    ValueDecoder,
    format_number,
    parse_int,
    to_signed,
)
from sevcon_diff.domain.diff_models import ValueKind
from sevcon_diff.domain.models import BitField, DcfParameter, ObjectKey, ParameterMetadata

decoder = ValueDecoder()


def param(
    value: str | None, data_type: int = 6, meta: ParameterMetadata | None = None
) -> DcfParameter:
    return DcfParameter(
        key=ObjectKey(0x4641, 3),
        name="test",
        raw_value=value,
        data_type=data_type,
        metadata=meta or ParameterMetadata(),
    )


@pytest.mark.parametrize(
    ("value", "data_type", "expected"),
    [
        ("0xfe0c", 3, -500),
        ("0xff", 2, -1),
        ("0x7f", 2, 127),
        ("0x80", 2, -128),
        ("0xffffffff", 4, -1),
        ("0x7fffffff", 4, 2147483647),
        ("0xfe0c", 6, 65036),
        ("0xff", 5, 255),
        ("0xffffffff", 7, 4294967295),
        ("-32768", 3, -32768),
        ("0x1", 1, 1),
    ],
)
def test_integer_sign_by_width(value: str, data_type: int, expected: int) -> None:
    decoded = decoder.decode(param(value, data_type))
    assert decoded.kind is ValueKind.INTEGER
    assert decoded.integer == expected


def test_raw_hex_is_padded_to_type_width() -> None:
    assert decoder.decode(param("0xfe0c", 3)).raw_hex == "0xFE0C"
    assert decoder.decode(param("0x80", 6)).raw_hex == "0x0080"


def test_scaling_gives_physical_value() -> None:
    meta = ParameterMetadata(scaling=5.96046447753906e-02, units="uH")
    decoded = decoder.decode(param("0x068a", 6, meta))
    assert decoded.physical == pytest.approx(0x068A * 5.96046447753906e-02)
    assert decoded.display == "99.7782"


def test_no_scaling_shows_integer() -> None:
    decoded = decoder.decode(param("0x0004", 6))
    assert decoded.physical is None
    assert decoded.display == "4"


def test_scaled_integer_result_has_no_decimals() -> None:
    meta = ParameterMetadata(scaling=0.001, units="Nm")
    assert decoder.decode(param("0x00004e20", 7, meta)).display == "20"


def test_enum_label() -> None:
    meta = ParameterMetadata(enum={5: "SIN/COS"})
    decoded = decoder.decode(param("0x0005", 6, meta))
    assert decoded.enum_label == "SIN/COS"
    assert decoded.display == "SIN/COS (5)"


def test_base16_format_displays_hex() -> None:
    meta = ParameterMetadata(number_formats=("BASE16",))
    assert decoder.decode(param("0x3643", 6, meta)).display == "0x3643"


def test_bit_split_reports_only_changed_fields() -> None:
    fields = (
        BitField(0, "Proportional Braking", 0x1, 0, enum={0: "No", 1: "Yes"}),
        BitField(2, "Speed Limit Mode", 0x4, 2, enum={0: "Proportional", 1: "Fixed"}),
        BitField(3, "Wide", 0xF0, 4),
    )
    meta = ParameterMetadata(number_formats=("BIT_SPLIT",), bit_fields=fields)
    p = param("0x0005", 6, meta)
    old = decoder.decode(p)
    new = decoder.decode(param("0x0031", 6, meta))
    changes = decoder.bit_changes(p, old, new)
    assert [c.name for c in changes] == ["Speed Limit Mode", "Wide"]
    assert changes[0].old_label == "Fixed" and changes[0].new_label == "Proportional"
    assert (changes[1].old_value, changes[1].new_value) == (0, 3)


@pytest.mark.parametrize("value", ["0xZZ", "abc", "12.5", "0x"])
def test_unparseable_value_is_kept_raw(value: str) -> None:
    decoded = decoder.decode(param(value, 6))
    assert decoded.kind is ValueKind.INVALID
    assert decoded.display == value


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_value_is_empty(value: str | None) -> None:
    assert decoder.decode(param(value, 6)).kind is ValueKind.EMPTY


def test_visible_string() -> None:
    decoded = decoder.decode(param("ENGIRO MS1920", 9))
    assert decoded.kind is ValueKind.STRING
    assert decoded.text == "ENGIRO MS1920"
    assert decoder.decode(param("", 9)).text == ""


def test_domain_blob_summary() -> None:
    decoded = decoder.decode(param("0x0102030405", 15))
    assert decoded.kind is ValueKind.DOMAIN
    assert decoded.blob_size == 5
    assert decoded.blob_hash and len(decoded.blob_hash) == 8
    assert decoder.decode(param("0102030405", 15)).identity == decoded.identity
    assert decoder.decode(param("0x0102030406", 15)).identity != decoded.identity


def test_helpers() -> None:
    assert parse_int("0x1F") == 31
    assert parse_int(" 42 ") == 42
    assert parse_int("-7") == -7
    assert parse_int("nope") is None
    assert to_signed(0xFE0C, 16) == -500
    assert format_number(0.03125) == "0.03125"
    assert format_number(20.0) == "20"
    assert format_number(-0.000427246) == "-0.000427246"
