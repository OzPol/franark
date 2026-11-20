[CmdletBinding()]
param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop or the documented Python environment is required.' }
    & docker compose --profile docs up --build -d
    if ($LASTEXITCODE -ne 0) { throw 'Franark did not start. Check Docker Desktop and the local configuration.' }
    $ready = $false
    for ($attempt=0; $attempt -lt 60; $attempt++) {
        try { $health = Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 3; if ($health.status -eq 'ok') { $ready=$true; break } } catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw 'The application health check did not become ready.' }
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765/portal' }
    Write-Output 'Assessment pilot: http://127.0.0.1:8765/portal'
    Write-Output 'System diagrams: http://127.0.0.1:8765/architecture'
    Write-Output 'Capabilities lab: http://127.0.0.1:8765/lab'
} finally { Pop-Location }
