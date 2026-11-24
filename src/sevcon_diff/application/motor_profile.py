"""Extract the torque-speed maps and motor constants of a DCF (what the chart window shows)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from sevcon_diff.application.value_decoder import ValueDecoder
from sevcon_diff.domain.models import DcfDocument, ObjectKey
from sevcon_diff.domain.motor_profile import (
    CurveSpec,
    MotorConstant,
    MotorProfile,
    MotorProfileSpec,
    ReferenceLine,
    TorqueSpeedCurve,
    TorqueSpeedPoint,
)
from sevcon_diff.domain.ports import DcfReader


class MotorProfileExtractor:
    """Reads the objects named by the spec; missing or undecodable objects are skipped."""

    def __init__(self, spec: MotorProfileSpec, decoder: ValueDecoder) -> None:
        self._spec = spec
        self._decoder = decoder

    def extract(self, doc: DcfDocument) -> MotorProfile:
        curves = (self._curve(doc, spec) for spec in self._spec.curves)
        references = (
            ReferenceLine(ref.id, ref.label, torque)
            for ref in self._spec.references
            if (torque := self._number(doc, ref.key)) is not None
        )
        constants = []
        for const in self._spec.constants:
            param = doc.get(const.key)
            constants.append(
                MotorConstant(
                    key=const.key,
                    label=const.label,
                    value=self._decoder.decode(param) if param is not None else None,
                    units=param.metadata.units if param is not None else "",
                )
            )
        return MotorProfile(
            source=doc.source,
            curves=tuple(c for c in curves if c is not None),
            references=tuple(references),
            constants=tuple(constants),
        )

    def _curve(self, doc: DcfDocument, spec: CurveSpec) -> TorqueSpeedCurve | None:
        points: list[TorqueSpeedPoint] = []
        for k in range(1, spec.points + 1):
            torque = self._number(doc, spec.torque_key(k))
            speed = self._number(doc, spec.speed_key(k))
            if torque is not None and speed is not None:
                points.append(TorqueSpeedPoint(speed_rpm=speed, torque_nm=torque))
        if not points or (spec.optional and all(p.torque_nm == 0 for p in points)):
            return None
        return TorqueSpeedCurve(spec.id, spec.label, spec.style, tuple(points))

    def _number(self, doc: DcfDocument, key: ObjectKey) -> float | None:
        param = doc.get(key)
        if param is None:
            return None
        return self._decoder.numeric(self._decoder.decode(param))


class LoadMotorProfiles:
    """Use case: read each file and extract its motor profile (order preserved)."""

    def __init__(self, reader: DcfReader, extractor: MotorProfileExtractor) -> None:
        self._reader = reader
        self._extractor = extractor

    def execute(self, paths: Sequence[Path]) -> tuple[MotorProfile, ...]:
        return tuple(self._extractor.extract(self._reader.read(path)) for path in paths)
