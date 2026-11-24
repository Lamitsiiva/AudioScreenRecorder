@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python est requis sur le PC qui construit l'executable.
    echo Installez Python puis relancez ce script.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Echec de l'installation des dependances.
    pause
    exit /b 1
)

python -m PyInstaller --noconfirm --clean --noconsole --onefile --name AudioRecorder app.py
if errorlevel 1 (
    echo.
    echo Echec de la creation de l'executable.
    pause
    exit /b 1
)

echo.
echo Executable cree : %~dp0dist\AudioRecorder.exe
echo Copiez ce fichier sur le PC cible. Python n'y est pas necessaire.
pause
