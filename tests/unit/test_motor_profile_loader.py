from __future__ import annotations

from typing import Any

import pytest

from sevcon_diff.domain.models import ObjectKey
from sevcon_diff.domain.motor_profile import LineStyle
from sevcon_diff.infrastructure.motor_profile_loader import (
    load_motor_profile_spec,
    parse_motor_profile_spec,
)
from sevcon_diff.infrastructure.rule_classifier import RuleError


def test_packaged_spec_loads() -> None:
    spec = load_motor_profile_spec()
    assert [c.id for c in spec.curves] == ["main", "secondary"]
    main, secondary = spec.curves
    assert (main.index, main.points, main.style, main.optional) == (
        0x4611, 9, LineStyle.SOLID, False
    )
    assert (secondary.index, secondary.style, secondary.optional) == (
        0x4615, LineStyle.DASHED, True
    )
    assert main.torque_key(1) == ObjectKey(0x4611, 1)
    assert main.speed_key(9) == ObjectKey(0x4611, 0x12)
    assert len(spec.references) == 1
    assert spec.references[0].key == ObjectKey(0x6076)
    assert len(spec.constants) == 6
    assert spec.constants[0].key == ObjectKey(0x4641, 0xA)
    assert spec.constants[1].key == ObjectKey(0x4641, 0x12)


def _curve(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"id": "m", "label": "M", "index": "4611", "points": 2}
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "data",
    [
        {},  # no curves at all
        {"torque_speed_map": [_curve(index="zz")]},
        {"torque_speed_map": [_curve(index="4611sub1")]},
        {"torque_speed_map": [_curve(points=0)]},
        {"torque_speed_map": [_curve(points="9")]},
        {"torque_speed_map": [_curve(style="dotted")]},
        {"torque_speed_map": [{"label": "M", "index": "4611", "points": 2}]},
        {"torque_speed_map": [_curve()], "constant": [{"label": "Ls"}]},
        {"torque_speed_map": [_curve()], "reference_line": [{"id": "x", "label": "X",
                                                             "key": "nothex"}]},
        {"torque_speed_map": {"id": "not-an-array"}},
    ],
)
def test_malformed_spec_raises_rule_error(data: dict[str, Any]) -> None:
    with pytest.raises(RuleError):
        parse_motor_profile_spec(data)
