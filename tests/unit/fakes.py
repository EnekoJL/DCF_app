"""Small in-memory test doubles for the domain ports."""

from __future__ import annotations

from sevcon_diff.domain.groups import FunctionalGroup
from sevcon_diff.domain.models import DcfDocument, DcfParameter, ObjectKey, ParameterMetadata

MOTOR = FunctionalGroup("motor", "Motor", motor_control=True, order=1)
OTHER = FunctionalGroup("other", "Otros", order=999)


class FakeClassifier:
    def __init__(self, motor_indices: frozenset[int] = frozenset()) -> None:
        self._motor = motor_indices

    def classify(self, param: DcfParameter) -> FunctionalGroup:
        return MOTOR if param.key.index in self._motor else OTHER

    def groups(self) -> tuple[FunctionalGroup, ...]:
        return (MOTOR, OTHER)


class FakeNoise:
    def __init__(self, noisy: frozenset[int] = frozenset()) -> None:
        self._noisy = noisy

    def noise_reason(self, param: DcfParameter) -> str | None:
        return "fake" if param.key.index in self._noisy else None

    @property
    def checksum_key(self) -> ObjectKey | None:
        return ObjectKey(0x5620)


def make_param(
    key: ObjectKey,
    value: str | None,
    data_type: int = 6,
    *,
    scaling: float | None = None,
    low: str | None = None,
    high: str | None = None,
    name: str = "param",
) -> DcfParameter:
    return DcfParameter(
        key=key,
        name=name,
        raw_value=value,
        data_type=data_type,
        access_type="rw",
        low_limit=low,
        high_limit=high,
        metadata=ParameterMetadata(scaling=scaling),
    )


def make_doc(*params: DcfParameter, revision: str = "0x1", date: str = "01-01-2025") -> DcfDocument:
    return DcfDocument(
        source=f"doc-{date}.dcf",
        file_info={"ModificationDate": date, "FileName": f"C:/x/{date}.dcf"},
        device_info={"RevisionNumber": revision},
        parameters={p.key: p for p in params},
    )
