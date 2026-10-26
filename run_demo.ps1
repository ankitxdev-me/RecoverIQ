# RecoverIQ — Master Launch Demo Script (Windows PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   RecoverIQ — AI Revenue Recovery Agent Demo Launcher" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Backend in separate window
Write-Host "`nStarting FastAPI backend server in new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "`$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000 --reload"

# 2. Start Frontend in current window
Write-Host "Starting Vite React frontend in current window..." -ForegroundColor Yellow
Write-Host "`nOpening RecoverIQ Dashboard: http://localhost:5173" -ForegroundColor Green
Write-Host "API Swagger Documentation: http://localhost:8000/docs" -ForegroundColor DarkGray
Write-Host "`nPress Ctrl+C at any time to stop the frontend." -ForegroundColor DarkGray

Push-Location frontend
npm run dev
Pop-Location
