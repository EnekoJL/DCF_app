# Sevcon DCF Diff

Comparador de configuraciones (`.dcf`) del inversor **Sevcon Gen4 Size 6** para MotoStudent.
Carga dos ficheros guardados con DVT y muestra qué ha cambiado — en unidades físicas, agrupado por
área (datos base del motor, lazos de corriente/velocidad, límites, encoder, térmica…) y ocultando
por defecto los valores de monitorización que cambian en cada guardado.

## Obtener el código

```bash
git clone https://github.com/EnekoJL/DCF_app.git
```

(o en GitHub: **Code → Download ZIP** y descomprimir).

## Instalación y uso (Windows)

1. Instalar Python 3.11 o superior desde python.org (marcar "Add to PATH"; dejar marcado
   "tcl/tk and IDLE", que viene por defecto).
2. Doble clic en `run_app.bat`. La primera vez crea `.venv-win` e instala dependencias
   (necesita conexión a Internet; tarda un minuto).
3. Elegir **Archivo base (A)** y **Archivo nuevo (B)** → **Comparar**. Hay DCF de ejemplo en
   `data/samples/`.

Desde consola (`cmd`, en la carpeta del proyecto) se puede usar el modo texto:

```bat
run_app.bat --cli data\samples\Primer_mapa_fk1.dcf data\samples\Motorland_Carrera1_100_30.dcf
```

## Instalación y uso (Linux / macOS)

Requiere Python 3.11+ con Tk (en Debian/Ubuntu: `sudo apt install python3-venv python3-tk`).

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
python -m sevcon_diff                      # GUI
python -m sevcon_diff --cli data/samples/Primer_mapa_fk1.dcf data/samples/Motorland_Carrera1_100_30.dcf
```

Tests: `pip install -e ".[dev]" && pytest`.

## Desarrollo

Ver `CLAUDE.md` (comandos, convenciones), `docs/ARCHITECTURE.md` y `MEMORY.md` (estado y registro
de cambios). DCF de ejemplo en `data/originals/`; manuales y TFG/TFM en `docs/datasheets/`.
