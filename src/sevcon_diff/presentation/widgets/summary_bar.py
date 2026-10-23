"""Toolbar above the table: headline counter, firmware chip, search, area filter, scope switch."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import GroupOption, SummaryViewModel
from sevcon_diff.presentation.widgets.theme import (
    ACCENT,
    CARD,
    CARD_BORDER,
    CHIP,
    FONT_FAMILY,
    MUTED,
    SECONDARY_HOVER,
    TEXT,
    WARN,
    WARN_BG,
)


def _option_label(option: GroupOption) -> str:
    return f"{option.label}  ({option.count})"


class SummaryBar(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self,
        master: Any,
        on_group: Callable[[str], None],
        on_search: Callable[[str], None],
        on_include_other: Callable[[bool], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_group = on_group
        self._area_ids: dict[str, str] = {}
        self._search_job: str | None = None
        self.grid_columnconfigure(2, weight=1)

        self._headline = ctk.CTkLabel(
            self, text=s.HEADLINE_EMPTY, text_color=TEXT,
            font=ctk.CTkFont(FONT_FAMILY, 20, "bold"),
        )
        self._headline.grid(row=0, column=0, sticky="w")
        self._scope = ctk.CTkLabel(
            self, text="", text_color=MUTED, font=ctk.CTkFont(FONT_FAMILY, 13)
        )
        self._scope.grid(row=0, column=1, sticky="w", padx=(8, 12))
        self._firmware = ctk.CTkLabel(
            self, text="", corner_radius=8, fg_color="transparent", text_color=MUTED,
            font=ctk.CTkFont(FONT_FAMILY, 11, "bold"), height=24,
        )
        self._firmware.grid(row=0, column=2, sticky="w")

        self._search = ctk.CTkEntry(
            self, placeholder_text=s.SEARCH_PLACEHOLDER, width=230, height=32, corner_radius=8,
            fg_color=CARD, border_color=CARD_BORDER, font=ctk.CTkFont(FONT_FAMILY, 12),
        )
        self._search.grid(row=0, column=3, padx=(12, 8))
        self._search.bind("<KeyRelease>", lambda _e: self._debounce_search(on_search))
        self._area = ctk.CTkOptionMenu(
            self, values=[s.GROUP_ALL], width=260, height=32, corner_radius=8,
            fg_color=CHIP, button_color=CHIP, button_hover_color=SECONDARY_HOVER,
            text_color=TEXT, dynamic_resizing=False, font=ctk.CTkFont(FONT_FAMILY, 12),
            dropdown_font=ctk.CTkFont(FONT_FAMILY, 12), command=self._area_chosen,
        )
        self._area.grid(row=0, column=4, padx=(0, 12))
        self._other = ctk.CTkSwitch(
            self, text=s.OTHER_AREAS.format(count=0), progress_color=ACCENT,
            font=ctk.CTkFont(FONT_FAMILY, 12), text_color=TEXT,
        )
        self._other.configure(command=lambda: on_include_other(bool(self._other.get())))
        self._other.grid(row=0, column=5)
        self.set_enabled(False)

    def set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for widget in (self._search, self._area, self._other):
            widget.configure(state=state)

    def _debounce_search(self, on_search: Callable[[str], None]) -> None:
        if self._search_job is not None:
            self.after_cancel(self._search_job)
        self._search_job = self.after(200, lambda: on_search(self._search.get()))

    def _area_chosen(self, label: str) -> None:
        group_id = self._area_ids.get(label)
        if group_id is not None:
            self._on_group(group_id)

    def update_summary(self, summary: SummaryViewModel | None) -> None:
        if summary is None:
            self._headline.configure(text=s.HEADLINE_EMPTY)
            self._scope.configure(text="")
            self._firmware.configure(text="", fg_color="transparent")
            self.set_enabled(False)
            return
        self.set_enabled(True)
        self._headline.configure(text=summary.headline)
        self._scope.configure(text=summary.scope)
        self._firmware.configure(
            text=f"  {summary.firmware}  ",
            text_color=WARN if summary.firmware_mismatch else MUTED,
            fg_color=WARN_BG if summary.firmware_mismatch else CHIP,
        )
        self._other.configure(text=s.OTHER_AREAS.format(count=summary.other_count))

    def set_groups(self, options: list[GroupOption], selected: str) -> None:
        self._area_ids = {_option_label(o): o.id for o in options}
        self._area.configure(values=list(self._area_ids))
        current = next((label for label, gid in self._area_ids.items() if gid == selected), None)
        self._area.set(current or s.GROUP_ALL)
