"""Shared colours and fonts for the widgets (light, dark) tuples as customtkinter expects."""

from __future__ import annotations

ACCENT = ("#1F6AA5", "#3B8ED0")
MOTOR = ("#B45309", "#F59E0B")
WARN = ("#B91C1C", "#F87171")
OK = ("#15803D", "#4ADE80")
MUTED = ("gray40", "gray65")
CARD = ("gray97", "gray20")
CARD_BORDER = ("gray82", "gray28")
SELECTED_GROUP = ("#DBEAFE", "#1E3A5F")


def pick(pair: tuple[str, str], dark: bool) -> str:
    return pair[1] if dark else pair[0]
