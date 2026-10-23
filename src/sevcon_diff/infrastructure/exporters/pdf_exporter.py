"""PDF report with fpdf2 (pure Python; core Helvetica font, so text is latin-1 only)."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

from sevcon_diff import __version__
from sevcon_diff.domain.diff_models import DiffResult, FileSummary
from sevcon_diff.infrastructure.exporters.report_model import (
    ReportGroup,
    build_groups,
    generated_at,
)

FONT = "Helvetica"
_REPLACEMENTS = {
    "\u2605": "*",  # star
    "\u0394": "d",  # Delta
    "\u2192": "->",
    "\u2190": "<-",
    "\u21c4": "<->",
    "\u00b5": "u",  # micro
    "\u203a": ">",
    "\u2039": "<",
    "\u2014": "-",
    "\u2013": "-",
    "\u2026": "...",
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u26a0": "!",  # warning sign
    "\u00b7": "-",
    "\u2264": "<=",
    "\u2265": ">=",
}
_COLUMNS = ("Objeto", "Parámetro", "Valor A", "Valor B", "d", "Unidad")
_COL_WIDTHS = (24, 101, 42, 42, 36, 22)
_MOTOR_RGB = (180, 83, 9)
_HEADER_RGB = (238, 241, 245)
_MUTED_RGB = (107, 114, 128)


def sanitize(text: str) -> str:
    """Make ``text`` printable with the latin-1 core fonts."""
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


class _ReportPdf(FPDF):
    title_text = ""

    def footer(self) -> None:
        self.set_y(-10)
        self.set_font(FONT, size=7)
        self.set_text_color(*_MUTED_RGB)
        self.cell(0, 5, sanitize(f"{self.title_text} - pág. {self.page_no()}/{{nb}}"), align="C")


class PdfReportExporter:
    """Implements ``ReportExporter``: landscape A4, one table per functional group."""

    def export(self, result: DiffResult, path: Path) -> None:
        pdf = _ReportPdf(orientation="L", unit="mm", format="A4")
        pdf.title_text = f"Sevcon DCF Diff v{__version__}"
        pdf.set_auto_page_break(auto=True, margin=14)
        pdf.set_margins(10, 10, 10)
        pdf.add_page()
        self._header(pdf, result)
        groups = build_groups(result)
        if not groups:
            pdf.set_font(FONT, "I", 10)
            pdf.cell(0, 8, sanitize("No hay diferencias que mostrar con los filtros actuales."))
        for group in groups:
            self._group(pdf, group)
        pdf.output(str(path))

    def _header(self, pdf: FPDF, result: DiffResult) -> None:
        pdf.set_font(FONT, "B", 15)
        pdf.cell(0, 8, sanitize("Comparación de configuración Sevcon Gen4"), new_x="LMARGIN",
                 new_y="NEXT")
        pdf.set_font(FONT, size=8)
        pdf.set_text_color(*_MUTED_RGB)
        pdf.cell(0, 5, sanitize(f"Generado el {generated_at()}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        for tag, label, info in (
            ("A", "Archivo base", result.file_a),
            ("B", "Archivo nuevo", result.file_b),
        ):
            self._file_line(pdf, tag, label, info)
        s = result.summary
        pdf.ln(1)
        pdf.set_font(FONT, "B", 9)
        pdf.cell(
            0,
            5,
            sanitize(
                f"Cambios relevantes: {s.relevant}   ·   ★ Control de motor: {s.motor_control}"
                f"   ·   Monitorización (ruido): {s.noise}   ·   Mostrados: {len(result.changes)}"
                f"   ·   Checksum: {'difiere' if result.checksum_differs else 'igual'}"
            ),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        if result.firmware_mismatch:
            pdf.set_text_color(185, 28, 28)
            pdf.cell(
                0,
                5,
                sanitize(
                    f"⚠ La revisión de firmware difiere ({result.file_a.revision_number} → "
                    f"{result.file_b.revision_number})."
                ),
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    @staticmethod
    def _file_line(pdf: FPDF, tag: str, label: str, info: FileSummary) -> None:
        pdf.set_font(FONT, "B", 9)
        pdf.cell(42, 5, sanitize(f"{tag} · {label}:"))
        pdf.set_font(FONT, size=9)
        pdf.multi_cell(
            0,
            5,
            sanitize(
                f"{info.display_name}  ·  modificado {info.modification_date} "
                f"{info.modification_time}  ·  producto {info.product_number or '—'}  ·  "
                f"firmware {info.revision_number or '—'}  ·  checksum {info.checksum or '—'}"
            ),
            new_x="LMARGIN",
            new_y="NEXT",
        )

    @staticmethod
    def _group(pdf: FPDF, group: ReportGroup) -> None:
        if pdf.will_page_break(20):
            pdf.add_page()
        pdf.ln(2)
        pdf.set_font(FONT, "B", 11)
        if group.motor_control:
            pdf.set_text_color(*_MOTOR_RGB)
        star = "★ " if group.motor_control else ""
        pdf.cell(0, 7, sanitize(f"{star}{group.label} ({len(group.rows)})"), new_x="LMARGIN",
                 new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(FONT, size=8)
        heading = FontFace(emphasis="BOLD", fill_color=_HEADER_RGB)
        with pdf.table(
            col_widths=_COL_WIDTHS,
            width=sum(_COL_WIDTHS),
            headings_style=heading,
            line_height=4.2,
            padding=1,
            first_row_as_headings=True,
        ) as table:
            header = table.row()
            for title in _COLUMNS:
                header.cell(sanitize(title))
            for row in group.rows:
                name = f"{row.parent} > {row.name}" if row.parent else row.name
                tags = [row.kind_label] if row.kind != "modified" else []
                if row.out_of_limits:
                    tags.append("fuera de límites")
                if row.is_noise:
                    tags.append(f"ruido: {row.noise_reason}")
                if tags:
                    name += f"  [{', '.join(tags)}]"
                if row.bits:
                    name += "\n" + "\n".join(f"  - {b}" for b in row.bits)
                cells = table.row()
                for value in (row.key, name, row.value_a, row.value_b, row.delta, row.units):
                    cells.cell(sanitize(value))
