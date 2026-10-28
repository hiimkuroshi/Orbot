@echo off
cd /d "%~dp0"
set "ORBOT_EXE="
for %%F in ("dist\Orbot-*.exe") do set "ORBOT_EXE=%%~fF"
if defined ORBOT_EXE (
    start "" "%ORBOT_EXE%"
    exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
    set "PYTHONDONTWRITEBYTECODE=1"
    start "" ".venv\Scripts\pythonw.exe" "run_orbot.py"
    exit /b 0
)
echo Run scripts\build.ps1 or install requirements-lock.txt in .venv first.
pause
