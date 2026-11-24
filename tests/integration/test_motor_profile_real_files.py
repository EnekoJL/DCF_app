"""Torque-speed maps and motor constants extracted from the real sample DCFs."""

from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from conftest import ALL_SAMPLES, MOTORLAND, MOTORLAND_RACE2, MOTORLAND_V7, PRIMER
from sevcon_diff.__main__ import build_profile_use_case, main
from sevcon_diff.application.motor_profile import LoadMotorProfiles
from sevcon_diff.domain.motor_profile import MotorProfile
from sevcon_diff.presentation.view_models import build_motor_chart
from sevcon_diff.presentation.widgets.torque_plot import draw_torque_chart


@pytest.fixture(scope="module")
def load() -> LoadMotorProfiles:
    return build_profile_use_case()


def one(load: LoadMotorProfiles, path: Path) -> MotorProfile:
    (profile,) = load.execute([path])
    return profile


def test_carrera1_main_map_exact(load: LoadMotorProfiles) -> None:
    profile = one(load, MOTORLAND)
    assert [c.id for c in profile.curves] == ["main"]  # 4615 all zeros -> omitted
    points = [(p.speed_rpm, p.torque_nm) for p in profile.curves[0].points]
    expected = [
        (0, 100), (2850, 100), (3500, 81.9), (4550, 71.6), (5000, 63.7), (5500, 57.3),
        (6000, 52.1), (6500, 47.8), (7000, 44.1),
    ]
    assert len(points) == len(expected)
    for (speed, torque), (exp_speed, exp_torque) in zip(points, expected, strict=True):
        assert speed == exp_speed
        assert torque == pytest.approx(exp_torque, abs=0.05)
    assert [(r.id, r.torque_nm) for r in profile.references] == [("peak_torque", 100)]


def test_carrera1_motor_constants(load: LoadMotorProfiles) -> None:
    constants = {c.key.section: c for c in one(load, MOTORLAND).constants}
    ls, ke = constants["4641subA"], constants["4641sub12"]
    assert ls.value is not None and ls.value.physical == pytest.approx(60.0, rel=1e-3)
    assert ls.units == "uH"
    assert ke.value is not None and ke.value.physical == pytest.approx(0.0286865, rel=1e-5)
    assert ke.units == "V/rads"
    assert constants["4641sub5"].value.integer == 5  # type: ignore[union-attr]


def test_carrera2_has_secondary_map(load: LoadMotorProfiles) -> None:
    curves = {c.id: c for c in one(load, MOTORLAND_RACE2).curves}
    assert set(curves) == {"main", "secondary"}
    secondary = curves["secondary"].points
    assert (secondary[0].speed_rpm, secondary[0].torque_nm) == (0, 150)
    assert (secondary[1].speed_rpm, secondary[1].torque_nm) == (1900, 150)


def test_v7_reaches_45_kw(load: LoadMotorProfiles) -> None:
    peak = one(load, MOTORLAND_V7).curves[0].peak_power
    assert peak is not None and peak.power_kw == pytest.approx(45, rel=0.02)


@pytest.mark.parametrize("path", ALL_SAMPLES, ids=lambda p: p.stem)
def test_every_sample_has_a_main_map(load: LoadMotorProfiles, path: Path) -> None:
    profile = one(load, path)
    main_curve = next(c for c in profile.curves if c.id == "main")
    assert main_curve.points
    speeds = [p.speed_rpm for p in main_curve.points]
    assert speeds == sorted(speeds)


def test_chart_renders_headless(load: LoadMotorProfiles, tmp_path: Path) -> None:
    chart = build_motor_chart(one(load, PRIMER), one(load, MOTORLAND))
    for dark in (False, True):
        fig = Figure(figsize=(8, 5))
        FigureCanvasAgg(fig)
        draw_torque_chart(fig, chart, show_power=True, dark=dark)
        fig.savefig(tmp_path / f"chart_{dark}.png")
    assert (tmp_path / "chart_True.png").stat().st_size > 0


def test_ke_change_flagged_between_primer_and_motorland(load: LoadMotorProfiles) -> None:
    chart = build_motor_chart(one(load, PRIMER), one(load, MOTORLAND))
    rows = {r.key_label: r for r in chart.constants}
    ke = rows["4641h sub12"]
    assert (ke.value_a, ke.value_b, ke.changed) == ("0.0291138", "0.0286865", True)
    assert not rows["4641h sub5"].changed


def test_profile_cli(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--profile", str(MOTORLAND_V7), str(MOTORLAND_RACE2)]) == 0
    out = capsys.readouterr().out
    assert "kW" in out and "Motorland_v7_45kW.dcf" in out and "4615" in out


def test_profile_cli_missing_file(tmp_path: Path) -> None:
    assert main(["--profile", str(tmp_path / "nope.dcf")]) == 2
