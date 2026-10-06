# Demo rapide du pipeline (Windows PowerShell)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    python -m venv .venv
    .\.venv\Scripts\pip.exe install -r requirements.txt
}

if (-not (Test-Path .\.env)) {
    Copy-Item .\.env.example .\.env
}

Write-Host "==> generate + validate" -ForegroundColor Cyan
.\.venv\Scripts\python.exe scripts\cli.py pipeline
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> simulate drift on SW-PROD-01" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path configs\running | Out-Null
Copy-Item configs\expected\*.cfg configs\running\ -Force
Add-Content configs\running\SW-PROD-01.cfg "`ninterface Loopback99`n description DRIFT-TEST`n"

Write-Host "==> drift detect" -ForegroundColor Cyan
.\.venv\Scripts\python.exe scripts\cli.py drift
Write-Host "Done. See reports\" -ForegroundColor Green
