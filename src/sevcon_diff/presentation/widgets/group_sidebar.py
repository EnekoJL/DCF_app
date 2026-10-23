"""Left sidebar: group list with counters, search box and filter switches."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import GroupItem
from sevcon_diff.presentation.widgets.theme import MOTOR, MUTED, SELECTED_GROUP


class GroupSidebar(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self,
        master: Any,
        on_group: Callable[[str], None],
        on_search: Callable[[str], None],
        on_show_noise: Callable[[bool], None],
        on_motor_only: Callable[[bool], None],
    ) -> None:
        super().__init__(master, corner_radius=0)
        self._on_group = on_group
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._signature: tuple[str, ...] = ()
        self._search_job: str | None = None
        self._font = ctk.CTkFont(size=12)
        self._font_selected = ctk.CTkFont(size=12, weight="bold")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text=s.GROUPS_TITLE, anchor="w", font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.grid(row=1, column=0, sticky="nsew", padx=4)
        self._list.grid_columnconfigure(0, weight=1)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
        filters.grid_columnconfigure(0, weight=1)
        self._search = ctk.CTkEntry(filters, placeholder_text=s.SEARCH_PLACEHOLDER)
        self._search.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._search.bind("<KeyRelease>", lambda _e: self._debounce_search(on_search))
        self._noise = ctk.CTkSwitch(filters, text=s.SHOW_NOISE)
        self._noise.configure(command=lambda: on_show_noise(bool(self._noise.get())))
        self._noise.grid(row=1, column=0, sticky="w", pady=2)
        self._motor = ctk.CTkSwitch(filters, text=s.MOTOR_ONLY)
        self._motor.configure(command=lambda: on_motor_only(bool(self._motor.get())))
        self._motor.grid(row=2, column=0, sticky="w", pady=2)

    def _debounce_search(self, on_search: Callable[[str], None]) -> None:
        if self._search_job is not None:
            self.after_cancel(self._search_job)
        self._search_job = self.after(200, lambda: on_search(self._search.get()))

    def set_groups(self, items: list[GroupItem], selected: str) -> None:
        signature = tuple(i.id for i in items)
        if signature != self._signature:
            for button in self._buttons.values():
                button.destroy()
            self._buttons = {}
            for row, item in enumerate(items):
                button = ctk.CTkButton(
                    self._list,
                    anchor="w",
                    height=30,
                    fg_color="transparent",
                    hover_color=SELECTED_GROUP,
                    command=lambda gid=item.id: self._on_group(gid),
                )
                button.grid(row=row, column=0, sticky="ew", pady=1)
                self._buttons[item.id] = button
            self._signature = signature
        for item in items:
            button = self._buttons[item.id]
            color = MOTOR if item.motor_control else ("gray10", "gray90")
            if item.count == 0 and item.id != selected:
                color = MUTED
            button.configure(
                text=f"{item.label}   {item.count}",
                text_color=color,
                fg_color=SELECTED_GROUP if item.id == selected else "transparent",
                font=self._font_selected if item.id == selected else self._font,
            )
