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
4. **Curva par–rpm** (junto a Comparar) abre la gráfica del mapa par–velocidad guardado en el DCF
   (4611h y, si está configurado, el secundario 4615h) con la potencia teórica en kW en cada punto
   y las constantes del motor (Ls, Ke, pares de polos…). Funciona con un solo fichero; con A y B
   superpone las dos curvas. La casilla "Mostrar curva de potencia" añade la potencia en un eje
   secundario.

`run_app.bat` reinstala las dependencias automáticamente cuando cambia `pyproject.toml` (p. ej. al
actualizar el código y aparecer una librería nueva como matplotlib).

Desde consola (`cmd`, en la carpeta del proyecto) se puede usar el modo texto:

```bat
run_app.bat --cli data\samples\Primer_mapa_fk1.dcf data\samples\Motorland_Carrera1_100_30.dcf
run_app.bat --profile data\samples\Motorland_v7_45kW.dcf
```

`--profile FICHERO [FICHERO ...]` imprime los puntos de cada mapa (rpm, Nm, kW), la potencia máxima
y las constantes del motor.

## Instalación y uso (Linux / macOS)

Requiere Python 3.11+ con Tk (en Debian/Ubuntu: `sudo apt install python3-venv python3-tk`).

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
python -m sevcon_diff                      # GUI
python -m sevcon_diff --cli data/samples/Primer_mapa_fk1.dcf data/samples/Motorland_Carrera1_100_30.dcf
python -m sevcon_diff --profile data/samples/Motorland_v7_45kW.dcf   # curva par-rpm en texto
```

Tests: `pip install -e ".[dev]" && pytest`.

## Desarrollo

Ver `CLAUDE.md` (comandos, convenciones), `docs/ARCHITECTURE.md` y `MEMORY.md` (estado y registro
de cambios). DCF de ejemplo en `data/originals/`; manuales y TFG/TFM en `docs/datasheets/`.
