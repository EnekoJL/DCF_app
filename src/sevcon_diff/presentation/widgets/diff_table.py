"""Comparison table: a ttk.Treeview grouped by area, styled to match the customtkinter theme."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any, Literal

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import GroupSection
from sevcon_diff.presentation.widgets.theme import CARD, CARD_BORDER, FONT_FAMILY, MUTED

_STYLE = "Diff.Treeview"
_GROUP_PREFIX = "group:"
_BIT_PREFIX = "bit:"
_NAME_WIDTH = 520

# column id, title, width, anchor
_COLUMNS: tuple[tuple[str, str, int, Literal["w", "e", "center"]], ...] = (
    ("value_a", s.COL_A, 150, "e"),
    ("trend", s.COL_TREND, 44, "center"),
    ("value_b", s.COL_B, 150, "w"),
    ("units", s.COL_UNITS, 110, "w"),
)

_PALETTE = {
    "light": {
        "bg": "#FFFFFF", "fg": "#111827", "alt": "#F9FAFB", "head_bg": "#F3F4F6",
        "head_fg": "#6B7280", "sel": "#DBEAFE", "sel_fg": "#111827", "group_bg": "#EEF2FF",
        "group_fg": "#1E3A8A", "bit": "#6B7280", "added": "#15803D", "removed": "#B91C1C",
        "limit": "#B91C1C",
    },
    "dark": {
        "bg": "#1A1D23", "fg": "#E5E7EB", "alt": "#1F232A", "head_bg": "#22262E",
        "head_fg": "#9CA3AF", "sel": "#1E3A5F", "sel_fg": "#FFFFFF", "group_bg": "#232A3B",
        "group_fg": "#BFDBFE", "bit": "#9CA3AF", "added": "#4ADE80", "removed": "#F87171",
        "limit": "#F87171",
    },
}


class DiffTable(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, master: Any, on_select: Callable[[str | None], None]) -> None:
        super().__init__(
            master, fg_color=CARD, border_color=CARD_BORDER, border_width=1, corner_radius=12
        )
        self._on_select = on_select
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._style = ttk.Style(self)
        if "clam" in self._style.theme_names():
            self._style.theme_use("clam")
        self._tree = ttk.Treeview(
            self, columns=[c[0] for c in _COLUMNS], show=("tree", "headings"), style=_STYLE,
            selectmode="browse",
        )
        self._tree.heading("#0", text=s.COL_NAME, anchor="w")
        for col_id, title, _width, anchor in _COLUMNS:
            self._tree.heading(col_id, text=title, anchor=anchor)
            self._tree.column(col_id, stretch=False, anchor=anchor)
        self._tree.column("#0", stretch=True)
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        y_scroll = ctk.CTkScrollbar(self, command=self._tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=(10, 0))
        self._tree.configure(yscrollcommand=y_scroll.set)
        self._tree.bind("<<TreeviewSelect>>", self._selected)

        self._empty = ctk.CTkLabel(
            self, text=s.ROWS_EMPTY, text_color=MUTED, fg_color="transparent",
            font=ctk.CTkFont(FONT_FAMILY, 13),
        )
        self._hint = ctk.CTkLabel(
            self, text=s.HINT_EMPTY, anchor="w", justify="left", text_color=MUTED,
            font=ctk.CTkFont(FONT_FAMILY, 11), wraplength=1100,
        )
        self._hint.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(6, 8))
        self._wrap = 0
        self.bind("<Configure>", self._fit_hint)  # the frame's width never depends on the hint
        self.apply_theme(ctk.get_appearance_mode())

    def apply_theme(self, mode: str) -> None:
        palette = _PALETTE["dark" if mode.lower() == "dark" else "light"]
        # ttk widgets are not scaled by customtkinter: apply the DPI factor ourselves.
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        size = round(12 * scale)
        # keep references: a garbage-collected tk Font disappears from the style
        self._font = font = ctk.CTkFont(FONT_FAMILY, size)
        self._bold = bold = ctk.CTkFont(FONT_FAMILY, size, "bold")
        self._small = ctk.CTkFont(FONT_FAMILY, round(11 * scale))
        self._heading_font = ctk.CTkFont(FONT_FAMILY, round(11 * scale), "bold")
        row_height = int(font.metrics("linespace") * 2.0)
        self._tree.column("#0", width=round(_NAME_WIDTH * scale), minwidth=round(240 * scale))
        for col_id, _title, width, _anchor in _COLUMNS:
            self._tree.column(col_id, width=round(width * scale), minwidth=round(width * scale))
        self._style.configure(
            _STYLE, background=palette["bg"], fieldbackground=palette["bg"],
            foreground=palette["fg"], rowheight=row_height, borderwidth=0, relief="flat",
            font=font, indent=round(18 * scale),
        )
        self._style.map(
            _STYLE,
            background=[("selected", palette["sel"])],
            foreground=[("selected", palette["sel_fg"])],
        )
        self._style.configure(
            f"{_STYLE}.Heading", background=palette["bg"], foreground=palette["head_fg"],
            relief="flat", borderwidth=0, font=self._heading_font,
            padding=(round(8 * scale), round(8 * scale)),
        )
        self._style.map(f"{_STYLE}.Heading", background=[("active", palette["head_bg"])])
        self._style.layout(_STYLE, [("Treeview.treearea", {"sticky": "nswe"})])
        self._tree.tag_configure("odd", background=palette["alt"])
        self._tree.tag_configure(
            "group", background=palette["group_bg"], foreground=palette["group_fg"], font=bold
        )
        self._tree.tag_configure("bit", foreground=palette["bit"], font=self._small)
        self._tree.tag_configure("added", foreground=palette["added"])
        self._tree.tag_configure("removed", foreground=palette["removed"])
        self._tree.tag_configure("limit", foreground=palette["limit"])
        self._empty.configure(fg_color=palette["bg"])

    def set_sections(self, sections: list[GroupSection]) -> None:
        self._tree.delete(*self._tree.get_children())
        for section in sections:
            group_iid = _GROUP_PREFIX + section.id
            self._tree.insert(
                "", tk.END, iid=group_iid, open=True, tags=("group",),
                text=f"{section.label}   ·   {len(section.rows)}", values=("", "", "", ""),
            )
            for position, row in enumerate(section.rows):
                tags: list[str] = ["odd"] if position % 2 else []
                if row.kind in ("added", "removed"):
                    tags.append(row.kind)
                if row.out_of_limits:
                    tags.append("limit")
                self._tree.insert(
                    group_iid, tk.END, iid=row.iid, tags=tags, text=row.name, open=False,
                    values=(row.value_a, row.trend, row.value_b, row.units),
                )
                for index, bit in enumerate(row.bits):
                    self._tree.insert(
                        row.iid, tk.END, iid=f"{_BIT_PREFIX}{row.iid}:{index}", tags=("bit",),
                        text=bit.name, values=(bit.value_a, s.TREND_CHANGED, bit.value_b, ""),
                    )
                if row.bits:
                    self._tree.item(row.iid, open=True)
        if sections:
            self._empty.place_forget()
        else:
            self._empty.place(relx=0.5, rely=0.45, anchor="center")

    def _fit_hint(self, event: tk.Event[Any]) -> None:
        wrap = max(event.width - 40, 200)
        if abs(wrap - self._wrap) > 8:
            self._wrap = wrap
            self._hint.configure(wraplength=wrap)

    def set_hint(self, text: str) -> None:
        self._hint.configure(text=text)

    def _selected(self, _event: object) -> None:
        selection = self._tree.selection()
        iid = selection[0] if selection else None
        if iid and iid.startswith(_BIT_PREFIX):
            iid = self._tree.parent(iid)
        if iid and iid.startswith(_GROUP_PREFIX):
            iid = None
        self._on_select(iid)
