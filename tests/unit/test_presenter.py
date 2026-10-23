"""The presenter holds no widgets, so it is tested headless with a recording fake view."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import MOTORLAND, PRIMER
from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.domain.diff_models import DiffResult
from sevcon_diff.presentation.presenter import CompareController


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
    sections = view.last("show_sections")[0]
    rows = [row for section in sections for row in section.rows]
    assert rows and {r.iid for r in rows} >= {"4641sub3", "4611sub1"}
    assert all(c.is_motor_control for c in controller.current_view().changes)  # type: ignore[union-attr]
    assert not any(c.is_noise for c in controller.current_view().changes)  # type: ignore[union-attr]
    im_min = next(r for r in rows if r.iid == "4641sub3")
    assert (im_min.value_a, im_min.value_b, im_min.trend) == ("-600", "-250", "▲")
    summary = view.last("show_summary")[0]
    assert summary.headline == f"{len(rows)} cambios" and summary.other_count > 0

    options = view.last("show_groups")[0]
    assert all(o.count > 0 for o in options)
    controller.set_include_other(True)
    all_rows = [r for sec in view.last("show_sections")[0] for r in sec.rows]
    assert len(all_rows) == len(rows) + summary.other_count
    controller.set_include_other(False)

    controller.select_group("torque_limits")
    sections = view.last("show_sections")[0]
    assert [sec.id for sec in sections] == ["torque_limits"]

    controller.select_change("4611sub1")
    assert view.last("show_hint")[0].startswith("4611h sub1")

    assert controller.export("html", tmp_path / "r.html")
    exported, _path = exporter.exported[0]
    assert {c.group.id for c in exported.changes} == {"torque_limits"}


def test_compare_error_is_reported(compare: CompareDcfFiles, tmp_path: Path) -> None:
    controller, view, _ = make(compare)
    controller.set_path_a(tmp_path / "missing_a.dcf")
    controller.set_path_b(tmp_path / "missing_b.dcf")
    thread = controller.compare()
    assert thread is not None
    thread.join(timeout=10)
    assert "show_error" in view.calls
    assert view.calls["show_busy"][-1] == (False,)
