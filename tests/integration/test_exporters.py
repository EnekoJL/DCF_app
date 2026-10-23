from __future__ import annotations

from pathlib import Path

import pytest

from conftest import CIRCE_V8, PRIMER
from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.application.filters import DiffQuery
from sevcon_diff.domain.diff_models import DiffResult
from sevcon_diff.infrastructure.exporters.html_exporter import HtmlReportExporter
from sevcon_diff.infrastructure.exporters.pdf_exporter import PdfReportExporter, sanitize


@pytest.fixture(scope="module")
def result(compare: CompareDcfFiles) -> DiffResult:
    return DiffQuery().apply_to(compare.execute(CIRCE_V8, PRIMER))


def test_html_export(result: DiffResult, tmp_path: Path) -> None:
    path = tmp_path / "report.html"
    HtmlReportExporter().export(result, path)
    html = path.read_text(encoding="utf-8")
    assert html.startswith("<!DOCTYPE html>")
    assert "Datos base del motor" in html and "Checksum" not in html
    assert "4641h sub2" in html
    assert "<link" not in html and "<script" not in html  # self-contained
    assert html.index("Datos base del motor") < html.index("CAN / PDO")


def test_pdf_export(result: DiffResult, tmp_path: Path) -> None:
    path = tmp_path / "report.pdf"
    PdfReportExporter().export(result, path)
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 2000


def test_exports_with_no_changes(result: DiffResult, tmp_path: Path) -> None:
    empty = result.with_changes(())
    HtmlReportExporter().export(empty, tmp_path / "e.html")
    PdfReportExporter().export(empty, tmp_path / "e.pdf")
    assert (tmp_path / "e.pdf").read_bytes().startswith(b"%PDF")


def test_sanitize_is_latin1() -> None:
    text = sanitize("\u2605 \u0394 \u2192 \u00b5H \u203a \u2014 \u26a0 \u6f22")
    text.encode("latin-1")
    assert text.startswith("* d -> uH > - !")
