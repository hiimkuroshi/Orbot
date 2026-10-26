param([ValidatePattern('^[A-Za-z0-9.-]+$')][string]$OutputName)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$orbotPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $orbotPython)) {
    throw 'Create .venv and install requirements-dev.txt before building.'
}
$env:PYTHONDONTWRITEBYTECODE = '1'
if (-not $OutputName) {
    $releaseVersion = & $orbotPython -c 'from orbot import __version__; print(__version__)'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read the application version.' }
    $OutputName = 'Orbot-' + $releaseVersion
}
$env:PYINSTALLER_CONFIG_DIR = Join-Path $projectRoot 'build\cache\pyinstaller'
& $orbotPython scripts/make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }
$orbotBase = & $orbotPython -c 'import sys; print(sys.base_prefix)'
$orbotLicenses = Join-Path $projectRoot 'licenses'
New-Item -ItemType Directory -Path $orbotLicenses -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $orbotBase 'LICENSE.txt') -Destination (Join-Path $orbotLicenses 'Python-LICENSE.txt')
Copy-Item -LiteralPath (Join-Path $orbotBase 'tcl\tk8.6\license.terms') -Destination (Join-Path $orbotLicenses 'Tk-LICENSE.txt')
Copy-Item -LiteralPath '.venv\Lib\site-packages\websocket_client-1.9.2.dist-info\licenses\LICENSE' -Destination (Join-Path $orbotLicenses 'websocket-client-LICENSE.txt')
Copy-Item -LiteralPath '.venv\Lib\site-packages\pillow-13.0.0.dist-info\licenses\LICENSE' -Destination (Join-Path $orbotLicenses 'Pillow-LICENSE.txt')
$pyInstallerArguments = @(
    '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
    '--name', $OutputName, '--icon', (Join-Path $projectRoot 'orbot/icon.ico'),
    '--distpath', 'dist', '--workpath', 'build/work', '--specpath', 'build/spec',
    '--add-data', ((Join-Path $projectRoot 'orbot/engine.js') + ';orbot'),
    '--add-data', ((Join-Path $projectRoot 'orbot/capture.js') + ';orbot'),
    '--add-data', ((Join-Path $projectRoot 'orbot/icon.ico') + ';orbot'),
    '--add-data', ((Join-Path $projectRoot 'orbot/assets') + ';orbot/assets'),
    '--add-data', ((Join-Path $projectRoot 'LICENSE') + ';licenses'),
    '--add-data', ((Join-Path $projectRoot 'licenses') + ';licenses'),
    (Join-Path $projectRoot 'run_orbot.py')
)
& $orbotPython @pyInstallerArguments
if ($LASTEXITCODE -ne 0) { throw 'The Orbot build failed.' }
Copy-Item -LiteralPath 'docs\RELEASE.md' -Destination 'dist\README.md'
$orbotBinary = Join-Path 'dist' "$OutputName.exe"
Get-FileHash -LiteralPath $orbotBinary -Algorithm SHA256 | Select-Object -ExpandProperty Hash | Set-Content -LiteralPath "$orbotBinary.sha256" -Encoding ascii
Write-Output "[OK] $orbotBinary"
