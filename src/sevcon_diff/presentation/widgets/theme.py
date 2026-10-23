"""Shared colours and fonts for the widgets (light, dark) tuples as customtkinter expects."""

from __future__ import annotations

FONT_FAMILY = "Segoe UI"

ACCENT = ("#2563EB", "#3B82F6")
ACCENT_HOVER = ("#1D4ED8", "#2563EB")
WARN = ("#B91C1C", "#F87171")
WARN_BG = ("#FEF2F2", "#3B1D1F")
MUTED = ("#6B7280", "#9CA3AF")
TEXT = ("#111827", "#E5E7EB")
WINDOW = ("#F3F4F6", "#111318")
CARD = ("#FFFFFF", "#1A1D23")
CARD_BORDER = ("#E5E7EB", "#2A2E36")
CHIP = ("#EEF2F7", "#232730")
SECONDARY_HOVER = ("#E5E7EB", "#2A2E36")


def pick(pair: tuple[str, str], dark: bool) -> str:
    return pair[1] if dark else pair[0]
