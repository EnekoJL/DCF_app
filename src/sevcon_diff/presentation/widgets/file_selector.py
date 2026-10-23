"""Picker for one DCF file: badge, file name, metadata line and browse button."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from typing import Any

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import FileCaption
from sevcon_diff.presentation.widgets.theme import (
    ACCENT,
    CARD,
    CARD_BORDER,
    CHIP,
    FONT_FAMILY,
    MUTED,
    SECONDARY_HOVER,
    TEXT,
)


class FileSelector(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self, master: Any, tag: str, title: str, on_selected: Callable[[Path], None]
    ) -> None:
        super().__init__(
            master, fg_color=CARD, border_color=CARD_BORDER, border_width=1, corner_radius=12
        )
        self._on_selected = on_selected
        self._initial_dir: str | None = None
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text=tag, width=36, height=36, corner_radius=10, fg_color=ACCENT,
            text_color="white", font=ctk.CTkFont(FONT_FAMILY, 15, "bold"),
        ).grid(row=0, column=0, rowspan=3, padx=(14, 12), pady=12)
        ctk.CTkLabel(
            self, text=title.upper(), anchor="w", text_color=MUTED,
            font=ctk.CTkFont(FONT_FAMILY, 10, "bold"), height=16,
        ).grid(row=0, column=1, sticky="sew", pady=(10, 0))
        self._name = ctk.CTkLabel(
            self, text=s.FILE_NONE, anchor="w", text_color=TEXT, height=20,
            font=ctk.CTkFont(FONT_FAMILY, 14, "bold"),
        )
        self._name.grid(row=1, column=1, sticky="ew")
        self._details = ctk.CTkLabel(
            self, text="", anchor="w", text_color=MUTED, height=16,
            font=ctk.CTkFont(FONT_FAMILY, 11),
        )
        self._details.grid(row=2, column=1, sticky="new", pady=(0, 10))
        ctk.CTkButton(
            self, text=s.BROWSE, width=96, height=32, corner_radius=8, fg_color=CHIP,
            hover_color=SECONDARY_HOVER, text_color=TEXT, font=ctk.CTkFont(FONT_FAMILY, 12),
            command=self._browse,
        ).grid(row=0, column=2, rowspan=3, padx=14)

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
