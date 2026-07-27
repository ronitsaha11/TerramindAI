$ErrorActionPreference = "Continue"

Write-Host "Stopping TerraMind AI Infrastructure..." -ForegroundColor Yellow

Write-Host "--> Stopping FastAPI server..." -ForegroundColor Cyan
Stop-Process -Name "uvicorn" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

Write-Host "--> Stopping Celery Worker..." -ForegroundColor Cyan
Stop-Process -Name "celery" -Force -ErrorAction SilentlyContinue

Write-Host "--> Stopping Docker containers..." -ForegroundColor Cyan
docker-compose stop redis db

Write-Host "Services stopped successfully!" -ForegroundColor Green
