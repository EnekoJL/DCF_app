"""Main window: layout and wiring of the passive widgets to the CompareController."""

from __future__ import annotations

import queue
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.presenter import CompareController
from sevcon_diff.presentation.view_models import (
    ChangeRow,
    DetailViewModel,
    FileCaption,
    GroupItem,
    SummaryViewModel,
)
from sevcon_diff.presentation.widgets.detail_panel import DetailPanel
from sevcon_diff.presentation.widgets.diff_table import DiffTable
from sevcon_diff.presentation.widgets.file_selector import FileSelector
from sevcon_diff.presentation.widgets.group_sidebar import GroupSidebar
from sevcon_diff.presentation.widgets.summary_bar import SummaryBar
from sevcon_diff.presentation.widgets.theme import MUTED

MIN_SIZE = (1280, 760)
_POLL_MS = 40
_SASH_COLORS = ("gray80", "gray22")


class SevconDiffApp(ctk.CTk):  # type: ignore[misc]
    """Implements the ``CompareView`` protocol of the presenter."""

    def __init__(self, controller: CompareController) -> None:
        super().__init__()
        self._controller = controller
        self._ui_queue: queue.SimpleQueue[Callable[[], None]] = queue.SimpleQueue()
        self.title(s.APP_TITLE)
        self.minsize(*MIN_SIZE)
        self.geometry(f"{MIN_SIZE[0] + 140}x{MIN_SIZE[1] + 80}")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_file_bar()
        self._summary = SummaryBar(self)
        self._summary.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        self._build_body()
        self._build_footer()

        ctk.AppearanceModeTracker.add(self._on_appearance_changed, self)
        self._on_appearance_changed(ctk.get_appearance_mode())
        self.after(_POLL_MS, self._drain_ui_queue)
        controller.attach(self, self._ui_queue.put)

    # --- layout -------------------------------------------------------------------------
    def _build_file_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        bar.grid_columnconfigure((0, 2), weight=1)
        self._file_a = FileSelector(bar, "A", s.FILE_A_TITLE, self._controller.set_path_a)
        self._file_a.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            bar, text=s.SWAP, width=44, height=44, font=ctk.CTkFont(size=18),
            command=self._controller.swap,
        ).grid(row=0, column=1, padx=10)
        self._file_b = FileSelector(bar, "B", s.FILE_B_TITLE, self._controller.set_path_b)
        self._file_b.grid(row=0, column=2, sticky="ew")
        self._compare_button = ctk.CTkButton(
            bar, text=s.COMPARE, width=140, height=44,
            font=ctk.CTkFont(size=14, weight="bold"), command=self._controller.compare,
        )
        self._compare_button.grid(row=0, column=3, padx=(12, 0))

    def _build_body(self) -> None:
        self._panes = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, sashwidth=6, bd=0, relief="flat", showhandle=False
        )
        self._panes.grid(row=2, column=0, sticky="nsew", padx=16)
        self._sidebar = GroupSidebar(
            self._panes,
            on_group=self._controller.select_group,
            on_search=self._controller.set_search,
            on_show_noise=self._controller.set_show_noise,
            on_motor_only=self._controller.set_motor_only,
        )
        self._table = DiffTable(self._panes, on_select=self._controller.select_change)
        self._detail = DetailPanel(self._panes)
        scale = ctk.ScalingTracker.get_widget_scaling(self)  # tk.PanedWindow is not scaled
        self._panes.add(
            self._sidebar, minsize=round(220 * scale), width=round(260 * scale), stretch="never"
        )
        self._panes.add(self._table, minsize=round(480 * scale), stretch="always")
        self._panes.add(
            self._detail, minsize=round(280 * scale), width=round(360 * scale), stretch="never"
        )

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=16, pady=10)
        footer.grid_columnconfigure(3, weight=1)
        self._export_buttons = [
            ctk.CTkButton(
                footer, text=s.EXPORT_HTML, width=130, state="disabled",
                command=lambda: self._export("html", ".html", s.HTML_FILETYPES),
            ),
            ctk.CTkButton(
                footer, text=s.EXPORT_PDF, width=130, state="disabled",
                command=lambda: self._export("pdf", ".pdf", s.PDF_FILETYPES),
            ),
        ]
        for col, button in enumerate(self._export_buttons):
            button.grid(row=0, column=col, padx=(0, 8))
        ctk.CTkButton(footer, text=s.IMPACT, state="disabled", fg_color="gray40").grid(
            row=0, column=2, padx=(0, 12)
        )
        self._status = ctk.CTkLabel(footer, text="", anchor="w", text_color=MUTED)
        self._status.grid(row=0, column=3, sticky="ew")
        ctk.CTkLabel(footer, text=s.APPEARANCE, text_color=MUTED).grid(
            row=0, column=4, padx=(12, 6)
        )
        appearance = ctk.CTkSegmentedButton(
            footer, values=list(s.APPEARANCE_MODES), command=self._set_appearance
        )
        appearance.set(next(iter(s.APPEARANCE_MODES)))
        appearance.grid(row=0, column=5)

    # --- theming ------------------------------------------------------------------------
    def _set_appearance(self, label: str) -> None:
        ctk.set_appearance_mode(s.APPEARANCE_MODES[label])

    def _on_appearance_changed(self, mode: str) -> None:
        dark = mode.lower() == "dark"
        self._panes.configure(bg=_SASH_COLORS[1] if dark else _SASH_COLORS[0])
        self._table.apply_theme(mode)

    def destroy(self) -> None:
        ctk.AppearanceModeTracker.remove(self._on_appearance_changed)
        super().destroy()

    # --- threading ----------------------------------------------------------------------
    def _drain_ui_queue(self) -> None:
        try:
            while True:
                self._ui_queue.get_nowait()()
        except queue.Empty:
            pass
        self.after(_POLL_MS, self._drain_ui_queue)

    # --- actions ------------------------------------------------------------------------
    def _export(self, fmt: str, extension: str, filetypes: tuple[tuple[str, str], ...]) -> None:
        result = self._controller.result
        if result is None:
            self.show_error(s.EXPORT_NOTHING)
            return
        suggested = f"diff_{Path(result.file_a.path).stem}_vs_{Path(result.file_b.path).stem}"
        chosen = filedialog.asksaveasfilename(
            parent=self, title=s.EXPORT_TITLE, defaultextension=extension,
            filetypes=filetypes, initialfile=suggested + extension,
        )
        if chosen:
            self._controller.export(fmt, Path(chosen))

    # --- CompareView --------------------------------------------------------------------
    def show_paths(self, a: Path | None, b: Path | None) -> None:
        self._file_a.set_path(a)
        self._file_b.set_path(b)

    def show_busy(self, busy: bool) -> None:
        self._compare_button.configure(
            state="disabled" if busy else "normal", text=s.COMPARING if busy else s.COMPARE
        )
        self.configure(cursor="watch" if busy else "")

    def show_file_captions(self, a: FileCaption, b: FileCaption) -> None:
        self._file_a.set_caption(a)
        self._file_b.set_caption(b)

    def show_summary(self, summary: SummaryViewModel | None) -> None:
        self._summary.update_summary(summary)
        for button in self._export_buttons:
            button.configure(state="normal" if summary is not None else "disabled")

    def show_groups(self, groups: list[GroupItem], selected: str) -> None:
        self._sidebar.set_groups(groups, selected)

    def show_rows(self, rows: list[ChangeRow], status: str) -> None:
        self._table.set_rows(rows, status)

    def show_detail(self, detail: DetailViewModel | None) -> None:
        self._detail.show(detail)

    def show_status(self, message: str) -> None:
        self._status.configure(text=message)

    def show_error(self, message: str) -> None:
        messagebox.showerror(s.ERROR_TITLE, message, parent=self)


def launch(controller: CompareController) -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = SevconDiffApp(controller)
    app.mainloop()
