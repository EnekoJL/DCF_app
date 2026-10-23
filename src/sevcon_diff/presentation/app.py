"""Main window: layout and wiring of the passive widgets to the CompareController."""

from __future__ import annotations

import queue
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.presenter import CompareController
from sevcon_diff.presentation.view_models import (
    FileCaption,
    GroupOption,
    GroupSection,
    SummaryViewModel,
)
from sevcon_diff.presentation.widgets.diff_table import DiffTable
from sevcon_diff.presentation.widgets.file_selector import FileSelector
from sevcon_diff.presentation.widgets.summary_bar import SummaryBar
from sevcon_diff.presentation.widgets.theme import (
    ACCENT,
    ACCENT_HOVER,
    CARD_BORDER,
    CHIP,
    FONT_FAMILY,
    MUTED,
    SECONDARY_HOVER,
    TEXT,
    WINDOW,
)

MIN_SIZE = (1180, 720)
_POLL_MS = 40
_PAD = 20


class SevconDiffApp(ctk.CTk):  # type: ignore[misc]
    """Implements the ``CompareView`` protocol of the presenter."""

    def __init__(self, controller: CompareController) -> None:
        super().__init__(fg_color=WINDOW)
        self._controller = controller
        self._ui_queue: queue.SimpleQueue[Callable[[], None]] = queue.SimpleQueue()
        self.title(s.APP_TITLE)
        self.minsize(*MIN_SIZE)
        self.geometry(f"{MIN_SIZE[0] + 180}x{MIN_SIZE[1] + 120}")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_file_bar()
        self._summary = SummaryBar(
            self,
            on_group=controller.select_group,
            on_search=controller.set_search,
            on_include_other=controller.set_include_other,
        )
        self._summary.grid(row=2, column=0, sticky="ew", padx=_PAD, pady=(18, 10))
        self._table = DiffTable(self, on_select=controller.select_change)
        self._table.grid(row=3, column=0, sticky="nsew", padx=_PAD)
        self._build_footer()

        ctk.AppearanceModeTracker.add(self._on_appearance_changed, self)
        self.after(_POLL_MS, self._drain_ui_queue)
        controller.attach(self, self._ui_queue.put)

    # --- layout -------------------------------------------------------------------------
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=_PAD, pady=(16, 12))
        header.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(
            header, text=s.HEADER_TITLE, text_color=TEXT,
            font=ctk.CTkFont(FONT_FAMILY, 18, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header, text=s.HEADER_SUBTITLE, text_color=MUTED, font=ctk.CTkFont(FONT_FAMILY, 12)
        ).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(3, 0))
        appearance = ctk.CTkSegmentedButton(
            header, values=list(s.APPEARANCE_MODES), command=self._set_appearance, height=28,
            font=ctk.CTkFont(FONT_FAMILY, 11), selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER, unselected_color=CHIP,
            unselected_hover_color=SECONDARY_HOVER, text_color=TEXT, fg_color=CHIP,
        )
        appearance.set(next(iter(s.APPEARANCE_MODES)))
        appearance.grid(row=0, column=3, sticky="e")

    def _build_file_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=_PAD)
        bar.grid_columnconfigure((0, 2), weight=1, uniform="files")
        self._file_a = FileSelector(bar, "A", s.FILE_A_TITLE, self._controller.set_path_a)
        self._file_a.grid(row=0, column=0, sticky="nsew")
        ctk.CTkButton(
            bar, text=s.SWAP, width=40, height=40, corner_radius=20, fg_color=CHIP,
            hover_color=SECONDARY_HOVER, text_color=TEXT, font=ctk.CTkFont(FONT_FAMILY, 16),
            command=self._controller.swap,
        ).grid(row=0, column=1, padx=10)
        self._file_b = FileSelector(bar, "B", s.FILE_B_TITLE, self._controller.set_path_b)
        self._file_b.grid(row=0, column=2, sticky="nsew")
        self._compare_button = ctk.CTkButton(
            bar, text=s.COMPARE, width=150, corner_radius=12, fg_color=ACCENT,
            hover_color=ACCENT_HOVER, font=ctk.CTkFont(FONT_FAMILY, 14, "bold"),
            command=self._controller.compare,
        )
        self._compare_button.grid(row=0, column=3, sticky="ns", padx=(12, 0))

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=_PAD, pady=12)
        footer.grid_columnconfigure(0, weight=1)
        self._status = ctk.CTkLabel(
            footer, text="", anchor="w", text_color=MUTED, font=ctk.CTkFont(FONT_FAMILY, 11)
        )
        self._status.grid(row=0, column=0, sticky="ew")
        self._export_buttons = [
            ctk.CTkButton(
                footer, text=text, width=128, height=32, corner_radius=8, state="disabled",
                fg_color="transparent", border_width=1, border_color=CARD_BORDER,
                hover_color=SECONDARY_HOVER, text_color=TEXT,
                text_color_disabled=MUTED, font=ctk.CTkFont(FONT_FAMILY, 12),
                command=command,
            )
            for text, command in (
                (s.EXPORT_HTML, lambda: self._export("html", ".html", s.HTML_FILETYPES)),
                (s.EXPORT_PDF, lambda: self._export("pdf", ".pdf", s.PDF_FILETYPES)),
            )
        ]
        for col, button in enumerate(self._export_buttons, start=1):
            button.grid(row=0, column=col, padx=(8, 0))

    # --- theming ------------------------------------------------------------------------
    def _set_appearance(self, label: str) -> None:
        ctk.set_appearance_mode(s.APPEARANCE_MODES[label])

    def _on_appearance_changed(self, mode: str) -> None:
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

    def show_groups(self, groups: list[GroupOption], selected: str) -> None:
        self._summary.set_groups(groups, selected)

    def show_sections(self, sections: list[GroupSection]) -> None:
        self._table.set_sections(sections)

    def show_hint(self, text: str) -> None:
        self._table.set_hint(text)

    def show_status(self, message: str) -> None:
        self._status.configure(text=message)

    def show_error(self, message: str) -> None:
        messagebox.showerror(s.ERROR_TITLE, message, parent=self)


def launch(controller: CompareController) -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = SevconDiffApp(controller)
    app.mainloop()
