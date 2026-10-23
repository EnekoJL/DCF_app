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
        assert len(tree.get_children()) == controller.result.summary.relevant
        tree.selection_set("4641sub3")
        app.update()
        controller.select_group("__motor__")
        controller.set_show_noise(True)
        app.update()
        assert len(tree.get_children()) >= controller.result.summary.motor_control
    finally:
        app.destroy()
