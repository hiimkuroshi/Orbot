param([ValidatePattern('^[A-Za-z0-9.-]+$')][string]$OutputName)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$orbotPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $orbotPython)) {
    throw 'Create .venv and install requirements-lock.txt before building.'
}
$env:PYTHONDONTWRITEBYTECODE = '1'
$releaseVersion = & $orbotPython -c 'from orbot import __version__; print(__version__)'
if ($LASTEXITCODE -ne 0) { throw 'Cannot read the application version.' }
if (-not $OutputName) { $OutputName = 'Orbot-' + $releaseVersion }
$env:PYINSTALLER_CONFIG_DIR = Join-Path $projectRoot 'build\cache\pyinstaller'

# dist/ only holds the artifacts of this build.
foreach ($folder in @('dist', 'build\onedir', 'build\package')) {
    if (Test-Path -LiteralPath $folder) { Remove-Item -LiteralPath $folder -Recurse -Force }
}
New-Item -ItemType Directory -Path 'dist' | Out-Null

& $orbotPython scripts/make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }
$versionFile = Join-Path $projectRoot 'build\version_info.txt'
& $orbotPython scripts/version_info.py $versionFile | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Version resource generation failed.' }

$orbotBase = & $orbotPython -c 'import sys; print(sys.base_prefix)'
$orbotLicenses = Join-Path $projectRoot 'licenses'
New-Item -ItemType Directory -Path $orbotLicenses -Force | Out-Null
function Update-OrbotLicense([string]$Source, [string]$Name) {
    # Refresh a notice from the installed package; Python builds differ in what they ship.
    $target = Join-Path $orbotLicenses $Name
    if ($Source -and (Test-Path -LiteralPath $Source)) {
        Copy-Item -LiteralPath $Source -Destination $target
    } elseif (Test-Path -LiteralPath $target) {
        Write-Warning "Keeping the committed $Name; this Python installation has no copy."
    } else {
        throw "Missing license notice $Name."
    }
}
$tkLicense = Get-ChildItem -LiteralPath $orbotBase -Filter 'license.terms' -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Directory.Name -like 'tk*' } | Select-Object -First 1
Update-OrbotLicense (Join-Path $orbotBase 'LICENSE.txt') 'Python-LICENSE.txt'
Update-OrbotLicense $(if ($tkLicense) { $tkLicense.FullName } else { '' }) 'Tk-LICENSE.txt'
Update-OrbotLicense '.venv\Lib\site-packages\websocket_client-1.9.2.dist-info\licenses\LICENSE' 'websocket-client-LICENSE.txt'
Update-OrbotLicense '.venv\Lib\site-packages\pillow-13.0.0.dist-info\licenses\LICENSE' 'Pillow-LICENSE.txt'

$commonArguments = @(
    '-m', 'PyInstaller', '--noconfirm', '--windowed', '--noupx',
    '--icon', (Join-Path $projectRoot 'orbot/icon.ico'),
    '--version-file', $versionFile,
    '--workpath', 'build/work', '--specpath', 'build/spec',
    '--add-data', ((Join-Path $projectRoot 'orbot/engine.js') + ';orbot'),
    '--add-data', ((Join-Path $projectRoot 'orbot/capture.js') + ';orbot'),
    '--add-data', ((Join-Path $projectRoot 'orbot/icon.ico') + ';orbot'),
    '--add-data', ((Join-Path $projectRoot 'orbot/assets') + ';orbot/assets'),
    '--add-data', ((Join-Path $projectRoot 'LICENSE') + ';licenses'),
    '--add-data', ((Join-Path $projectRoot 'licenses') + ';licenses'),
    (Join-Path $projectRoot 'run_orbot.py')
)

# Recommended download: a folder app. It starts without unpacking itself to %TEMP%.
& $orbotPython @commonArguments --onedir --name 'Orbot' --distpath 'build/onedir'
if ($LASTEXITCODE -ne 0) { throw 'The Orbot folder build failed.' }
# Single-file EXE for people who prefer one download.
& $orbotPython @commonArguments --onefile --name $OutputName --distpath 'dist'
if ($LASTEXITCODE -ne 0) { throw 'The Orbot single-file build failed.' }

$packageName = "Orbot-$releaseVersion-windows-x64"
$stage = Join-Path $projectRoot "build\package\Orbot-$releaseVersion"
New-Item -ItemType Directory -Path $stage -Force | Out-Null
Copy-Item -Path 'build\onedir\Orbot\*' -Destination $stage -Recurse
Copy-Item -LiteralPath 'docs\RELEASE.md' -Destination (Join-Path $stage 'README.md')
Copy-Item -LiteralPath 'LICENSE' -Destination (Join-Path $stage 'LICENSE.txt')
Copy-Item -LiteralPath 'licenses' -Destination (Join-Path $stage 'licenses') -Recurse
Compress-Archive -LiteralPath $stage -DestinationPath "dist\$packageName.zip" -CompressionLevel Optimal

Copy-Item -LiteralPath 'docs\RELEASE.md' -Destination 'dist\README.md'
$artifacts = Get-ChildItem -LiteralPath 'dist' -File | Where-Object { $_.Extension -in '.exe', '.zip' } | Sort-Object Name
$sums = foreach ($artifact in $artifacts) {
    $hash = (Get-FileHash -LiteralPath $artifact.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $($artifact.Name)"
}
# LF line endings and no BOM, so `sha256sum -c SHA256SUMS.txt` also works.
[System.IO.File]::WriteAllText((Join-Path $projectRoot 'dist\SHA256SUMS.txt'), (($sums -join "`n") + "`n"))
foreach ($artifact in $artifacts) { Write-Output "[OK] dist\$($artifact.Name)" }
Write-Output '[OK] dist\SHA256SUMS.txt'

# Start both packaged apps (demo and normal) and require a clean exit.
foreach ($exe in @("dist\$OutputName.exe", 'build\onedir\Orbot\Orbot.exe')) {
    foreach ($mode in @('--demo --smoke-test', '--smoke-test')) {
        $process = Start-Process -FilePath $exe -ArgumentList $mode -PassThru
        $null = $process.Handle  # Keep the handle so the exit code stays readable.
        if (-not $process.WaitForExit(120000)) {
            $process.Kill()
            throw "$exe $mode did not exit."
        }
        if ($process.ExitCode -ne 0) { throw "$exe $mode exited with code $($process.ExitCode)." }
        Write-Output "[OK] $exe $mode"
    }
}
