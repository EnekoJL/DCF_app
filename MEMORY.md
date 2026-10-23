# MEMORY — Sevcon DCF Diff

Registro vivo del proyecto: cambios, problemas, decisiones e información útil.
Añadir entradas **arriba** dentro de cada sección, con fecha `AAAA-MM-DD`.
La arquitectura y el formato DCF no se duplican aquí: ver `CLAUDE.md`, `docs/ARCHITECTURE.md`
y `docs/sevcon_parameters.md`.

## Estado actual

- **v1 implementada** (2026-10-20): comparación + filtros + vista de detalle + export HTML/PDF +
  CLI de depuración. 128 tests en verde, `ruff` y `mypy --strict` limpios.
- GUI v1.1 revisada y aprobada por el usuario en Windows (2026-10-23).
- Tests de GUI en WSL: se ejecutan sobre WSLg (DISPLAY=:0) y abren una ventana real. Lanzarlos
  siempre con `timeout`.
- Git: remoto `origin` = https://github.com/EnekoJL/DCF_app.git. La rama local `master` sigue a
  `origin/main`. El 2026-10-23 se sobrescribió `main` (force push, decisión del usuario): antes
  contenía otro proyecto, "DCF calibration studio" (PySide6, commit `ae35bb3`), del que hay copia
  local en la rama `backup-calibration-studio`.

## Registro de cambios

- **2026-10-23** — Añadidos 3 DCF reales de Motorland (`Motorland_Carrera2_100..150_30`,
  `Motorland_Qualy1_120_40`, `Motorland_v7_45kW`) a `data/originals/` y `data/samples/`, y a
  `ALL_SAMPLES` en los tests. Se parsean bien y no tienen cambios sin clasificar. 131 tests en verde.
- **2026-10-23** — Rediseño de la GUI (petición: "más directo, profesional y moderno"):
  - Fuera el panel de detalle (derecha) y la barra de grupos (izquierda). Ahora hay una tabla
    única a ancho completo, agrupada por área y con columnas Parámetro · Antes · ▲/▼ · Después ·
    Unidad. Los bitfields salen como filas hijas.
  - Encima de la tabla: nº de cambios, chip de firmware, búsqueda, desplegable de área e
    interruptor "Otras áreas (N)", apagado por defecto. Debajo: línea de ayuda con el objeto y la
    descripción Sevcon de la fila seleccionada.
  - Checksum eliminado de la GUI, los informes y la CLI. La monitorización ya no se muestra ni se
    cuenta en la GUI (en la CLI sigue con `--all`). Quitado el botón "Analizar impacto".
  - Foco = grupos con `motor_control = true`. "Batería / potencia" pasa a "Límites de batería /
    potencia" y entra en el foco (order 85).
  - Informes HTML/PDF: sin Δ, checksum ni ruido; columnas Antes/Después.
  - **Problema encontrado:** cuelgue de la GUI. La etiqueta de ayuda reajustaba `wraplength`
    en su propio `<Configure>`, lo que provocaba un bucle infinito de redimensionado. Ahora se
    ajusta desde el `<Configure>` del marco de la tabla. **Regla:** nunca reconfigurar un widget
    desde su propio `<Configure>` si eso cambia su tamaño.
  - **Problema encontrado:** el atributo `self._options` en un widget pisa un método interno de
    tkinter (`TypeError: 'dict' object is not callable`). Evitar `_options`, `_w`, `_name`, etc.
- **2026-10-23** — Commit inicial (`93b3fa3`) con todo el proyecto, DCF y PDFs incluidos.
- **2026-10-23** — Reorganización de carpetas:
  - DCF originales de la raíz → `data/originals/` (idénticos a `data/samples/`).
  - `datasheet/` → `docs/datasheets/`.
  - Creado este `MEMORY.md`; referencias actualizadas en `CLAUDE.md`, `README.md` y
    `docs/sevcon_parameters.md`. Tests siguen en verde (128).
- **2026-10-20** — v1 completa (ver *Estado actual*). Copiada a Windows.

## Decisiones

- Ejecución en **Windows nativo** (`run_app.bat` crea `.venv-win`); desarrollo y tests en WSL.
- Monitorización/ruido y parámetros sin cambios: **nunca** se muestran ni se cuentan en la GUI.
- La comparación se centra en el control de motor y los límites de motor, batería y tensión.
  El resto queda tras el interruptor "Otras áreas".
- La GUI no muestra el checksum (`0x5620`): cambia con cualquier parámetro y no aporta nada.
- Extras de v1: export HTML/PDF y panel de detalle.
- UI en español (`presentation/strings_es.py`), código en inglés.
- Fuente de verdad de nombres/escalado/unidades: el propio DCF (`;SEVCONFIELD`), no el manual.

## Problemas y dudas abiertas

1. Perfil `0x2921`: valores `0xFFFF` (6553.5 %, 65535 rpm) probablemente significan
   "no configurado" — ¿mostrarlos como tal?
2. Ke `0x4641 sub 12` decodifica 0.0291 V/(rad/s) frente a 0.022 del TFG (RMS); probablemente
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
