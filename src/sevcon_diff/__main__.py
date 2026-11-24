"""Composition root: the only module that wires concrete classes together."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from sevcon_diff import __version__
from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.application.diff_engine import DcfDiffEngine
from sevcon_diff.application.filters import DiffQuery
from sevcon_diff.application.motor_profile import LoadMotorProfiles, MotorProfileExtractor
from sevcon_diff.application.value_decoder import ValueDecoder
from sevcon_diff.domain.diff_models import ChangeKind, DiffResult
from sevcon_diff.domain.motor_profile import MotorProfile
from sevcon_diff.domain.ports import DcfReadError, ReportExporter
from sevcon_diff.infrastructure.dcf_parser import SevconDcfReader
from sevcon_diff.infrastructure.exporters.html_exporter import HtmlReportExporter
from sevcon_diff.infrastructure.exporters.pdf_exporter import PdfReportExporter
from sevcon_diff.infrastructure.motor_profile_loader import load_motor_profile_spec
from sevcon_diff.infrastructure.rule_classifier import TomlNoiseFilter, TomlRuleClassifier


def build_compare_use_case() -> CompareDcfFiles:
    engine = DcfDiffEngine(TomlRuleClassifier(), TomlNoiseFilter())
    return CompareDcfFiles(SevconDcfReader(), engine)


def build_profile_use_case() -> LoadMotorProfiles:
    extractor = MotorProfileExtractor(load_motor_profile_spec(), ValueDecoder())
    return LoadMotorProfiles(SevconDcfReader(), extractor)


def build_exporters() -> dict[str, ReportExporter]:
    return {"html": HtmlReportExporter(), "pdf": PdfReportExporter()}


def print_diff(result: DiffResult, query: DiffQuery, out: TextIO) -> None:
    """Plain-text grouped diff (debugging aid and future agent input)."""
    a, b = result.file_a, result.file_b
    out.write(f"A: {a.path}  ({a.modification_date} {a.modification_time})\n")
    out.write(f"B: {b.path}  ({b.modification_date} {b.modification_time})\n")
    if result.firmware_mismatch:
        out.write(f"!! Firmware distinto: {a.revision_number} -> {b.revision_number}\n")
    s = result.summary
    out.write(f"Cambios: {s.relevant} ({s.motor_control} en control de motor y límites)\n")
    filtered = query.apply_to(result)
    for group, changes in filtered.grouped():
        out.write(f"\n== {group.display_label} ({len(changes)}) ==\n")
        for c in changes:
            old = c.old.display if c.old else "(no existe)"
            new = c.new.display if c.new else "(no existe)"
            line = f"  {c.key.section:<10} {c.full_name}: {old} -> {new}"
            if c.units:
                line += f" {c.units}"
            if c.delta_display:
                line += f"  [d {c.delta_display}]"
            if c.kind is not ChangeKind.MODIFIED:
                line += f"  <{c.kind.value}>"
            if c.is_noise:
                line += f"  (ruido: {c.noise_reason})"
            out.write(line + "\n")
            for bit in c.bit_changes:
                out.write(f"      · {bit.name}: {bit.old_display} -> {bit.new_display}\n")


def print_profile(profile: MotorProfile, out: TextIO) -> None:
    """Plain-text torque-speed maps (with theoretical power) and motor constants."""
    out.write(f"== {profile.display_name} ==\n")
    if not profile.curves:
        out.write("  (sin mapa par-rpm)\n")
    for curve in profile.curves:
        out.write(f"\n  {curve.label}\n")
        out.write(f"  {'rpm':>8} {'Nm':>9} {'kW':>7}\n")
        for point in curve.points:
            out.write(
                f"  {point.speed_rpm:>8.0f} {point.torque_nm:>9.3f} {point.power_kw:>7.1f}\n"
            )
        peak = curve.peak_power
        if peak is not None:
            out.write(
                f"  Potencia máx: {peak.power_kw:.1f} kW a {peak.speed_rpm:.0f} rpm"
                f" ({peak.torque_nm:.3f} Nm)\n"
            )
    if profile.references:
        out.write("\n  Referencias:\n")
        for ref in profile.references:
            out.write(f"    {ref.label}: {ref.torque_nm:g} Nm\n")
    if profile.constants:
        out.write("\n  Constantes del motor:\n")
        for const in profile.constants:
            value = const.value.display if const.value is not None else "(no existe)"
            units = f" {const.units}" if const.units else ""
            out.write(f"    {const.label} [{const.key.label}]: {value}{units}\n")
    out.write("\n")


def run_profile_cli(paths: Sequence[Path]) -> int:
    try:
        profiles = build_profile_use_case().execute(paths)
    except DcfReadError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for profile in profiles:
        print_profile(profile, sys.stdout)
    return 0


def run_cli(path_a: Path, path_b: Path, show_all: bool, motor_only: bool) -> int:
    try:
        result = build_compare_use_case().execute(path_a, path_b)
    except DcfReadError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    print_diff(result, DiffQuery(show_noise=show_all, motor_only=motor_only), sys.stdout)
    return 0


def run_gui() -> int:
    from sevcon_diff.presentation.app import launch
    from sevcon_diff.presentation.presenter import CompareController

    controller = CompareController(
        build_compare_use_case(), build_exporters(), build_profile_use_case()
    )
    launch(controller)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sevcon-diff", description="Comparador de ficheros DCF Sevcon Gen4"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--cli", nargs=2, metavar=("A", "B"), type=Path, help="imprime el diff en consola"
    )
    parser.add_argument(
        "--profile", nargs="+", metavar="FILE", type=Path,
        help="imprime la curva par-rpm (con potencia) y las constantes del motor",
    )
    parser.add_argument("--all", action="store_true", help="incluye monitorización (ruido)")
    parser.add_argument("--motor-only", action="store_true", help="solo control de motor y límites")
    args = parser.parse_args(argv)
    if (args.cli or args.profile) and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if args.profile:
        return run_profile_cli(args.profile)
    if args.cli:
        return run_cli(args.cli[0], args.cli[1], args.all, args.motor_only)
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
