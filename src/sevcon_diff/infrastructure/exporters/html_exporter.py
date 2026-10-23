"""Self-contained HTML report (Jinja2 template with inline CSS)."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from jinja2 import Environment, select_autoescape

from sevcon_diff import __version__
from sevcon_diff.domain.diff_models import DiffResult
from sevcon_diff.infrastructure.exporters.report_model import build_groups, generated_at

TEMPLATE_PACKAGE = "sevcon_diff.infrastructure.exporters"
TEMPLATE_NAME = "report.html.j2"


class HtmlReportExporter:
    """Implements ``ReportExporter``."""

    def __init__(self) -> None:
        source = (
            resources.files(TEMPLATE_PACKAGE)
            .joinpath("templates")
            .joinpath(TEMPLATE_NAME)
            .read_text(encoding="utf-8")
        )
        env = Environment(autoescape=select_autoescape(default=True, default_for_string=True))
        self._template = env.from_string(source)

    def render(self, result: DiffResult) -> str:
        return self._template.render(
            result=result,
            a=result.file_a,
            b=result.file_b,
            summary=result.summary,
            groups=build_groups(result),
            shown=len(result.changes),
            generated=generated_at(),
            version=__version__,
        )

    def export(self, result: DiffResult, path: Path) -> None:
        Path(path).write_text(self.render(result), encoding="utf-8")
