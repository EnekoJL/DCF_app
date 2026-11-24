"""Torque-speed chart window: matplotlib canvas + toolbar and the motor constants table.

matplotlib is only imported here (lazily, from ``app.py``) so a missing install never breaks
the main window.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import SLOT_A, SLOT_B, MotorChartViewModel
from sevcon_diff.presentation.widgets.theme import (
    CARD,
    CARD_BORDER,
    FONT_FAMILY,
    MUTED,
    SERIES_A,
    SERIES_B,
    TEXT,
    WARN,
    WINDOW,
    pick,
)
from sevcon_diff.presentation.widgets.torque_plot import draw_torque_chart

_SIZE = (1320, 780)
_MIN_SIZE = (900, 560)
_PAD = 16
_TABLE_WIDTH = 440
_SLOT_COLOURS = {SLOT_A: SERIES_A, SLOT_B: SERIES_B}


class TorqueChartWindow(ctk.CTkToplevel):  # type: ignore[misc]
    def __init__(self, master: Any, chart: MotorChartViewModel) -> None:
        super().__init__(master, fg_color=WINDOW)
        self._chart = chart
        self._dark = ctk.get_appearance_mode().lower() == "dark"
        self.title(s.CHART_WINDOW_TITLE)
        self.geometry(f"{_SIZE[0]}x{_SIZE[1]}")
        self.minsize(*_MIN_SIZE)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=_PAD, pady=(14, 10))
        header.grid_columnconfigure(0, weight=1)
        self._title_label = ctk.CTkLabel(
            header, text=chart.title, anchor="w", text_color=TEXT,
            font=ctk.CTkFont(FONT_FAMILY, 19, "bold"),
        )
        self._title_label.grid(row=0, column=0, sticky="ew")
        self._show_power = tk.BooleanVar(master=self, value=False)
        self.power_toggle = ctk.CTkCheckBox(
            header, text=s.CHART_SHOW_POWER, variable=self._show_power, command=self._redraw,
            text_color=TEXT, font=ctk.CTkFont(FONT_FAMILY, 14),
        )
        self.power_toggle.grid(row=0, column=1, sticky="e")

        plot_card = ctk.CTkFrame(
            self, fg_color=CARD, border_color=CARD_BORDER, border_width=1, corner_radius=12
        )
        plot_card.grid(row=1, column=0, sticky="nsew", padx=(_PAD, 8), pady=(0, _PAD))
        plot_card.grid_columnconfigure(0, weight=1)
        plot_card.grid_rowconfigure(0, weight=1)
        self.figure = Figure(figsize=(9, 6), dpi=100)
        self._mpl_canvas = FigureCanvasTkAgg(self.figure, master=plot_card)
        plot_widget = self._mpl_canvas.get_tk_widget()
        plot_widget.configure(highlightthickness=0, borderwidth=0)
        plot_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        self._toolbar = NavigationToolbar2Tk(self._mpl_canvas, plot_card, pack_toolbar=False)
        self._toolbar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        self._table_card = ctk.CTkFrame(
            self, width=_TABLE_WIDTH, fg_color=CARD, border_color=CARD_BORDER, border_width=1,
            corner_radius=12,
        )
        self._table_card.grid(row=1, column=1, sticky="nsew", padx=(8, _PAD), pady=(0, _PAD))
        self._table_body: ctk.CTkFrame | None = None
        self._build_table()

        self.apply_theme(ctk.get_appearance_mode())

    # --- public -------------------------------------------------------------------------
    def update_chart(self, chart: MotorChartViewModel) -> None:
        self._chart = chart
        self._title_label.configure(text=chart.title)
        self._build_table()
        self._toolbar.update()  # forget the zoom history of the previous data
        self._redraw()

    def apply_theme(self, mode: str) -> None:
        self._dark = mode.lower() == "dark"
        background = pick(CARD, self._dark)
        self._mpl_canvas.get_tk_widget().configure(background=background)
        self._paint_toolbar(background, pick(TEXT, self._dark))
        self._redraw()

    def set_show_power(self, show: bool) -> None:
        self._show_power.set(show)
        self._redraw()

    # --- drawing ------------------------------------------------------------------------
    def _redraw(self) -> None:
        draw_torque_chart(
            self.figure, self._chart, show_power=self._show_power.get(), dark=self._dark
        )
        self._mpl_canvas.draw_idle()

    def _paint_toolbar(self, background: str, foreground: str) -> None:
        widgets = [self._toolbar, *self._toolbar.winfo_children()]
        for widget in widgets:
            for option, value in (
                ("background", background),
                ("foreground", foreground),
                ("activebackground", background),
                ("selectcolor", background),
            ):
                try:
                    widget.configure(**{option: value})
                except tk.TclError:
                    continue
        # matplotlib recolours its icons for dark backgrounds when asked to reload them
        refresh = getattr(self._toolbar, "_set_image_for_button", None)
        buttons = getattr(self._toolbar, "_buttons", {})
        if callable(refresh) and isinstance(buttons, dict):
            for button in buttons.values():
                try:
                    refresh(button)
                except (tk.TclError, AttributeError, OSError):
                    break

    def _build_table(self) -> None:
        if self._table_body is not None:
            self._table_body.destroy()
        chart = self._chart
        body = ctk.CTkFrame(self._table_card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=12)
        self._table_body = body
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            body, text=s.CHART_CONSTANTS_TITLE, anchor="w", text_color=TEXT,
            font=ctk.CTkFont(FONT_FAMILY, 17, "bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 6))
        row = 1
        for slot in (SLOT_A, SLOT_B):
            name = chart.file_names.get(slot)
            if name is None:
                continue
            ctk.CTkLabel(
                body, text=f"{slot} · {name}", anchor="w", justify="left",
                text_color=_SLOT_COLOURS[slot], wraplength=_TABLE_WIDTH - 40,
                font=ctk.CTkFont(FONT_FAMILY, 14, "bold"),
            ).grid(row=row, column=0, columnspan=4, sticky="ew")
            row += 1

        head_font = ctk.CTkFont(FONT_FAMILY, 12, "bold")
        for col, (text, colour) in enumerate(
            (
                (s.CHART_COL_CONSTANT, MUTED),
                (SLOT_A, SERIES_A),
                (SLOT_B, SERIES_B),
                (s.CHART_COL_UNITS, MUTED),
            )
        ):
            ctk.CTkLabel(
                body, text=text.upper(), anchor="w" if col in (0, 3) else "e",
                text_color=colour, font=head_font,
            ).grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0), pady=(12, 2))
        row += 1

        regular = ctk.CTkFont(FONT_FAMILY, 15)
        bold = ctk.CTkFont(FONT_FAMILY, 15, "bold")
        small = ctk.CTkFont(FONT_FAMILY, 12)
        for const in chart.constants:
            value_colour = WARN if const.changed else TEXT
            value_font = bold if const.changed else regular
            ctk.CTkLabel(
                body, text=const.label, anchor="w", justify="left", text_color=TEXT,
                font=regular, wraplength=210,
            ).grid(row=row, column=0, sticky="ew", pady=(6, 0))
            for col, value in ((1, const.value_a), (2, const.value_b)):
                ctk.CTkLabel(
                    body, text=value, anchor="e", text_color=value_colour, font=value_font
                ).grid(row=row, column=col, sticky="ew", padx=(10, 0), pady=(6, 0))
            ctk.CTkLabel(
                body, text=const.units, anchor="w", text_color=MUTED, font=small
            ).grid(row=row, column=3, sticky="ew", padx=(10, 0), pady=(6, 0))
            ctk.CTkLabel(
                body, text=const.key_label, anchor="w", text_color=MUTED, font=small, height=18
            ).grid(row=row + 1, column=0, sticky="ew")
            row += 2

        if any(const.changed for const in chart.constants):
            ctk.CTkLabel(
                body, text=s.CHART_CHANGED_NOTE, anchor="w", justify="left", text_color=WARN,
                font=small, wraplength=_TABLE_WIDTH - 40,
            ).grid(row=row, column=0, columnspan=4, sticky="ew", pady=(14, 0))
