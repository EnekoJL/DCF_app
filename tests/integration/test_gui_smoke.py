"""Builds the real window and runs a comparison through it. Skipped when no display exists."""

from __future__ import annotations

import time
import tkinter as tk

import pytest

from conftest import MOTORLAND, PRIMER
from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.presentation.presenter import CompareController


def _display_available() -> bool:
    try:
        root = tk.Tk()
    except tk.TclError:
        return False
    root.destroy()
    return True


pytestmark = pytest.mark.skipif(not _display_available(), reason="no display available")


def test_window_compares_and_filters(compare: CompareDcfFiles) -> None:
    from sevcon_diff.presentation.app import SevconDiffApp

    controller = CompareController(compare, {})
    app = SevconDiffApp(controller)
    try:
        controller.set_path_a(PRIMER)
        controller.set_path_b(MOTORLAND)
        thread = controller.compare()
        assert thread is not None
        thread.join(timeout=30)
        deadline = time.monotonic() + 10
        while controller.result is None and time.monotonic() < deadline:
            app.update()
        assert controller.result is not None
        app.update()
        tree = app._table._tree
        shown = sum(len(tree.get_children(g)) for g in tree.get_children())
        assert shown == len(controller.current_view().changes)  # type: ignore[union-attr]
        tree.selection_set("4641sub3")
        app.update()
        controller.set_include_other(True)
        controller.select_group("can_pdo")
        app.update()
        assert tree.get_children() == ("group:can_pdo",)
    finally:
        app.destroy()


def test_motor_chart_window(compare: CompareDcfFiles) -> None:
    from sevcon_diff.__main__ import build_profile_use_case
    from sevcon_diff.presentation.app import SevconDiffApp

    controller = CompareController(compare, {}, build_profile_use_case())
    app = SevconDiffApp(controller)
    try:
        assert app._chart_button.cget("state") == "disabled"
        controller.set_path_a(PRIMER)
        assert app._chart_button.cget("state") == "normal"
        controller.set_path_b(MOTORLAND)

        def open_chart() -> None:
            thread = controller.show_motor_chart()
            assert thread is not None
            thread.join(timeout=30)
            deadline = time.monotonic() + 10
            while app.chart_window is None and time.monotonic() < deadline:
                app.update()
            app.update()

        open_chart()
        window = app.chart_window
        assert window is not None and window.winfo_exists()
        assert len(window.figure.axes) == 1
        window.set_show_power(True)
        app.update()
        assert len(window.figure.axes) == 2  # power on a twin axis
        window.apply_theme("Dark")
        app.update()

        controller.set_path_a(None)  # only B now: same window is reused
        open_chart()
        assert app.chart_window is window
        window.destroy()
        app.update()
        open_chart()  # closed -> a new window
        assert app.chart_window is not window and app.chart_window is not None
    finally:
        app.destroy()
