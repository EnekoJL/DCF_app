"""Row of summary cards shown after a comparison."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import SummaryViewModel
from sevcon_diff.presentation.widgets.theme import CARD, CARD_BORDER, MOTOR, MUTED, OK, WARN


class _Card(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, master: Any, caption: str, value_size: int = 22) -> None:
        super().__init__(master, fg_color=CARD, border_color=CARD_BORDER, border_width=1)
        self.value = ctk.CTkLabel(
            self, text="—", anchor="w", font=ctk.CTkFont(size=value_size, weight="bold")
        )
        self.value.pack(fill="x", padx=14, pady=(8, 0))
        self.caption = ctk.CTkLabel(
            self, text=caption, anchor="w", text_color=MUTED, font=ctk.CTkFont(size=11)
        )
        self.caption.pack(fill="x", padx=14, pady=(0, 8))


class SummaryBar(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._relevant = _Card(self, s.CARD_RELEVANT)
        self._motor = _Card(self, s.CARD_MOTOR)
        self._noise = _Card(self, s.CARD_NOISE)
        self._checksum = _Card(self, s.CARD_CHECKSUM, value_size=14)
        self._firmware = _Card(self, s.CARD_FIRMWARE, value_size=13)
        self._default_color = self._relevant.value.cget("text_color")
        self._motor.value.configure(text_color=MOTOR)
        for col, (card, weight) in enumerate(
            ((self._relevant, 1), (self._motor, 1), (self._noise, 1), (self._checksum, 2),
             (self._firmware, 2))
        ):
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
            self.grid_columnconfigure(col, weight=weight, uniform="cards" if weight == 1 else "")

    def update_summary(self, summary: SummaryViewModel | None) -> None:
        if summary is None:
            for card in (self._relevant, self._motor, self._noise, self._checksum):
                card.value.configure(text="—")
            self._firmware.value.configure(text="")
            return
        self._relevant.value.configure(text=summary.relevant)
        self._motor.value.configure(text=f"★ {summary.motor}")
        self._noise.value.configure(text=summary.noise)
        self._checksum.value.configure(
            text=summary.checksum, text_color=WARN if summary.checksum_differs else OK
        )
        self._firmware.value.configure(
            text=summary.firmware,
            text_color=WARN if summary.firmware_mismatch else self._default_color,
        )
