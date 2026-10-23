"""Right panel with every detail of the selected change."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import DetailViewModel
from sevcon_diff.presentation.widgets.theme import CARD, CARD_BORDER, MOTOR, MUTED, WARN

_WRAP = 300


class DetailPanel(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, master: Any) -> None:
        super().__init__(master, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._body = ctk.CTkScrollableFrame(self, corner_radius=0, label_text=s.DETAIL_TITLE)
        self._body.grid(row=0, column=0, sticky="nsew")
        self._body.grid_columnconfigure(0, weight=1)
        self._title_font = ctk.CTkFont(size=15, weight="bold")
        self._section_font = ctk.CTkFont(size=12, weight="bold")
        self._small_font = ctk.CTkFont(size=11)
        self._mono_font = ctk.CTkFont(family="Consolas", size=12)
        self.show(None)

    def _clear(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()

    def _add_label(self, text: str, row: int, **kwargs: Any) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            self._body, text=text, anchor="w", justify="left", wraplength=_WRAP, **kwargs
        )
        label.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 2))
        return label

    def show(self, detail: DetailViewModel | None) -> None:
        self._clear()
        if detail is None:
            self._add_label(s.DETAIL_EMPTY, 0, text_color=MUTED).grid_configure(pady=20)
            return
        row = 0
        self._add_label(
            detail.title, row, font=self._title_font,
            text_color=MOTOR if detail.motor_control else None,
        ).grid_configure(pady=(8, 0))
        row += 1
        self._add_label(detail.subtitle, row, text_color=MUTED, font=self._small_font)
        row += 1
        for warning in detail.warnings:
            box = ctk.CTkLabel(
                self._body, text=warning, anchor="w", justify="left", wraplength=_WRAP,
                text_color=WARN, fg_color=CARD, corner_radius=6,
            )
            box.grid(row=row, column=0, sticky="ew", padx=10, pady=(6, 0), ipadx=6, ipady=4)
            row += 1

        fields = ctk.CTkFrame(self._body, fg_color=CARD, border_color=CARD_BORDER, border_width=1)
        fields.grid(row=row, column=0, sticky="ew", padx=10, pady=10)
        fields.grid_columnconfigure(1, weight=1)
        for index, (name, value) in enumerate(detail.fields):
            ctk.CTkLabel(
                fields, text=name, anchor="nw", text_color=MUTED, font=self._small_font
            ).grid(row=index, column=0, sticky="nw", padx=(10, 8), pady=1)
            ctk.CTkLabel(
                fields, text=value, anchor="w", justify="left", wraplength=_WRAP - 120,
                font=self._mono_font,
            ).grid(row=index, column=1, sticky="ew", padx=(0, 10), pady=1)
        row += 1

        if detail.bits:
            self._add_label(s.DETAIL_BITS, row, font=self._section_font)
            row += 1
            bits = ctk.CTkFrame(self._body, fg_color=CARD, border_color=CARD_BORDER, border_width=1)
            bits.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 10))
            bits.grid_columnconfigure(0, weight=1)
            for index, bit in enumerate(detail.bits):
                ctk.CTkLabel(
                    bits, text=f"{bit.name}\n   {bit.value_a}  →  {bit.value_b}", anchor="w",
                    justify="left", wraplength=_WRAP - 20, font=self._small_font,
                ).grid(row=index, column=0, sticky="ew", padx=10, pady=2)
            row += 1

        self._add_label(s.DETAIL_DESCRIPTION, row, font=self._section_font)
        row += 1
        self._add_label(detail.description, row, font=self._small_font)
