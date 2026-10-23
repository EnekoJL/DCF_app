"""Use case: compare two DCF files."""

from __future__ import annotations

from pathlib import Path

from sevcon_diff.application.diff_engine import DcfDiffEngine
from sevcon_diff.domain.diff_models import DiffResult
from sevcon_diff.domain.ports import DcfReader


class CompareDcfFiles:
    """Reads both files through the injected reader and diffs them (A = base, B = new)."""

    def __init__(self, reader: DcfReader, engine: DcfDiffEngine) -> None:
        self._reader = reader
        self._engine = engine

    def execute(self, path_a: Path, path_b: Path) -> DiffResult:
        doc_a = self._reader.read(path_a)
        doc_b = self._reader.read(path_b)
        return self._engine.diff(doc_a, doc_b)
