@echo off
REM Lanzador para Windows nativo: crea el venv la primera vez e inicia la GUI.
setlocal
cd /d "%~dp0"

if not exist ".venv-win\Scripts\python.exe" (
    echo Creando entorno virtual...
    py -3 -m venv .venv-win || python -m venv .venv-win
    if errorlevel 1 (
        echo No se encontro Python 3.11+ en Windows. Instalalo desde python.org.
        pause
        exit /b 1
    )
    ".venv-win\Scripts\python.exe" -m pip install --upgrade pip
    ".venv-win\Scripts\python.exe" -m pip install -e .
)

".venv-win\Scripts\python.exe" -m sevcon_diff %*
endlocal
