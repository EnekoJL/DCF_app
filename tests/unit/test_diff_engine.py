from __future__ import annotations

import json

import pytest
from fakes import FakeClassifier, FakeNoise, make_doc, make_param

from sevcon_diff.application.diff_engine import DcfDiffEngine
from sevcon_diff.domain.diff_models import ChangeKind
from sevcon_diff.domain.models import DcfDocument, ObjectKey

K1 = ObjectKey(0x4641, 2)
K2 = ObjectKey(0x6076)
K3 = ObjectKey(0x2000, 1)


def engine() -> DcfDiffEngine:
    return DcfDiffEngine(FakeClassifier(frozenset({0x4641})), FakeNoise(frozenset({0x2000})))


def test_self_compare_real_file_has_no_changes(
    circe_doc: DcfDocument, engine: DcfDiffEngine
) -> None:
    result = engine.diff(circe_doc, circe_doc)
    assert result.changes == ()
    assert result.summary.total == 0
    assert not result.checksum_differs
    assert not result.firmware_mismatch


def test_hex_padding_is_not_a_change() -> None:
    a = make_doc(make_param(K1, "0x80"))
    b = make_doc(make_param(K1, "0x0080"))
    assert engine().diff(a, b).changes == ()


def test_signed_equivalent_literals_are_not_a_change() -> None:
    a = make_doc(make_param(K1, "0xfe0c", 3))
    b = make_doc(make_param(K1, "0xFE0C", 3))
    assert engine().diff(a, b).changes == ()


def test_added_and_removed() -> None:
    a = make_doc(make_param(K1, "0x1"), make_param(K2, "0x2"))
    b = make_doc(make_param(K1, "0x1"), make_param(K3, "0x3"))
    changes = {c.key: c for c in engine().diff(a, b).changes}
    assert changes[K2].kind is ChangeKind.REMOVED
    assert changes[K2].new is None and changes[K2].old is not None
    assert changes[K3].kind is ChangeKind.ADDED
    assert changes[K3].old is None
    assert K1 not in changes


def test_modified_with_delta_group_and_noise() -> None:
    a = make_doc(make_param(K1, "0x0004", scaling=0.5), make_param(K3, "0x1"))
    b = make_doc(make_param(K1, "0x0005", scaling=0.5), make_param(K3, "0x2"))
    result = engine().diff(a, b)
    by_key = {c.key: c for c in result.changes}
    motor = by_key[K1]
    assert motor.kind is ChangeKind.MODIFIED
    assert motor.group.motor_control
    assert motor.delta == pytest.approx(0.5)
    assert motor.delta_percent == pytest.approx(25.0)
    assert motor.delta_display == "+0.5"
    assert by_key[K3].is_noise and by_key[K3].noise_reason == "fake"
    assert result.summary.relevant == 1
    assert result.summary.noise == 1
    assert result.summary.motor_control == 1


def test_out_of_limits_flags() -> None:
    a = make_doc(make_param(K1, "0x0005", low="1", high="10"))
    b = make_doc(make_param(K1, "0x000B", low="1", high="10"))
    change = engine().diff(a, b).changes[0]
    assert not change.old_out_of_limits
    assert change.new_out_of_limits
    assert change.low_limit is not None and change.low_limit.integer == 1


def test_inconsistent_limits_are_ignored() -> None:
    a = make_doc(make_param(K1, "0x0005", 3, low="0", high="0xFFFF"))
    b = make_doc(make_param(K1, "0x0006", 3, low="0", high="0xFFFF"))
    change = engine().diff(a, b).changes[0]
    assert not change.out_of_limits


def test_file_info_differences_are_not_changes() -> None:
    a = make_doc(make_param(K1, "0x1"), revision="0x1", date="01-01-2025")
    b = make_doc(make_param(K1, "0x1"), revision="0x2", date="02-02-2025")
    result = engine().diff(a, b)
    assert result.changes == ()
    assert result.firmware_mismatch
    assert result.file_a.modification_date == "01-01-2025"


def test_to_dict_is_json_serialisable() -> None:
    a = make_doc(make_param(K1, "0x0004", scaling=0.5), make_param(K2, "0x2"))
    b = make_doc(make_param(K1, "0x0005", scaling=0.5))
    payload = engine().diff(a, b).to_dict()
    text = json.dumps(payload)
    assert '"key": "4641sub2"' in text
    assert payload["summary"]["total"] == 2
