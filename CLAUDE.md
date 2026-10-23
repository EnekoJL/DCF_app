# CLAUDE.md — Sevcon DCF Diff

Herramienta de escritorio (Python + customtkinter) para comparar dos ficheros `.dcf` del inversor
**Sevcon Gen4 Size 6** (equipo MotoStudent) y mostrar las diferencias decodificadas a unidades
físicas y agrupadas por área funcional, con foco en el control del motor.

Leer antes de tocar nada:
- `docs/ARCHITECTURE.md` — capas, puertos, flujo, puntos de extensión.
- `docs/sevcon_parameters.md` — formato DCF, mapa de objetos, ruido, referencia de motor.
- `MEMORY.md` — registro vivo: estado, cambios, decisiones, dudas abiertas. **Actualizarlo** al
  terminar cada cambio o al descubrir un problema/dato relevante.

## Reglas de arquitectura (no negociables)

- Capas: `domain` ← `application` ← `infrastructure` / `presentation`. `domain` y `application`
  **no importan** tkinter, customtkinter, jinja2, fpdf ni hacen I/O.
- Solo `src/sevcon_diff/__main__.py` instancia clases concretas e inyecta dependencias.
- Dependencias entre capas a través de `typing.Protocol` de `domain/ports.py`.
- Clasificación de grupos y ruido **solo** en los TOML de `infrastructure/knowledge/`; nunca índices
  hardcodeados en código Python (salvo tests).
- Modelos de dominio: `@dataclass(frozen=True, slots=True)`; colecciones como `tuple`/`Mapping`.
- La fuente de verdad de nombres/escalado/unidades es el propio DCF (`;SEVCONFIELD`), no el manual.
- Un valor que no se pueda decodificar se muestra en raw; el parser **nunca** lanza por una línea rara.

## Convenciones

- Código, identificadores, docstrings y comentarios en **inglés**. Textos visibles en **español**,
  centralizados en `presentation/strings_es.py`.
- Type hints completos (`mypy --strict` limpio), `ruff` limpio, líneas ≤ 100.
- Docstrings breves solo donde aportan; nada de comentarios obvios.
- Tests con `pytest`; los de dominio/aplicación/infraestructura corren sin display (WSL headless).
  Fixtures sobre `data/samples/*.dcf` (no modificar esas copias; originales en `data/originals/`).
- Objetivo de ejecución: **Windows nativo** (`run_app.bat`). Desarrollo y tests en WSL.

## Comandos

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
pytest                       # tests
ruff check src tests         # lint
mypy                         # tipos (config en pyproject)
python -m sevcon_diff --cli data/samples/Primer_mapa_fk1.dcf data/samples/Motorland_Carrera1_100_30.dcf
python -m sevcon_diff        # GUI (en Windows: run_app.bat)
```

## Estado

- v1: comparación + filtros + vista de detalle + export HTML/PDF + CLI de depuración.
- Futuro: `ChangeImpactAnalyzer` (agente IA que explica el efecto esperado de los cambios).
