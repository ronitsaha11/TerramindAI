# Brings the full TerraMind stack up and verifies each layer before moving on.
#
#   powershell -ExecutionPolicy Bypass -File scripts\start_stack.ps1
#
# Containers: db (postgis) + redis. Everything else runs natively, matching how
# the project is developed today. Logs land next to the service that wrote them.

$ErrorActionPreference = "Stop"

$Root     = Split-Path -Parent $PSScriptRoot
$Backend  = Join-Path $Root "apps\backend"
$Frontend = Join-Path $Root "frontend"

function Wait-For {
    param(
        [string]$Name,
        [scriptblock]$Check,
        [int]$Attempts = 20,
        [int]$DelaySeconds = 2
    )
    for ($i = 0; $i -lt $Attempts; $i++) {
        Start-Sleep -Seconds $DelaySeconds
        try { if (& $Check) { Write-Host "    $Name ready" -ForegroundColor Green; return $true } } catch {}
    }
    Write-Host "    $Name FAILED to become ready" -ForegroundColor Red
    return $false
}

Write-Host "TerraMind AI - starting stack" -ForegroundColor Cyan

# 1. Containers -------------------------------------------------------------
Write-Host "[1/5] Containers (db, redis)..." -ForegroundColor Cyan
Set-Location $Root
docker compose up -d db redis | Out-Null
$dbReady = Wait-For -Name "postgres" -Check {
    docker exec terramindai-db-1 pg_isready -U terramind -q | Out-Null
    return ($LASTEXITCODE -eq 0)
}
if (-not $dbReady) { exit 1 }

# 2. Migrations -------------------------------------------------------------
Write-Host "[2/5] Database migrations..." -ForegroundColor Cyan
Set-Location $Backend
$env:PYTHONPATH = $Backend
& ".venv\Scripts\python.exe" -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { Write-Host "    migrations FAILED" -ForegroundColor Red; exit 1 }
Write-Host "    schema at head" -ForegroundColor Green

# 3. Celery -----------------------------------------------------------------
# --pool=solo is required on Windows; the default pool dies on billiard
# permission errors.
Write-Host "[3/5] Celery worker..." -ForegroundColor Cyan
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*celery*' -and $_.CommandLine -like '*TerramindAI*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m celery -A src.async_processing.celery_app worker -l info --pool=solo" `
    -WindowStyle Hidden -RedirectStandardOutput "celery.log" -RedirectStandardError "celery.err"
Write-Host "    worker launched (celery.log)" -ForegroundColor Green

# 4. API --------------------------------------------------------------------
Write-Host "[4/5] FastAPI..." -ForegroundColor Cyan
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*uvicorn*' -and $_.CommandLine -like '*TerramindAI*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn src.main:app --port 8000" `
    -WindowStyle Hidden -RedirectStandardOutput "fastapi.log" -RedirectStandardError "fastapi.err"
$apiReady = Wait-For -Name "api" -Check {
    (Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200
}
if (-not $apiReady) { Get-Content (Join-Path $Backend "fastapi.err") -Tail 30; exit 1 }

# 5. Frontend ---------------------------------------------------------------
# pnpm is a .cmd shim, so it must be launched through cmd.exe.
Write-Host "[5/5] Vite dev server..." -ForegroundColor Cyan
Set-Location $Frontend
# Scoped to this repo so unrelated Vite projects on this machine survive.
Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object { $_.CommandLine -like '*vite*' -and $_.CommandLine -like '*TerramindAI*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# --strictPort means a foreign listener on 5273 would fail opaquely. Name it.
$holder = Get-NetTCPConnection -LocalPort 5273 -State Listen -ErrorAction SilentlyContinue |
          Select-Object -First 1
if ($holder) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($holder.OwningProcess)" -ErrorAction SilentlyContinue
    if ($proc -and $proc.CommandLine -notlike "*TerramindAI*") {
        Write-Host "    port 5273 is held by another project:" -ForegroundColor Red
        Write-Host "      PID $($proc.ProcessId)  $($proc.CommandLine)" -ForegroundColor Red
        Write-Host "    Stop it, or change the port in this script." -ForegroundColor Red
        exit 1
    }
}
Start-Process -FilePath "cmd.exe" -ArgumentList "/c pnpm dev --port 5273 --strictPort" `
    -WindowStyle Hidden -RedirectStandardOutput "vite.out.log" -RedirectStandardError "vite.err.log"
$feReady = Wait-For -Name "frontend" -Check {
    (Invoke-WebRequest -Uri "http://localhost:5273" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200
}
if (-not $feReady) { Get-Content (Join-Path $Frontend "vite.err.log") -Tail 30; exit 1 }

Set-Location $Root
Write-Host ""
Write-Host "Stack is live:" -ForegroundColor Green
Write-Host "  frontend  http://localhost:5273"
Write-Host "  api docs  http://127.0.0.1:8000/docs"
Write-Host "  health    http://127.0.0.1:8000/api/v1/health"
Write-Host ""
Write-Host "Stop with: powershell -ExecutionPolicy Bypass -File scripts\stop_stack.ps1"
