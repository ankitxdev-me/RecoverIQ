# RecoverIQ — Run Backend Server
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Starting RecoverIQ Backend (FastAPI on Port 8000)..." -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Error: Virtual environment not found. Please run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

$env:PYTHONPATH = "."
& ".\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
