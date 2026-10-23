# MEMORY — Sevcon DCF Diff

Registro vivo del proyecto: cambios, problemas, decisiones e información útil.
Añadir entradas **arriba** dentro de cada sección, con fecha `AAAA-MM-DD`.
La arquitectura y el formato DCF no se duplican aquí: ver `CLAUDE.md`, `docs/ARCHITECTURE.md`
y `docs/sevcon_parameters.md`.

## Estado actual

- **v1 implementada** (2026-10-20): comparación + filtros + vista de detalle + export HTML/PDF +
  CLI de depuración. 128 tests en verde, `ruff` y `mypy --strict` limpios.
- Pendiente: revisión visual de la GUI por el usuario en Windows.
- Git: commit inicial `93b3fa3` en `master` (2026-10-23). Sin remoto configurado.

## Registro de cambios

- **2026-10-23** — Commit inicial (`93b3fa3`) con todo el proyecto, DCF y PDFs incluidos.
- **2026-10-23** — Reorganización de carpetas:
  - DCF originales de la raíz → `data/originals/` (idénticos a `data/samples/`).
  - `datasheet/` → `docs/datasheets/`.
  - Creado este `MEMORY.md`; referencias actualizadas en `CLAUDE.md`, `README.md` y
    `docs/sevcon_parameters.md`. Tests siguen en verde (128).
- **2026-10-20** — v1 completa (ver *Estado actual*). Copiada a Windows.

## Decisiones

- Ejecución en **Windows nativo** (`run_app.bat` crea `.venv-win`); desarrollo y tests en WSL.
- Valores de monitorización/ruido **ocultos por defecto**.
- Extras de v1: export HTML/PDF y panel de detalle.
- UI en español (`presentation/strings_es.py`), código en inglés.
- Fuente de verdad de nombres/escalado/unidades: el propio DCF (`;SEVCONFIELD`), no el manual.

## Problemas y dudas abiertas

1. Perfil `0x2921`: valores `0xFFFF` (6553.5 %, 65535 rpm) probablemente significan
   "no configurado" — ¿mostrarlos como tal?
2. Checksum `0x5620 = 0x0000` en Motorland: seguramente "no calculado", no "distinto".
3. Ke `0x4641 sub 12` decodifica 0.0291 V/(rad/s) frente a 0.022 del TFG (RMS); probablemente
   el DCF da valor de pico. Sin verificar.

## Roadmap

- **Agente de impacto IA** (`ChangeImpactAnalyzer`, en `infrastructure/ai/`, Claude API):
  explicar el efecto esperado de aplicar el diff usando `docs/sevcon_parameters.md` como contexto.
  Aplazado por decisión del usuario.

## Información útil

- Copia de Windows: `C:\Z-Eneko\CFD_Sevcon` (`/mnt/c/Z-Eneko/CFD_Sevcon`). Sincronizar tras
  cada cambio:
  ```bash
  rsync -rt --exclude='.venv/' --exclude='.venv-win/' --exclude='__pycache__/' \
    --exclude='.pytest_cache/' --exclude='.mypy_cache/' --exclude='.ruff_cache/' \
    --exclude='*.egg-info/' ./ /mnt/c/Z-Eneko/CFD_Sevcon/
  ```
  Nunca borrar `.venv-win/` en el lado Windows.
- PDFs de referencia en `docs/datasheets/`. El más útil: TFG Castelló Díez (Gen4 Size 6 +
  motor ENGIRO en MotoStudent). El manual Gen4 de 2009 está desfasado respecto al firmware.
  En WSL no hay poppler: extraer texto de los PDF con Python.

## Estructura de carpetas

```
CFD_Sevcon/
├── CLAUDE.md, MEMORY.md, README.md, pyproject.toml, run_app.bat
├── data/
│   ├── originals/     # DCF originales guardados con DVT (no tocar)
│   └── samples/       # copias usadas como fixtures de tests (no tocar)
├── docs/
│   ├── ARCHITECTURE.md, sevcon_parameters.md
│   └── datasheets/    # manuales Sevcon/DVT, TFG, TFM (PDF)
├── src/sevcon_diff/   # domain / application / infrastructure / presentation
└── tests/             # unit / integration
```
