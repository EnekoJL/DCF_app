"""The presenter holds no widgets, so it is tested headless with a recording fake view."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import MOTORLAND, PRIMER
from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.domain.diff_models import DiffResult
from sevcon_diff.presentation.presenter import CompareController
from sevcon_diff.presentation.view_models import GROUP_MOTOR


class RecordingView:
    def __init__(self) -> None:
        self.calls: dict[str, list[Any]] = {}

    def __getattr__(self, name: str) -> Any:
        if not name.startswith("show_"):
            raise AttributeError(name)
        return lambda *args: self.calls.setdefault(name, []).append(args)

    def last(self, name: str) -> Any:
        return self.calls[name][-1]


class RecordingExporter:
    def __init__(self) -> None:
        self.exported: list[tuple[DiffResult, Path]] = []

    def export(self, result: DiffResult, path: Path) -> None:
        self.exported.append((result, path))


def make(compare: CompareDcfFiles) -> tuple[CompareController, RecordingView, RecordingExporter]:
    exporter = RecordingExporter()
    controller = CompareController(compare, {"html": exporter})
    view = RecordingView()
    controller.attach(view)  # type: ignore[arg-type]
    return controller, view, exporter


def test_compare_flow(compare: CompareDcfFiles, tmp_path: Path) -> None:
    controller, view, exporter = make(compare)
    assert controller.compare() is None  # no files yet
    controller.set_path_a(PRIMER)
    controller.set_path_b(MOTORLAND)
    thread = controller.compare()
    assert thread is not None
    thread.join(timeout=30)

    assert view.calls["show_busy"] == [(True,), (False,)]
    rows, _status = view.last("show_rows")
    assert rows and not any(r.is_noise for r in rows)
    keys = {r.iid for r in rows}
    assert "4641sub3" in keys

    controller.set_show_noise(True)
    assert len(view.last("show_rows")[0]) > len(rows)
    controller.set_show_noise(False)

    controller.select_group(GROUP_MOTOR)
    motor_rows = view.last("show_rows")[0]
    assert motor_rows and all(r.motor_control for r in motor_rows)

    controller.select_change("4641sub3")
    detail = view.last("show_detail")[0]
    assert detail is not None and "Im min" in detail.title
    assert any(value.startswith("-600") for _name, value in detail.fields)

    assert controller.export("html", tmp_path / "r.html")
    exported, _path = exporter.exported[0]
    assert all(c.is_motor_control for c in exported.changes)


def test_compare_error_is_reported(compare: CompareDcfFiles, tmp_path: Path) -> None:
    controller, view, _ = make(compare)
    controller.set_path_a(tmp_path / "missing_a.dcf")
    controller.set_path_b(tmp_path / "missing_b.dcf")
    thread = controller.compare()
    assert thread is not None
    thread.join(timeout=10)
    assert "show_error" in view.calls
    assert view.calls["show_busy"][-1] == (False,)
