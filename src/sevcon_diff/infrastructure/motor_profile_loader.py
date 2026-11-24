"""Loads ``knowledge/motor_profile.toml`` into a :class:`MotorProfileSpec`."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sevcon_diff.domain.models import ObjectKey
from sevcon_diff.domain.motor_profile import (
    ConstantSpec,
    CurveSpec,
    LineStyle,
    MotorProfileSpec,
    ReferenceSpec,
)
from sevcon_diff.infrastructure.rule_classifier import RuleError, load_knowledge

PROFILE_FILE = "motor_profile.toml"


def load_motor_profile_spec(file_name: str = PROFILE_FILE) -> MotorProfileSpec:
    return parse_motor_profile_spec(load_knowledge(file_name))


def parse_motor_profile_spec(data: Mapping[str, Any]) -> MotorProfileSpec:
    """Build the spec from already-parsed TOML; raises :class:`RuleError` on bad entries."""
    curves = tuple(_curve(raw) for raw in _blocks(data, "torque_speed_map"))
    if not curves:
        raise RuleError("motor profile needs at least one [[torque_speed_map]]")
    return MotorProfileSpec(
        curves=curves,
        references=tuple(
            ReferenceSpec(
                id=_text(raw, "id"), label=_text(raw, "label"), key=_key(_require(raw, "key"))
            )
            for raw in _blocks(data, "reference_line")
        ),
        constants=tuple(
            ConstantSpec(key=_key(_require(raw, "key")), label=_text(raw, "label"))
            for raw in _blocks(data, "constant")
        ),
    )


def _blocks(data: Mapping[str, Any], name: str) -> list[Mapping[str, Any]]:
    blocks = data.get(name, [])
    if not isinstance(blocks, list) or not all(isinstance(b, Mapping) for b in blocks):
        raise RuleError(f"[[{name}]] must be an array of tables")
    return blocks


def _require(raw: Mapping[str, Any], field: str) -> object:
    if field not in raw:
        raise RuleError(f"missing '{field}': {dict(raw)!r}")
    return raw[field]


def _text(raw: Mapping[str, Any], field: str) -> str:
    value = str(_require(raw, field)).strip()
    if not value:
        raise RuleError(f"empty '{field}': {dict(raw)!r}")
    return value


def _key(value: object) -> ObjectKey:
    try:
        return ObjectKey.parse(str(value))
    except ValueError as exc:
        raise RuleError(f"invalid object key: {value!r}") from exc


def _curve(raw: Mapping[str, Any]) -> CurveSpec:
    key = _key(_require(raw, "index"))
    if key.sub is not None:
        raise RuleError(f"torque_speed_map index must not have a sub-index: {dict(raw)!r}")
    points = _require(raw, "points")
    if not isinstance(points, int) or isinstance(points, bool) or points < 1:
        raise RuleError(f"'points' must be a positive integer: {dict(raw)!r}")
    try:
        style = LineStyle(str(raw.get("style", LineStyle.SOLID.value)).lower())
    except ValueError as exc:
        raise RuleError(f"invalid style: {dict(raw)!r}") from exc
    return CurveSpec(
        id=_text(raw, "id"),
        label=_text(raw, "label"),
        index=key.index,
        points=points,
        style=style,
        optional=bool(raw.get("optional", False)),
    )
