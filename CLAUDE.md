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
  **no importan** tkinter, customtkinter, matplotlib, jinja2, fpdf ni hacen I/O.
- Solo `src/sevcon_diff/__main__.py` instancia clases concretas e inyecta dependencias.
- Dependencias entre capas a través de `typing.Protocol` de `domain/ports.py`.
- Clasificación de grupos, ruido y perfil del motor (mapas par–rpm, constantes) **solo** en los
  TOML de `infrastructure/knowledge/`; nunca índices hardcodeados en código Python (salvo tests).
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
  Los tests de GUI abren ventanas reales en WSLg: lanzar siempre con `timeout`.
- Tras cada cambio, sincronizar con la copia de Windows (`rsync`, ver `MEMORY.md` → Información útil).
- Si cambian las dependencias de `pyproject.toml`, `run_app.bat` debe reinstalarlas en `.venv-win`.

## Comandos

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
timeout 300 pytest           # tests (los de GUI abren ventana en WSLg)
ruff check src tests         # lint
mypy                         # tipos (config en pyproject)
python -m sevcon_diff --cli data/samples/Primer_mapa_fk1.dcf data/samples/Motorland_Carrera1_100_30.dcf
python -m sevcon_diff --profile data/samples/Motorland_v7_45kW.dcf   # curva par–rpm + constantes
python -m sevcon_diff        # GUI (en Windows: run_app.bat)
```

## Estado

- v1: comparación + filtros + export HTML/PDF + CLI de depuración.
- v1.1 (2026-10-23): GUI rediseñada — tabla única a ancho completo (antes/después), solo áreas
  de foco por defecto, sin checksum ni monitorización.
- v1.2 (2026-11-24): botón "Curva par–rpm" — mapas 4611h/4615h de A y B superpuestos,
  potencia teórica P = T·ω en cada punto, constantes Ls/Ke/npp/Is max/par de pico. Nueva
  dependencia: matplotlib. 12 DCF de ejemplo en `data/samples/`.
- Repo público en GitHub (`EnekoJL/DCF_app`), pensado para que un profesor lo clone y ejecute.
- Futuro: `ChangeImpactAnalyzer` (agente IA que explica el efecto esperado de los cambios).
