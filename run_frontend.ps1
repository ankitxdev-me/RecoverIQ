# RecoverIQ — Run Frontend Dashboard
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Starting RecoverIQ Frontend Dashboard (Vite on Port 5173)..." -ForegroundColor Cyan
Write-Host "   URL: http://localhost:5173" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

Push-Location frontend
npm run dev
Pop-Location
