from __future__ import annotations

from typing import Any

import pytest

from sevcon_diff.domain.models import DcfParameter, ObjectKey, ParameterMetadata
from sevcon_diff.infrastructure.rule_classifier import (
    RuleError,
    TomlNoiseFilter,
    TomlRuleClassifier,
)


def key(text: str) -> ObjectKey:
    return ObjectKey.parse(text)


def p(text: str, category: str = "CONFIGURATION", access: str = "rw") -> DcfParameter:
    return DcfParameter(
        key=key(text),
        name=text,
        raw_value="0x0",
        data_type=6,
        access_type=access,
        metadata=ParameterMetadata(category=category),
    )


SYNTHETIC_GROUPS: dict[str, Any] = {
    "fallback": "other",
    "group": [
        {"id": "by_range", "label": "R", "rules": [{"range": ["4600", "46FF"]}]},
        {"id": "by_index", "label": "I", "rules": [{"index": "4641"}]},
        {"id": "first_subs", "label": "S1", "motor_control": True, "rules": [
            {"index": "4641", "subs": ["2", "A-C"]},
        ]},
        {"id": "second_subs", "label": "S2", "rules": [{"index": "4641", "subs": ["2", "1D"]}]},
        {"id": "other", "label": "Otros", "rules": []},
    ],
}


def test_specificity_beats_file_order() -> None:
    c = TomlRuleClassifier(SYNTHETIC_GROUPS)
    assert c.classify_key(key("4641sub2")).id == "first_subs"  # tie -> first in file
    assert c.classify_key(key("4641sub1D")).id == "second_subs"  # subs > index
    assert c.classify_key(key("4641sub3")).id == "by_index"  # index > range
    assert c.classify_key(key("4650sub1")).id == "by_range"
    assert c.classify_key(key("1000")).id == "other"


def test_sub_ranges_are_inclusive_hex() -> None:
    c = TomlRuleClassifier(SYNTHETIC_GROUPS)
    for sub in ("A", "B", "C"):
        assert c.classify_key(key(f"4641sub{sub}")).id == "first_subs"
    assert c.classify_key(key("4641sub9")).id == "by_index"
    assert c.classify_key(key("4641subD")).id == "by_index"


def test_subs_rule_does_not_match_plain_object() -> None:
    c = TomlRuleClassifier(SYNTHETIC_GROUPS)
    assert c.classify_key(key("4641")).id == "by_index"


def test_groups_sorted_motor_first() -> None:
    groups = TomlRuleClassifier(SYNTHETIC_GROUPS).groups()
    assert groups[0].id == "first_subs"


def test_malformed_rule_raises() -> None:
    with pytest.raises(RuleError):
        TomlRuleClassifier({"group": [{"id": "x", "rules": [{"subs": ["1"]}]}]})
    with pytest.raises(RuleError):
        TomlRuleClassifier({"group": [{"id": "x", "rules": [{"index": "XYZ"}]}]})


@pytest.mark.parametrize(
    ("text", "group_id"),
    [
        ("4641sub2", "motor_base"),
        ("4641sub3", "motor_base"),
        ("4641sub5", "motor_base"),
        ("4641sub1", "motor_base"),
        ("4641subA", "electrical_model"),
        ("4641sub2B", "electrical_model"),
        ("4641subD", "current_loop"),
        ("4641sub21", "current_loop"),
        ("4641sub16", "field_weakening"),
        ("4641sub1F", "field_weakening"),
        ("4621sub5", "electrical_model"),
        ("4621sub3", "thermal"),
        ("4617sub2", "motor_base"),
        ("4617sub1", "electrical_model"),
        ("6076", "motor_base"),
        ("4651sub1", "speed_loop"),
        ("2920sub2", "torque_limits"),
        ("2920sub5", "speed_limits"),
        ("2920sub10", "speed_limits"),
        ("2920sub7", "traction_profiles"),
        ("2907", "speed_limits"),
        ("2930sub2", "torque_limits"),
        ("2930sub1", "traction_profiles"),
        ("4612sub3", "voltage_limits"),
        ("4630sub10", "encoder"),
        ("461Esub1", "thermal"),
        ("2870sub2", "battery"),
        ("3300sub1", "io"),
        ("1A00sub1", "can_pdo"),
        ("1800sub2", "can_pdo"),
        ("9999", "other"),
    ],
)
def test_real_groups(classifier: TomlRuleClassifier, text: str, group_id: str) -> None:
    assert classifier.classify_key(key(text)).id == group_id


def test_real_groups_have_motor_flags(classifier: TomlRuleClassifier) -> None:
    by_id = {g.id: g for g in classifier.groups()}
    assert by_id["motor_base"].motor_control
    assert by_id["current_loop"].motor_control
    assert not by_id["can_pdo"].motor_control
    assert classifier.groups()[-1].id == "other"


SYNTHETIC_NOISE: dict[str, Any] = {
    "categories": ["MONITORING"],
    "access_types": ["ro"],
    "indicators": {"checksum": "5620"},
    "noise": [
        {"reason": "Medidas", "rules": [{"index": "4630", "subs": ["9-C"]}]},
        {"reason": "Rango", "rules": [{"range": ["2781", "2786"]}]},
    ],
    "keep": [{"reason": "Excepción", "rules": [{"index": "2783", "subs": ["1"]}]}],
}


def test_noise_rules_and_keep_override() -> None:
    f = TomlNoiseFilter(SYNTHETIC_NOISE)
    assert f.noise_reason(p("4630sub9")) == "Medidas"
    assert f.noise_reason(p("4630subC")) == "Medidas"
    assert f.noise_reason(p("4630sub10")) is None
    assert f.noise_reason(p("2785sub2")) == "Rango"
    assert f.noise_reason(p("2783sub1")) is None  # keep wins
    assert f.noise_reason(p("2783sub1", category="MONITORING")) is None
    assert f.noise_reason(p("6000", category="MONITORING")) == "CATEGORY=MONITORING"
    assert f.noise_reason(p("6000", access="ro")) == "AccessType=ro"
    assert f.noise_reason(p("6000")) is None
    assert f.checksum_key == ObjectKey(0x5620)


@pytest.mark.parametrize(
    "text", ["1001", "29A0sub1", "29A1sub3", "4602sub2", "5600sub1", "5620", "4630subA", "2781sub1"]
)
def test_real_noise(noise_filter: TomlNoiseFilter, text: str) -> None:
    assert noise_filter.noise_reason(p(text)) is not None


@pytest.mark.parametrize("text", ["4641sub5", "4651sub1", "6076", "4630sub10", "2920sub1"])
def test_real_configuration_is_not_noise(noise_filter: TomlNoiseFilter, text: str) -> None:
    assert noise_filter.noise_reason(p(text)) is None
