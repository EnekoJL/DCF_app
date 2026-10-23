# Sevcon DCF Diff

Comparador de configuraciones (`.dcf`) del inversor **Sevcon Gen4 Size 6** para MotoStudent.
Carga dos ficheros guardados con DVT y muestra qué ha cambiado — en unidades físicas, agrupado por
área (datos base del motor, lazos de corriente/velocidad, límites, encoder, térmica…) y ocultando
por defecto los valores de monitorización que cambian en cada guardado.

## Instalación y uso (Windows)

1. Instalar Python 3.11 o superior desde python.org (marcar "Add to PATH").
2. Doble clic en `run_app.bat`. La primera vez crea `.venv-win` e instala dependencias.
3. Elegir **Archivo base (A)** y **Archivo nuevo (B)** → **Comparar**.

Desde consola: `python -m sevcon_diff --cli A.dcf B.dcf` imprime el diff agrupado.

## Desarrollo

Ver `CLAUDE.md` (comandos, convenciones), `docs/ARCHITECTURE.md` y `MEMORY.md` (estado y registro
de cambios). DCF de ejemplo en `data/originals/`; manuales y TFG/TFM en `docs/datasheets/`.
