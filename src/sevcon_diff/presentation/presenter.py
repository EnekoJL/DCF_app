"""CompareController: mediates between passive widgets and the application layer.

It holds no widgets. The view is any object implementing :class:`CompareView`; results computed
in a worker thread are handed back through ``run_on_ui`` (``widget.after`` in the real app).
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.application.filters import DiffQuery
from sevcon_diff.domain.diff_models import DiffResult, ParameterChange
from sevcon_diff.domain.ports import ReportExporter
from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import (
    GROUP_ALL,
    FileCaption,
    GroupOption,
    GroupSection,
    SummaryViewModel,
    build_group_options,
    build_hint,
    build_sections,
    build_summary,
    file_caption,
)

UiScheduler = Callable[[Callable[[], None]], None]


class CompareView(Protocol):
    def show_paths(self, a: Path | None, b: Path | None) -> None: ...
    def show_busy(self, busy: bool) -> None: ...
    def show_file_captions(self, a: FileCaption, b: FileCaption) -> None: ...
    def show_summary(self, summary: SummaryViewModel | None) -> None: ...
    def show_groups(self, groups: list[GroupOption], selected: str) -> None: ...
    def show_sections(self, sections: list[GroupSection]) -> None: ...
    def show_hint(self, text: str) -> None: ...
    def show_status(self, message: str) -> None: ...
    def show_error(self, message: str) -> None: ...


def _run_inline(callback: Callable[[], None]) -> None:
    callback()


class CompareController:
    def __init__(
        self, compare: CompareDcfFiles, exporters: Mapping[str, ReportExporter]
    ) -> None:
        self._compare = compare
        self._exporters = dict(exporters)
        self._view: CompareView | None = None
        self._run_on_ui: UiScheduler = _run_inline
        self._path_a: Path | None = None
        self._path_b: Path | None = None
        self._result: DiffResult | None = None
        self._query = DiffQuery(motor_only=True)
        self._group = GROUP_ALL
        self._visible: dict[str, ParameterChange] = {}

    # --- wiring -------------------------------------------------------------------------
    def attach(self, view: CompareView, run_on_ui: UiScheduler | None = None) -> None:
        self._view = view
        self._run_on_ui = run_on_ui or _run_inline
        view.show_paths(self._path_a, self._path_b)
        view.show_status(s.STATUS_READY)

    @property
    def view(self) -> CompareView:
        if self._view is None:
            raise RuntimeError("controller has no view attached")
        return self._view

    @property
    def result(self) -> DiffResult | None:
        return self._result

    @property
    def export_formats(self) -> tuple[str, ...]:
        return tuple(self._exporters)

    # --- files --------------------------------------------------------------------------
    def set_path_a(self, path: Path | None) -> None:
        self._path_a = path
        self.view.show_paths(self._path_a, self._path_b)

    def set_path_b(self, path: Path | None) -> None:
        self._path_b = path
        self.view.show_paths(self._path_a, self._path_b)

    def swap(self) -> None:
        self._path_a, self._path_b = self._path_b, self._path_a
        self.view.show_paths(self._path_a, self._path_b)
        if self._result is not None and self._path_a and self._path_b:
            self.compare()

    def compare(self) -> threading.Thread | None:
        """Start the comparison in a worker thread (returned so tests can join it)."""
        if self._path_a is None or self._path_b is None:
            self.view.show_status(s.STATUS_NEED_FILES)
            return None
        path_a, path_b = self._path_a, self._path_b
        self.view.show_busy(True)
        self.view.show_status(s.COMPARING)

        def work() -> None:
            try:
                result = self._compare.execute(path_a, path_b)
            except Exception as exc:  # report any failure to the user, never crash the UI
                message = s.ERROR_COMPARE.format(error=exc)
                self._run_on_ui(lambda: self._on_failed(message))
            else:
                self._run_on_ui(lambda: self._on_compared(result))

        thread = threading.Thread(target=work, name="dcf-compare", daemon=True)
        thread.start()
        return thread

    def _on_compared(self, result: DiffResult) -> None:
        self._result = result
        view = self.view
        view.show_busy(False)
        view.show_file_captions(file_caption(result.file_a), file_caption(result.file_b))
        self._refresh()
        view.show_status(s.STATUS_DONE)

    def _on_failed(self, message: str) -> None:
        self.view.show_busy(False)
        self.view.show_status(message)
        self.view.show_error(message)

    # --- filtering ----------------------------------------------------------------------
    def set_search(self, text: str) -> None:
        self._query = replace(self._query, text=text)
        self._refresh()

    def set_include_other(self, include: bool) -> None:
        """Also show changes outside the focus areas (CAN, I/O, traction profiles...)."""
        self._query = replace(self._query, motor_only=not include)
        self._refresh()

    def select_group(self, group_id: str) -> None:
        self._group = group_id
        self._refresh()

    def _group_query(self) -> DiffQuery:
        if self._group == GROUP_ALL:
            return self._query
        return replace(self._query, group_ids=frozenset({self._group}))

    def current_view(self) -> DiffResult | None:
        """The result restricted to what the table currently shows (used for exports)."""
        if self._result is None:
            return None
        return self._group_query().apply_to(self._result)

    def _refresh(self) -> None:
        result = self._result
        if result is None:
            return
        include_other = not self._query.motor_only
        in_scope = replace(self._query, text="").apply(result.changes)
        self.view.show_summary(build_summary(result, len(in_scope), include_other))
        options = build_group_options(result, in_scope)
        if self._group not in {o.id for o in options}:
            self._group = GROUP_ALL
        self.view.show_groups(options, self._group)
        shown = self._group_query().apply(result.changes)
        self._visible = {c.key.section: c for c in shown}
        self.view.show_sections(build_sections(result.with_changes(shown)))
        self.view.show_hint(s.HINT_EMPTY)

    # --- selection / export -------------------------------------------------------------
    def select_change(self, iid: str | None) -> None:
        change = self._visible.get(iid) if iid else None
        self.view.show_hint(build_hint(change) if change else s.HINT_EMPTY)

    def export(self, fmt: str, path: Path) -> bool:
        current = self.current_view()
        if current is None:
            self.view.show_error(s.EXPORT_NOTHING)
            return False
        try:
            self._exporters[fmt].export(current, path)
        except Exception as exc:  # disk full, permissions, locked file...
            self.view.show_error(s.EXPORT_FAILED.format(error=exc))
            return False
        self.view.show_status(s.EXPORT_DONE.format(path=path))
        return True
