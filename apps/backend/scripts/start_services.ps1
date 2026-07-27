$ErrorActionPreference = "Stop"

Write-Host "Starting TerraMind AI Infrastructure..." -ForegroundColor Green

# Step 1: Start Redis and PostGIS using Docker Compose
Write-Host "--> Starting Docker containers..." -ForegroundColor Cyan
docker-compose up -d redis db

# Wait a moment for DB to initialize
Start-Sleep -Seconds 3

# Step 2: Set up environment for the scripts
$env:PYTHONPATH = (Get-Item .).FullName

# Step 3: Run Alembic migrations to ensure DB is up to date (optional, skipping for smoke test unless required)
# Write-Host "--> Running DB migrations..." -ForegroundColor Cyan
# .venv\Scripts\alembic upgrade head

# Step 4: Start Celery Worker in the background
Write-Host "--> Starting Celery Worker..." -ForegroundColor Cyan
# Start process hidden/no new window, redirect output
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m celery -A src.async_processing.celery_app worker -l info --pool=solo" -WindowStyle Hidden -RedirectStandardOutput "celery.log" -RedirectStandardError "celery.err"

# Step 5: Start FastAPI in the background
Write-Host "--> Starting FastAPI server..." -ForegroundColor Cyan
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn src.main:app --port 8000" -WindowStyle Hidden -RedirectStandardOutput "fastapi.log" -RedirectStandardError "fastapi.err"

Write-Host "--> Waiting for FastAPI to become healthy (timeout 30s)..." -ForegroundColor Cyan
$healthy = $false
for ($i=0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -Method GET
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        # ignore errors and retry
    }
}

if (-not $healthy) {
    Write-Host "ERROR: FastAPI failed to start or become healthy in time." -ForegroundColor Red
    exit 1
}

Write-Host "Services started successfully!" -ForegroundColor Green
Write-Host "You can now run: python scripts/smoke_test.py" -ForegroundColor Yellow
