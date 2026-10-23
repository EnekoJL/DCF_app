from __future__ import annotations

from pathlib import Path

import pytest

from sevcon_diff.domain.models import DcfDocument, ObjectKey
from sevcon_diff.domain.ports import DcfReadError
from sevcon_diff.infrastructure.dcf_parser import SevconDcfReader


def test_record_sub_has_parent_and_inherits_category(circe_doc: DcfDocument) -> None:
    p = circe_doc.parameters[ObjectKey(0x4641, 3)]
    assert p.name == "Minimum Magnetizing Current (Im min)"
    assert p.parent_name == "AC Motor data"
    assert p.raw_value == "0xfe0c"
    assert p.data_type == 3
    assert p.access_type == "rw"
    assert p.metadata.category == "CONFIGURATION"
    assert p.metadata.units == "A(RMS)"
    assert p.metadata.access_level == 4
    assert p.metadata.write_in_preop_only is True
    assert (p.low_limit, p.high_limit, p.default_value) == ("-32768", "0", "50")


def test_record_header_is_not_a_parameter(circe_doc: DcfDocument) -> None:
    assert ObjectKey(0x4641) not in circe_doc.parameters


def test_plain_object_and_scaling(circe_doc: DcfDocument) -> None:
    p = circe_doc.parameters[ObjectKey(0x6076)]
    assert p.parent_name is None
    assert p.metadata.scaling == pytest.approx(0.001)
    assert p.metadata.units == "Nm"
    ls = circe_doc.parameters[ObjectKey(0x4641, 0xA)]
    assert ls.metadata.scaling == pytest.approx(5.96046447753906e-02)


def test_hex_subindex_without_padding(circe_doc: DcfDocument) -> None:
    assert ObjectKey(0x4641, 0xA) in circe_doc.parameters  # [4641subA]
    assert ObjectKey(0x4641, 0x12) in circe_doc.parameters  # [4641sub12]
    assert ObjectKey.parse("4641sub2B") == ObjectKey(0x4641, 0x2B)
    assert ObjectKey(0x4641, 0x2B).section == "4641sub2B"
    assert ObjectKey(0x4641, 2).hex == "0x4641.02"


def test_description_lines_are_joined(circe_doc: DcfDocument) -> None:
    description = circe_doc.parameters[ObjectKey(0x2910, 1)].metadata.description
    lines = description.split("\n")
    assert len(lines) == 16
    assert lines[0].startswith("Bit 0")
    assert lines[-1].startswith("Bit 15")


def test_bit_split_fields(circe_doc: DcfDocument) -> None:
    meta = circe_doc.parameters[ObjectKey(0x2910, 1)].metadata
    assert meta.is_bit_split
    by_name = {f.name: f for f in meta.bit_fields}
    speed = by_name["Speed Limit Mode"]
    assert (speed.split, speed.mask, speed.shift) == (2, 0x4, 2)
    assert speed.enum == {0: "Proportional to throttle", 1: "Fixed at maximum"}
    assert meta.enum == {}  # enum lines after SPLIT belong to the split


def test_split_units_and_object_with_two_number_formats(circe_doc: DcfDocument) -> None:
    meta = circe_doc.parameters[ObjectKey(0x1016, 1)].metadata
    assert meta.number_formats == ("BASE16", "BIT_SPLIT")
    assert meta.bit_fields[0].units == "ms"
    assert meta.units == ""


def test_object_enum(circe_doc: DcfDocument) -> None:
    meta = circe_doc.parameters[ObjectKey(0x4630, 3)].metadata
    assert meta.enum[5] == "SIN/COS"


def test_metadata_sections(circe_doc: DcfDocument) -> None:
    assert circe_doc.modification_date == "04-10-2025"
    assert circe_doc.file_name.endswith("circe-MS2223.dcf")
    assert circe_doc.product_number == "0x07055037"
    assert circe_doc.revision_number == "0x0001002c"
    # Non-hex sections never become parameters.
    assert all(0 <= k.index <= 0xFFFF for k in circe_doc.parameters)
    assert len(circe_doc.parameters) > 1000


SYNTHETIC = """\
garbage before any section
[FileInfo]
FileName=x.dcf
[DeviceInfo]
RevisionNumber=0x1
[Comments]
Line1=whatever=with=equals
[2000]
SubNumber=2
ObjectType=9
ParameterName=Parent
;SEVCONFIELD CATEGORY=MONITORING
[2000sub1]
ParameterName=Child
ParameterValue=0x0010
DataType=6
AccessType=RW
line without equals
;SEVCONFIELD SCALING=not-a-number
;SEVCONFIELD 410 = inclinometer
;SEVCONFIELD 0x20=hex key
;SEVCONFIELD LONELYTOKEN
;SEVCONFIELD CATEGORY=CONFIGURATION
; plain comment
[2001]
ParameterName=No value (wo)
DataType=1
AccessType=wo
[ZZZZ]
Foo=bar
[2002sub]
"""


def test_parser_is_robust_with_odd_lines() -> None:
    doc = SevconDcfReader().parse(SYNTHETIC)
    child = doc.parameters[ObjectKey(0x2000, 1)]
    assert child.parent_name == "Parent"
    assert child.access_type == "rw"
    assert child.metadata.scaling is None
    assert child.metadata.enum == {410: "inclinometer", 0x20: "hex key"}
    assert child.metadata.category == "CONFIGURATION"  # own category beats the parent's
    wo = doc.parameters[ObjectKey(0x2001)]
    assert wo.raw_value is None
    assert set(doc.parameters) == {ObjectKey(0x2000, 1), ObjectKey(0x2001)}
    assert doc.revision_number == "0x1"


def test_category_inherited_from_parent() -> None:
    text = SYNTHETIC.replace(";SEVCONFIELD CATEGORY=CONFIGURATION\n", "")
    child = SevconDcfReader().parse(text).parameters[ObjectKey(0x2000, 1)]
    assert child.metadata.category == "MONITORING"


def test_missing_file_raises_read_error(tmp_path: Path) -> None:
    with pytest.raises(DcfReadError):
        SevconDcfReader().read(tmp_path / "missing.dcf")


def test_not_a_dcf_raises_read_error(tmp_path: Path) -> None:
    path = tmp_path / "notes.dcf"
    path.write_text("hello\nworld\n", encoding="utf-8")
    with pytest.raises(DcfReadError):
        SevconDcfReader().read(path)
