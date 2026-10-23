"""Picker for one DCF file: title, file name, metadata line and browse button."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from typing import Any

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import FileCaption
from sevcon_diff.presentation.widgets.theme import ACCENT, CARD, CARD_BORDER, MUTED


class FileSelector(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self, master: Any, tag: str, title: str, on_selected: Callable[[Path], None]
    ) -> None:
        super().__init__(master, fg_color=CARD, border_color=CARD_BORDER, border_width=1)
        self._on_selected = on_selected
        self._initial_dir: str | None = None
        self.grid_columnconfigure(1, weight=1)

        badge = ctk.CTkLabel(
            self, text=tag, width=30, height=30, corner_radius=8, fg_color=ACCENT,
            text_color="white", font=ctk.CTkFont(size=15, weight="bold"),
        )
        badge.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=12), text_color=MUTED).grid(
            row=0, column=1, sticky="sw", pady=(8, 0)
        )
        self._name = ctk.CTkLabel(
            self, text=s.FILE_NONE, anchor="w", font=ctk.CTkFont(size=14, weight="bold")
        )
        self._name.grid(row=1, column=1, sticky="ew")
        self._details = ctk.CTkLabel(
            self, text="", anchor="w", text_color=MUTED, font=ctk.CTkFont(size=11)
        )
        self._details.grid(row=2, column=1, sticky="ew", pady=(0, 8))
        ctk.CTkButton(self, text=s.BROWSE, width=100, command=self._browse).grid(
            row=0, column=2, rowspan=3, padx=12
        )

    def _browse(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self, title=s.OPEN_DCF, filetypes=s.DCF_FILETYPES, initialdir=self._initial_dir
        )
        if chosen:
            path = Path(chosen)
            self._initial_dir = str(path.parent)
            self._on_selected(path)

    def set_path(self, path: Path | None) -> None:
        self._name.configure(text=path.name if path else s.FILE_NONE)
        self._details.configure(text=str(path.parent) if path else "")
        if path:
            self._initial_dir = str(path.parent)

    def set_caption(self, caption: FileCaption) -> None:
        if caption.details:
            self._details.configure(text=caption.details)
