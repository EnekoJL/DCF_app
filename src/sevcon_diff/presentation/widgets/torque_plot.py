"""Draws the torque-speed chart on a matplotlib ``Figure``.

No Tk here (and no pyplot), so the same drawing renders headless to a PNG for checks and tests.
"""

from __future__ import annotations

from collections.abc import Sequence

from matplotlib import font_manager, rcParams
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.transforms import blended_transform_factory

from sevcon_diff.domain.motor_profile import LineStyle
from sevcon_diff.presentation import strings_es as s
from sevcon_diff.presentation.view_models import SLOT_A, MotorChartViewModel
from sevcon_diff.presentation.widgets.theme import (
    CARD,
    CARD_BORDER,
    FONT_FAMILY,
    MUTED,
    SERIES_A,
    SERIES_B,
    TEXT,
    pick,
)

_LINESTYLES = {LineStyle.SOLID: "-", LineStyle.DASHED: "--"}
_ANNOTATION_FONT = 11
_TICK_FONT = 12.5
_LABEL_FONT = 14.5
_LEGEND_FONT = 12.5
_HEADROOM = 1.15
_fonts_ready = False


def _use_app_font() -> None:
    """Prefer the app font when installed (Windows); fall back silently elsewhere."""
    global _fonts_ready
    if _fonts_ready:
        return
    _fonts_ready = True
    installed = {font.name for font in font_manager.fontManager.ttflist}
    if FONT_FAMILY in installed:
        rcParams["font.sans-serif"] = [FONT_FAMILY, *rcParams["font.sans-serif"]]


def slot_colour(slot: str, dark: bool) -> str:
    return pick(SERIES_A if slot == SLOT_A else SERIES_B, dark)


def _style_axes(ax: Axes, background: str, text: str, muted: str, grid: str) -> None:
    ax.set_facecolor(background)
    for spine in ax.spines.values():
        spine.set_color(grid)
    ax.tick_params(colors=muted, labelsize=_TICK_FONT)
    ax.xaxis.label.set_color(text)
    ax.yaxis.label.set_color(text)


def _upper(values: Sequence[float]) -> float:
    top = max(values, default=0.0)
    return top * _HEADROOM if top > 0 else 1.0


def draw_torque_chart(
    fig: Figure, chart: MotorChartViewModel, *, show_power: bool = False, dark: bool = False
) -> None:
    """(Re)draw ``chart`` on ``fig``: maps with kW per point, torque caps, optional power."""
    _use_app_font()
    fig.clear()
    fig.set_layout_engine("constrained")
    background, text = pick(CARD, dark), pick(TEXT, dark)
    muted, grid = pick(MUTED, dark), pick(CARD_BORDER, dark)
    fig.set_facecolor(background)
    ax = fig.add_subplot()
    _style_axes(ax, background, text, muted, grid)
    ax.set_xlabel(s.CHART_AXIS_SPEED, fontsize=_LABEL_FONT)
    ax.set_ylabel(s.CHART_AXIS_TORQUE, fontsize=_LABEL_FONT)
    ax.grid(True, color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    if chart.empty:
        ax.text(
            0.5, 0.5, s.CHART_EMPTY, transform=ax.transAxes, ha="center", va="center",
            color=muted, fontsize=_LABEL_FONT,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return

    handles: list[Artist] = []
    # a point shared by two maps of the same file (same rpm and kW) is labelled only once
    labelled: set[tuple[str, float, str]] = set()
    for series in chart.series:
        colour = slot_colour(series.slot, dark)
        (line,) = ax.plot(
            series.speeds, series.torques, color=colour, linestyle=_LINESTYLES[series.style],
            linewidth=2.8, marker="o", markersize=8, markerfacecolor=colour,
            markeredgecolor=background, markeredgewidth=1.5, label=series.legend, zorder=3,
        )
        handles.append(line)
        if not show_power:
            continue
        # kW per point only with the power view; A above the points, B below.
        above = series.slot == SLOT_A
        for speed, torque, label in zip(
            series.speeds, series.torques, series.annotations, strict=True
        ):
            if label and (series.slot, speed, label) not in labelled:
                labelled.add((series.slot, speed, label))
                ax.annotate(
                    label, (speed, torque), xytext=(0, 10 if above else -11),
                    textcoords="offset points", ha="center", va="bottom" if above else "top",
                    fontsize=_ANNOTATION_FONT, color=colour, zorder=4,
                )

    ref_transform = blended_transform_factory(ax.transAxes, ax.transData)
    for ref in chart.references:
        colour = slot_colour(ref.slot, dark)
        ax.axhline(ref.torque_nm, color=colour, linestyle=":", linewidth=1, alpha=0.8, zorder=2)
        ax.text(
            0.995, ref.torque_nm, ref.text, transform=ref_transform, ha="right",
            va="bottom" if ref.slot == SLOT_A else "top", fontsize=_ANNOTATION_FONT,
            color=colour, alpha=0.9,
        )

    torques = [t for series in chart.series for t in series.torques]
    torques.extend(ref.torque_nm for ref in chart.references)
    ax.set_ylim(0, _upper(torques))
    speeds = [v for series in chart.series for v in series.speeds]
    ax.set_xlim(0, max(speeds, default=0.0) * 1.04 or 1.0)

    if show_power:
        power_ax = ax.twinx()
        _style_axes(power_ax, background, text, muted, grid)
        power_ax.patch.set_visible(False)
        power_ax.set_ylabel(s.CHART_AXIS_POWER, fontsize=_LABEL_FONT)
        for series in chart.series:
            (line,) = power_ax.plot(
                series.speeds, series.powers_kw, color=slot_colour(series.slot, dark),
                linestyle=_LINESTYLES[series.style], linewidth=1.8, alpha=0.5,
                label=series.power_legend, zorder=1,
            )
            handles.append(line)
        power_ax.set_ylim(0, _upper([p for series in chart.series for p in series.powers_kw]))

    fig.legend(
        handles=handles, loc="outside lower center", ncols=2 if len(handles) > 2 else 1,
        fontsize=_LEGEND_FONT, frameon=False, labelcolor=text, handlelength=4,
    )
