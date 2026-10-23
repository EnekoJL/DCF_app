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
from sevcon_diff.domain.diff_models import ChangeKind, DiffResult
from sevcon_diff.domain.ports import DcfReadError, ReportExporter
from sevcon_diff.infrastructure.dcf_parser import SevconDcfReader
from sevcon_diff.infrastructure.exporters.html_exporter import HtmlReportExporter
from sevcon_diff.infrastructure.exporters.pdf_exporter import PdfReportExporter
from sevcon_diff.infrastructure.rule_classifier import TomlNoiseFilter, TomlRuleClassifier


def build_compare_use_case() -> CompareDcfFiles:
    engine = DcfDiffEngine(TomlRuleClassifier(), TomlNoiseFilter())
    return CompareDcfFiles(SevconDcfReader(), engine)


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

    controller = CompareController(build_compare_use_case(), build_exporters())
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
    parser.add_argument("--all", action="store_true", help="incluye monitorización (ruido)")
    parser.add_argument("--motor-only", action="store_true", help="solo control de motor y límites")
    args = parser.parse_args(argv)
    if args.cli:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        return run_cli(args.cli[0], args.cli[1], args.all, args.motor_only)
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
