"""Motor profile read from one DCF: torque-speed maps, torque caps and motor constants.

Which objects make up the profile is data (``MotorProfileSpec``), loaded by the infrastructure
from ``knowledge/motor_profile.toml``; this module only defines the shapes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from sevcon_diff.domain.diff_models import DecodedValue
from sevcon_diff.domain.models import ObjectKey

RPM_TO_RAD_S = 2 * math.pi / 60


class LineStyle(StrEnum):
    SOLID = "solid"
    DASHED = "dashed"


# --- specification (what to read) -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CurveSpec:
    """Torque-speed map stored as ``points`` (torque, speed) pairs in consecutive subs.

    Point ``k`` (1-based) has its torque in sub ``2k-1`` and its speed in sub ``2k``.
    """

    id: str
    label: str
    index: int
    points: int
    style: LineStyle = LineStyle.SOLID
    optional: bool = False

    def torque_key(self, point: int) -> ObjectKey:
        return ObjectKey(self.index, 2 * point - 1)

    def speed_key(self, point: int) -> ObjectKey:
        return ObjectKey(self.index, 2 * point)


@dataclass(frozen=True, slots=True)
class ReferenceSpec:
    """Horizontal torque cap drawn over the curves (e.g. peak torque)."""

    id: str
    label: str
    key: ObjectKey


@dataclass(frozen=True, slots=True)
class ConstantSpec:
    key: ObjectKey
    label: str


@dataclass(frozen=True, slots=True)
class MotorProfileSpec:
    curves: tuple[CurveSpec, ...]
    references: tuple[ReferenceSpec, ...] = ()
    constants: tuple[ConstantSpec, ...] = ()


# --- extracted profile (what one file contains) ----------------------------------------


@dataclass(frozen=True, slots=True)
class TorqueSpeedPoint:
    speed_rpm: float
    torque_nm: float

    @property
    def power_kw(self) -> float:
        return self.torque_nm * self.speed_rpm * RPM_TO_RAD_S / 1000


@dataclass(frozen=True, slots=True)
class TorqueSpeedCurve:
    id: str
    label: str
    style: LineStyle
    points: tuple[TorqueSpeedPoint, ...]

    @property
    def peak_power(self) -> TorqueSpeedPoint | None:
        """Point with the highest theoretical power (first one on ties)."""
        return max(self.points, key=lambda p: p.power_kw, default=None)


@dataclass(frozen=True, slots=True)
class ReferenceLine:
    id: str
    label: str
    torque_nm: float


@dataclass(frozen=True, slots=True)
class MotorConstant:
    key: ObjectKey
    label: str
    value: DecodedValue | None  # None when the object is missing from the file
    units: str = ""


@dataclass(frozen=True, slots=True)
class MotorProfile:
    source: str  # file path as given
    curves: tuple[TorqueSpeedCurve, ...]
    references: tuple[ReferenceLine, ...] = ()
    constants: tuple[MotorConstant, ...] = ()

    @property
    def display_name(self) -> str:
        return self.source.replace("\\", "/").rsplit("/", 1)[-1]
