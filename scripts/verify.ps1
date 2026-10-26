$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$orbotPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$env:PYTHONDONTWRITEBYTECODE = '1'
function Assert-OrbotStep {
    param([string]$Name)
    if ($LASTEXITCODE -ne 0) { throw "$Name failed." }
}
& node --test tests/engine.test.cjs
Assert-OrbotStep 'Engine tests'
& $orbotPython -m unittest discover -s tests -p 'test_*.py' -v
Assert-OrbotStep 'CDP integration tests'
& $orbotPython scripts/gui_smoke.py
Assert-OrbotStep 'GUI smoke test'
& $orbotPython -m ruff check orbot tests scripts run_orbot.py
Assert-OrbotStep 'Lint'
& $orbotPython -m mypy orbot
Assert-OrbotStep 'Types'
& $orbotPython -m bandit -r orbot -ll
Assert-OrbotStep 'Security analysis'
Write-Output '[OK] All Orbot checks passed.'
