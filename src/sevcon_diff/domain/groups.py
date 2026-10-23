"""Functional groups used to organise parameter changes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FunctionalGroup:
    """A functional area of the controller (e.g. current loop). Defined in TOML."""

    id: str
    label: str
    motor_control: bool = False
    order: int = 999

    @property
    def display_label(self) -> str:
        return f"★ {self.label}" if self.motor_control else self.label
