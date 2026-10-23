from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import ALL_SAMPLES, CIRCE, CIRCE_V8, MOTORLAND, PRIMER
from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.application.value_decoder import ValueDecoder
from sevcon_diff.domain.diff_models import DiffResult, ParameterChange
from sevcon_diff.domain.models import DcfDocument, ObjectKey

NOISE_INDICES = {0x1001, 0x29A0, 0x29A1, 0x4602, 0x5600, 0x5620, 0x2781, 0x4600, 0x5100}
EXPECTED_REAL = {
    0x2910, 0x2915, 0x2920, 0x2921, 0x2870, 0x4611, 0x4612, 0x4623, 0x4624, 0x461E, 0x4641,
    0x4651, 0x6075, 0x6076, 0x6080, 0x6083, 0x6087,
}


@pytest.fixture(scope="module")
def circe_vs_v8(compare: CompareDcfFiles) -> DiffResult:
    return compare.execute(CIRCE, CIRCE_V8)


@pytest.fixture(scope="module")
def primer_vs_motorland(compare: CompareDcfFiles) -> DiffResult:
    return compare.execute(PRIMER, MOTORLAND)


def by_key(result: DiffResult) -> dict[str, ParameterChange]:
    return {c.key.section: c for c in result.changes}


def test_known_decoded_values(circe_doc: DcfDocument) -> None:
    decoder = ValueDecoder()
    im_min = decoder.decode(circe_doc.parameters[ObjectKey(0x4641, 3)])
    assert im_min.integer == -500
    assert circe_doc.parameters[ObjectKey(0x4641, 3)].metadata.units == "A(RMS)"
    ls = decoder.decode(circe_doc.parameters[ObjectKey(0x4641, 0xA)])
    assert ls.physical == pytest.approx(0x068A * 5.96046447753906e-02)
    kp = circe_doc.parameters[ObjectKey(0x4651, 1)]
    assert kp.metadata.scaling == pytest.approx(0.000244140625)
    torque = decoder.decode(circe_doc.parameters[ObjectKey(0x6076)])
    assert torque.physical == pytest.approx(20.0)


def test_pole_pairs_change(circe_vs_v8: DiffResult) -> None:
    change = by_key(circe_vs_v8)["4641sub5"]
    assert change.old is not None and change.new is not None
    assert (change.old.integer, change.new.integer) == (4, 5)
    assert change.group.id == "motor_base"
    assert change.is_motor_control
    assert not change.is_noise


def test_speed_kp_uses_file_scaling(circe_vs_v8: DiffResult) -> None:
    change = by_key(circe_vs_v8)["4651sub1"]
    assert change.old is not None and change.new is not None
    assert (change.old.integer, change.new.integer) == (0, 128)
    assert change.new.physical == pytest.approx(0.03125)
    assert change.group.id == "speed_loop"


def test_monitoring_objects_are_noise(circe_vs_v8: DiffResult) -> None:
    noisy = [c for c in circe_vs_v8.changes if c.key.index in NOISE_INDICES]
    assert noisy, "the sample pair is expected to differ in counters/FIFOs"
    assert all(c.is_noise for c in noisy)
    assert {c.key.index for c in noisy} >= {0x1001, 0x29A0, 0x4602, 0x5600}


def test_bit_split_reports_only_changed_field(circe_vs_v8: DiffResult) -> None:
    change = by_key(circe_vs_v8)["2910sub1"]
    assert [b.name for b in change.bit_changes] == ["Speed Limit Mode"]
    assert change.delta is None


def test_same_firmware_and_checksum_indicator(circe_vs_v8: DiffResult) -> None:
    assert not circe_vs_v8.firmware_mismatch
    assert circe_vs_v8.file_a.checksum is not None
    assert "5620" not in {c.key.section for c in circe_vs_v8.changes if not c.is_noise}


def test_primer_vs_motorland_real_changes(primer_vs_motorland: DiffResult) -> None:
    relevant = [c for c in primer_vs_motorland.changes if not c.is_noise]
    indices = {c.key.index for c in relevant}
    assert indices & EXPECTED_REAL >= {0x4611, 0x4624, 0x461E, 0x4641, 0x4651, 0x6076, 0x2921}
    assert not indices & NOISE_INDICES
    assert all(c.group.id != "other" for c in relevant)
    im_min = by_key(primer_vs_motorland)["4641sub3"]
    assert im_min.old is not None and im_min.old.display == "-600"
    assert im_min.units == "A(RMS)"
    assert im_min.delta == pytest.approx(350)


@pytest.mark.parametrize("pair", [(CIRCE, CIRCE_V8), (CIRCE_V8, PRIMER), (PRIMER, MOTORLAND)])
def test_every_relevant_change_has_a_specific_group(
    compare: CompareDcfFiles, pair: tuple[Path, Path]
) -> None:
    result = compare.execute(*pair)
    unclassified = [
        c.key.section for c in result.changes if not c.is_noise and c.group.id == "other"
    ]
    assert unclassified == []


@pytest.mark.parametrize("path", ALL_SAMPLES, ids=lambda p: p.name)
def test_self_compare_is_empty(compare: CompareDcfFiles, path: Path) -> None:
    assert compare.execute(path, path).changes == ()


def test_result_is_json_serialisable(primer_vs_motorland: DiffResult) -> None:
    payload = json.loads(json.dumps(primer_vs_motorland.to_dict()))
    assert payload["summary"]["relevant"] == primer_vs_motorland.summary.relevant
    assert payload["file_b"]["modification_date"]
