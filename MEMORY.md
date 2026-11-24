# MEMORY — Sevcon DCF Diff

Registro vivo del proyecto: cambios, problemas, decisiones e información útil.
Añadir entradas **arriba** dentro de cada sección, con fecha `AAAA-MM-DD`.
La arquitectura y el formato DCF no se duplican aquí: ver `CLAUDE.md`, `docs/ARCHITECTURE.md`
y `docs/sevcon_parameters.md`.

## Estado actual

- **v1 implementada** (2026-10-20): comparación + filtros + vista de detalle + export HTML/PDF +
  CLI de depuración. 128 tests en verde, `ruff` y `mypy --strict` limpios.
- 2026-11-24: v1.2 (curva par–rpm). 12 DCF de ejemplo y 187 tests en verde. Repositorio público, preparado para que
  lo use un profesor (README con clonado/ZIP, `.gitattributes` con CRLF para `.bat`).
- GUI v1.1 revisada y aprobada por el usuario en Windows (2026-10-23).
- Tests de GUI en WSL: se ejecutan sobre WSLg (DISPLAY=:0) y abren una ventana real. Lanzarlos
  siempre con `timeout`.
- Git: remoto `origin` = https://github.com/EnekoJL/DCF_app.git. La rama local `main` sigue a
  `origin/main`. El 2026-10-23 se sobrescribió `main` (force push, decisión del usuario): antes
  contenía otro proyecto, "DCF calibration studio" (PySide6, commit `ae35bb3`), del que hay copia
  local en la rama `backup-calibration-studio`.
- Clones: desarrollo en WSL (`~/workdir/CFD_Sevcon`), copia de ejecución sincronizada por rsync
  (`C:\Z-Eneko\CFD_Sevcon`, sin `.git`) y un clon de pruebas del usuario
  (`C:\Z-Eneko\test\DCF_app`, autor git "Enekin").

## Registro de cambios

- **2026-11-24** — Ventana "Curva par–rpm" (v1.2) implementada y verificada: 187 tests (sin
  saltar ninguno de GUI), `ruff`/`mypy` limpios. Comando de depuración: `--profile FICHERO...`.
  `run_app.bat` reinstala dependencias si cambia `pyproject.toml` (copia en
  `.venv-win\pyproject.stamp`): la primera ejecución en Windows tras el cambio necesita Internet
  para instalar matplotlib. El dibujo está en `widgets/torque_plot.py` (sin Tk, renderizable a PNG).
  Lectura de los mapas reales: `Carrera1_100_30` = 100 Nm hasta 2850 rpm y luego ~30 kW
  constantes; `v7_45kW` ≈ 45 kW; `Primer` mantiene 78.9 Nm planos hasta 6500 rpm (53.7 kW).
  Más dudas de datos: `DCF_10_04-v8_Circe` y `2MapasLimitados` tienen npp 5 con Ls/Ke de Circe
  (npp 4). En `Carrera2`, 6076 = 150 Nm, pero el mapa principal se queda en 100 (solo el
  secundario llega a 150). La escala de 6076 (0.001 Nm/bit) es correcta. Diseño:
  - Qué objetos se leen está en `knowledge/motor_profile.toml`: mapas 4611h (principal) y
    4615h (secundario, opcional), línea de par de pico 6076h y constantes 4641 subA/12/5/2 y
    6076. El punto k del mapa está en sub 2k-1 (par, 0.0625 Nm) y sub 2k (rpm).
  - Modelos en `domain/motor_profile.py`. El extractor y el caso de uso `LoadMotorProfiles`
    están en `application/`; la ventana usa matplotlib, que solo se importa en `presentation`.
  - En cada punto se anota la potencia teórica P = T·ω en kW, con una curva de potencia
    opcional. A y B se superponen (A azul, B naranja).
  - Datos comprobados: en `Motorland_v7_45kW` salen unos 45 kW (cuadra con el nombre). El
    mapa secundario solo está configurado en `Carrera2` (150 Nm).
  - **Problema encontrado:** Circe (FW antiguo) tiene un mapa de 314 Nm con 6076 = 20 Nm. El
    tope efectivo de par no está claro; por eso no se calcula una "curva efectiva".
- **2026-11-24** — 5 DCF nuevos del usuario (commit `8dcb33f`, hecho desde Windows):
  `Segundo_mapa_fk1_Temperatura`, `2MapasLimitadosPara30-06_PunoRespuestaRapida`,
  `Motorland_v2_MapaCambiado`, `Motorland_v3_MapaCambiado_encoder_reinsaw_Ajustado` y
  `Motorland_v4_UMA`. Copiados a `data/samples/` y añadidos a `ALL_SAMPLES`. La prueba de
  "sin cambios sin clasificar" ahora recorre todos los pares consecutivos de `ALL_SAMPLES`.
  Comprobado a mano: en los 66 pares posibles de los 12 DCF no queda nada en "other".
  144 tests en verde.
  - **Problema encontrado:** desde la red del usuario, los push por HTTPS de unos 75 KB fallan
    con `HTTP 408`. Los de pocos KB sí pasan. Ni `http.postBuffer` ni HTTP/1.1 lo arreglan,
    así que es la red (proxy/VPN). SSH a GitHub responde, pero la clave no está dada de alta.
- **2026-11-24** — Preparado para entregarlo a un profesor. Comprobado desde un clon limpio:
  instalación, 131 tests, `ruff`, `mypy` y CLI correctos.
  - Añadido `.gitattributes`: `*.bat` con CRLF (un `.bat` en LF puede fallar en `cmd`), y `*.dcf`
    y `*.pdf` sin conversión.
  - README: cómo clonar o descargar el ZIP, `run_app.bat --cli` en Windows y una sección para
    Linux/macOS (`python3-tk`).
  - **Duda abierta:** el repositorio es público e incluye los manuales de Sevcon/DVT y los PDF
    de un TFG y un TFM de terceros. Falta decidir si se pueden redistribuir.
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
