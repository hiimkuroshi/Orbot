@echo off
cd /d "%~dp0"
if exist "dist\Orbot-0.2.0.exe" (
    start "" "dist\Orbot-0.2.0.exe"
    exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
    set "PYTHONDONTWRITEBYTECODE=1"
    start "" ".venv\Scripts\pythonw.exe" "run_orbot.py"
    exit /b 0
)
echo Run scripts\build.ps1 or install requirements in .venv first.
pause
