"""Change table: a ttk.Treeview styled to match the customtkinter theme."""

from __future__ import annotations

import re
import tkinter as tk
from collections.abc import Callable
from functools import partial
from tkinter import ttk
from typing import Any, Literal

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import ChangeRow

_NUMBER_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?")
_STYLE = "Diff.Treeview"

# column id, title, width, stretch, anchor
_COLUMNS: tuple[tuple[str, str, int, bool, Literal["w", "e"]], ...] = (
    ("key", s.COL_KEY, 100, False, "w"),
    ("name", s.COL_NAME, 340, True, "w"),
    ("group", s.COL_GROUP, 190, False, "w"),
    ("value_a", s.COL_A, 120, False, "e"),
    ("value_b", s.COL_B, 120, False, "e"),
    ("delta", s.COL_DELTA, 130, False, "e"),
    ("units", s.COL_UNITS, 80, False, "w"),
)

_PALETTE = {
    "light": {
        "bg": "#FFFFFF", "fg": "#1D2330", "alt": "#F5F7FA", "head_bg": "#E8ECF1",
        "head_fg": "#374151", "sel": "#BFDBFE", "sel_fg": "#0B1220", "motor": "#FFF7ED",
        "motor_alt": "#FDEFD9", "added": "#15803D", "removed": "#B91C1C", "noise": "#8A8F98",
        "limit": "#B91C1C",
    },
    "dark": {
        "bg": "#1E1F22", "fg": "#E6E8EB", "alt": "#25272B", "head_bg": "#2B2D31",
        "head_fg": "#C9CDD3", "sel": "#1F4E79", "sel_fg": "#FFFFFF", "motor": "#2A2318",
        "motor_alt": "#30281B", "added": "#4ADE80", "removed": "#F87171", "noise": "#7D828A",
        "limit": "#F87171",
    },
}


def _sort_value(text: str) -> tuple[int, float, str]:
    match = _NUMBER_RE.match(text.replace(",", ""))
    if match:
        return (0, float(match.group()), text)
    return (1, 0.0, text.lower())


class DiffTable(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, master: Any, on_select: Callable[[str | None], None]) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self._on_select = on_select
        self._rows: list[ChangeRow] = []
        self._sort_column: str | None = None
        self._sort_reverse = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._style = ttk.Style(self)
        if "clam" in self._style.theme_names():
            self._style.theme_use("clam")
        self._tree = ttk.Treeview(
            self, columns=[c[0] for c in _COLUMNS], show="headings", style=_STYLE,
            selectmode="browse",
        )
        for col_id, title, width, stretch, anchor in _COLUMNS:
            self._tree.heading(col_id, text=title, command=partial(self._sort_by, col_id))
            self._tree.column(col_id, width=width, minwidth=60, stretch=stretch, anchor=anchor)
        self._tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ctk.CTkScrollbar(self, command=self._tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ctk.CTkScrollbar(self, orientation="horizontal", command=self._tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self._tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self._tree.bind("<<TreeviewSelect>>", self._selected)
        self._status = ctk.CTkLabel(self, text="", anchor="w", font=ctk.CTkFont(size=11))
        self._status.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6)
        self.apply_theme(ctk.get_appearance_mode())

    def apply_theme(self, mode: str) -> None:
        palette = _PALETTE["dark" if mode.lower() == "dark" else "light"]
        # ttk widgets are not scaled by customtkinter: apply the DPI factor ourselves.
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        size = round(12 * scale)
        # keep references: a garbage-collected tk Font disappears from the style
        self._font = font = ctk.CTkFont(size=size)
        self._heading_font = heading_font = ctk.CTkFont(size=size, weight="bold")
        row_height = int(font.metrics("linespace") * 1.9)
        for col_id, _title, width, _stretch, _anchor in _COLUMNS:
            self._tree.column(col_id, width=round(width * scale), minwidth=round(60 * scale))
        self._style.configure(
            _STYLE, background=palette["bg"], fieldbackground=palette["bg"],
            foreground=palette["fg"], rowheight=row_height, borderwidth=0, relief="flat",
            font=font,
        )
        self._style.map(
            _STYLE,
            background=[("selected", palette["sel"])],
            foreground=[("selected", palette["sel_fg"])],
        )
        self._style.configure(
            f"{_STYLE}.Heading", background=palette["head_bg"], foreground=palette["head_fg"],
            relief="flat", borderwidth=0, font=heading_font,
            padding=(round(6 * scale), round(6 * scale)),
        )
        self._style.map(f"{_STYLE}.Heading", background=[("active", palette["sel"])])
        self._style.layout(_STYLE, [("Treeview.treearea", {"sticky": "nswe"})])
        self._tree.tag_configure("odd", background=palette["alt"])
        self._tree.tag_configure("motor", background=palette["motor"])
        self._tree.tag_configure("motor_odd", background=palette["motor_alt"])
        self._tree.tag_configure("added", foreground=palette["added"])
        self._tree.tag_configure("removed", foreground=palette["removed"])
        self._tree.tag_configure("noise", foreground=palette["noise"])
        self._tree.tag_configure("limit", foreground=palette["limit"])

    def set_rows(self, rows: list[ChangeRow], status: str) -> None:
        self._rows = list(rows)
        if self._sort_column is not None:
            self._apply_sort()
        self._render()
        self._status.configure(text=status)

    def _render(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for position, row in enumerate(self._rows):
            odd = position % 2 == 1
            tags: list[str] = []
            if row.motor_control:
                tags.append("motor_odd" if odd else "motor")
            elif odd:
                tags.append("odd")
            if row.kind in ("added", "removed"):
                tags.append(row.kind)
            if row.out_of_limits:
                tags.append("limit")
            if row.is_noise:
                tags.append("noise")
            self._tree.insert(
                "", tk.END, iid=row.iid, tags=tags,
                values=(row.key, row.name, row.group, row.value_a, row.value_b, row.delta,
                        row.units),
            )

    def _sort_by(self, column: str) -> None:
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column, self._sort_reverse = column, False
        self._apply_sort()
        self._render()
        for col_id, title, *_ in _COLUMNS:
            arrow = (" ▼" if self._sort_reverse else " ▲") if col_id == column else ""
            self._tree.heading(col_id, text=title + arrow)

    def _apply_sort(self) -> None:
        column = self._sort_column
        if column == "key":
            self._rows.sort(key=lambda r: r.sort_key, reverse=self._sort_reverse)
        elif column in ("value_a", "value_b", "delta"):
            self._rows.sort(key=lambda r: _sort_value(getattr(r, column)),
                            reverse=self._sort_reverse)
        elif column is not None:
            self._rows.sort(key=lambda r: str(getattr(r, column)).lower(),
                            reverse=self._sort_reverse)

    def _selected(self, _event: object) -> None:
        selection = self._tree.selection()
        self._on_select(selection[0] if selection else None)
