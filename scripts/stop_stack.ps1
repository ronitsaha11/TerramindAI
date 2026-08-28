# Stops everything start_stack.ps1 launched.
#
#   powershell -ExecutionPolicy Bypass -File scripts\stop_stack.ps1
#
# Containers are left running by default so the database keeps its data and the
# next start is fast. Pass -Containers to stop them too.

param([switch]$Containers)

$Root = Split-Path -Parent $PSScriptRoot

# Only ever touches processes whose command line points at THIS repository.
# Matching on '*vite*' alone would kill unrelated dev servers on this machine.
function Stop-Matching {
    param([string]$ProcessName, [string]$Pattern, [string]$Label)
    $procs = Get-CimInstance Win32_Process -Filter "Name='$ProcessName'" |
             Where-Object { $_.CommandLine -like $Pattern -and $_.CommandLine -like "*TerramindAI*" }
    if (-not $procs) { Write-Host "  $Label - nothing running"; return }
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force
        Write-Host "  $Label - stopped PID $($p.ProcessId)" -ForegroundColor Yellow
    }
}

Write-Host "Stopping TerraMind stack..." -ForegroundColor Cyan
Stop-Matching -ProcessName "node.exe"   -Pattern '*vite*'    -Label "vite    "
Stop-Matching -ProcessName "python.exe" -Pattern '*uvicorn*' -Label "fastapi "
Stop-Matching -ProcessName "python.exe" -Pattern '*celery*'  -Label "celery  "

if ($Containers) {
    Set-Location $Root
    docker compose stop db redis | Out-Null
    Write-Host "  containers - stopped" -ForegroundColor Yellow
} else {
    Write-Host "  containers - left running (use -Containers to stop)"
}

Write-Host "Done." -ForegroundColor Green
