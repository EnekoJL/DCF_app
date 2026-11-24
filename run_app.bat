@echo off
REM Lanzador para Windows nativo: crea el venv la primera vez, reinstala dependencias cuando
REM cambia pyproject.toml (copia en .venv-win\pyproject.stamp) e inicia la GUI.
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
)

fc /b pyproject.toml ".venv-win\pyproject.stamp" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    ".venv-win\Scripts\python.exe" -m pip install -e .
    if errorlevel 1 (
        echo No se pudieron instalar las dependencias. Revisa la conexion a Internet.
        pause
    ) else (
        copy /y pyproject.toml ".venv-win\pyproject.stamp" >nul
    )
)

".venv-win\Scripts\python.exe" -m sevcon_diff %*
endlocal
