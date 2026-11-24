"""Extractor on synthetic documents and the chart view model (no files, no display)."""

from __future__ import annotations

from dataclasses import replace

import pytest
from fakes import make_doc, make_param

from sevcon_diff.application.motor_profile import MotorProfileExtractor
from sevcon_diff.application.value_decoder import ValueDecoder
from sevcon_diff.domain.models import ObjectKey
from sevcon_diff.domain.motor_profile import (
    ConstantSpec,
    CurveSpec,
    LineStyle,
    MotorProfile,
    MotorProfileSpec,
    ReferenceSpec,
    TorqueSpeedPoint,
)
from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import build_motor_chart

SPEC = MotorProfileSpec(
    curves=(
        CurveSpec("main", "Main", 0x4611, 3),
        CurveSpec("second", "Second", 0x4615, 2, LineStyle.DASHED, optional=True),
    ),
    references=(ReferenceSpec("peak", "Peak", ObjectKey(0x6076)),),
    constants=(ConstantSpec(ObjectKey(0x4641, 0x12), "Ke"),),
)


def extractor() -> MotorProfileExtractor:
    return MotorProfileExtractor(SPEC, ValueDecoder())


def test_power_is_torque_times_omega() -> None:
    assert TorqueSpeedPoint(speed_rpm=3500, torque_nm=120).power_kw == pytest.approx(
        43.98, abs=0.01
    )


def test_missing_objects_never_raise() -> None:
    profile = extractor().extract(make_doc())
    assert profile.curves == ()
    assert profile.references == ()
    assert len(profile.constants) == 1 and profile.constants[0].value is None


def test_points_kept_in_order_and_incomplete_ones_dropped() -> None:
    doc = make_doc(
        make_param(ObjectKey(0x4611, 1), "1600", scaling=0.0625),  # 100 Nm
        make_param(ObjectKey(0x4611, 2), "0"),
        make_param(ObjectKey(0x4611, 3), "800", scaling=0.0625),  # speed missing -> dropped
        make_param(ObjectKey(0x4611, 5), "640", scaling=0.0625),
        make_param(ObjectKey(0x4611, 6), "6000"),
        make_param(ObjectKey(0x4615, 1), "0", scaling=0.0625),  # optional map all zeros
        make_param(ObjectKey(0x4615, 2), "0"),
        make_param(ObjectKey(0x6076, None), "garbage"),  # undecodable -> no reference
    )
    profile = extractor().extract(doc)
    assert [c.id for c in profile.curves] == ["main"]
    points = profile.curves[0].points
    assert [(p.speed_rpm, p.torque_nm) for p in points] == [(0, 100), (6000, 40)]
    assert profile.references == ()


def _profile(ke_raw: str, source: str) -> MotorProfile:
    doc = make_doc(
        make_param(ObjectKey(0x4611, 1), "1600", scaling=0.0625),
        make_param(ObjectKey(0x4611, 2), "0"),
        make_param(ObjectKey(0x4611, 3), "1600", scaling=0.0625),
        make_param(ObjectKey(0x4611, 4), "3000"),
        make_param(ObjectKey(0x6076), "100"),
        make_param(ObjectKey(0x4641, 0x12), ke_raw, scaling=1 / 32768),
    )
    return replace(extractor().extract(doc), source=source)


def test_view_model_with_two_files() -> None:
    a = _profile("954", "C:\\dcf\\a.dcf")
    b = _profile("940", "/x/b.dcf")
    chart = build_motor_chart(a, b)
    assert chart.slots == ("A", "B")
    assert [(sr.slot, sr.file_name) for sr in chart.series] == [("A", "a.dcf"), ("B", "b.dcf")]
    series = chart.series[0]
    assert series.annotations[0] == ""  # 0 rpm -> 0 kW, not labelled
    assert series.annotations[1] == "31.4 kW"
    assert series.max_power_kw == pytest.approx(31.4159, rel=1e-4)
    assert "máx 31.4 kW" in series.legend and series.legend.startswith("A · Main")
    assert [r.slot for r in chart.references] == ["A", "B"]
    assert chart.references[0].text.endswith("100 Nm")
    (ke,) = chart.constants
    assert ke.changed and ke.value_a != ke.value_b
    assert chart.title == s.CHART_TITLE_TWO.format(a="a.dcf", b="b.dcf")


def test_view_model_with_only_b() -> None:
    b = _profile("940", "b.dcf")
    chart = build_motor_chart(None, b)
    assert chart.slots == ("B",)
    assert {sr.slot for sr in chart.series} == {"B"}
    (ke,) = chart.constants
    assert ke.value_a == s.MISSING_VALUE and ke.value_b != s.MISSING_VALUE
    assert not ke.changed


def test_view_model_empty() -> None:
    chart = build_motor_chart(None, None)
    assert chart.empty and chart.title == s.CHART_TITLE
