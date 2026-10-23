"""Ports (Protocols) implemented by the outer layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from sevcon_diff.domain.diff_models import DiffResult
from sevcon_diff.domain.groups import FunctionalGroup
from sevcon_diff.domain.models import DcfDocument, DcfParameter, ObjectKey


class DcfReadError(Exception):
    """A DCF file could not be read at all (missing, unreadable, not a DCF)."""


class DcfReader(Protocol):
    def read(self, path: Path) -> DcfDocument: ...


class ParameterClassifier(Protocol):
    def classify(self, param: DcfParameter) -> FunctionalGroup: ...

    def groups(self) -> tuple[FunctionalGroup, ...]:
        """All known groups (used to build the UI list even when empty)."""
        ...


class NoiseFilter(Protocol):
    def noise_reason(self, param: DcfParameter) -> str | None:
        """Why ``param`` is monitoring noise, or None if it is real configuration."""
        ...

    @property
    def checksum_key(self) -> ObjectKey | None:
        """Object shown as the 'configuration differs' indicator."""
        ...


class ReportExporter(Protocol):
    def export(self, result: DiffResult, path: Path) -> None: ...


@dataclass(frozen=True, slots=True)
class ChangeImpact:
    key: ObjectKey
    severity: str
    explanation: str


@dataclass(frozen=True, slots=True)
class ImpactReport:
    """Output of a future AI impact analysis (not implemented in v1)."""

    summary: str
    impacts: tuple[ChangeImpact, ...] = field(default_factory=tuple)


class ChangeImpactAnalyzer(Protocol):
    """Future extension point: explains the expected effect of the changes."""

    def analyze(self, result: DiffResult) -> ImpactReport: ...
