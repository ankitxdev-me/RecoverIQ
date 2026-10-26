# RecoverIQ — Automated Windows Setup Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   RecoverIQ — AI Revenue Recovery Agent Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/4] Checking Python environment..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Error: Python was not found in PATH. Please install Python 3.11+." -ForegroundColor Red
    exit 1
}
$pyVer = python --version
Write-Host "Found: $pyVer" -ForegroundColor Green

# 2. Virtual Environment Setup
Write-Host "`n[2/4] Setting up Python virtual environment (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "Created .venv successfully." -ForegroundColor Green
} else {
    Write-Host ".venv already exists." -ForegroundColor Green
}

Write-Host "Installing backend Python dependencies..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r backend/requirements.txt
Write-Host "Backend dependencies installed successfully." -ForegroundColor Green

# 3. Frontend Setup
Write-Host "`n[3/4] Installing Frontend NPM packages..." -ForegroundColor Yellow
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "Error: Node.js was not found in PATH. Please install Node.js 18+." -ForegroundColor Red
    exit 1
}
Push-Location frontend
npm install
npm run build
Pop-Location
Write-Host "Frontend packages installed and built successfully." -ForegroundColor Green

# 4. Check Ollama Service
Write-Host "`n[4/4] Checking local Ollama service (qwen2.5:3b)..." -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    $modelFound = $resp.models | Where-Object { $_.name -like "*qwen2.5:3b*" }
    if ($modelFound) {
        Write-Host "Ollama service online with model 'qwen2.5:3b' ready!" -ForegroundColor Green
    } else {
        Write-Host "Notice: Ollama is running, but 'qwen2.5:3b' was not found. RecoverIQ will use its deterministic rule-based fallback until downloaded." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Notice: Ollama is currently offline at http://localhost:11434." -ForegroundColor Yellow
    Write-Host "RecoverIQ will run in deterministic fallback mode. Start Ollama anytime with: ollama serve" -ForegroundColor DarkGray
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "   Setup complete! Launch the app using:" -ForegroundColor Green
Write-Host "   .\run_backend.ps1   (starts FastAPI server on :8000)" -ForegroundColor White
Write-Host "   .\run_frontend.ps1  (starts Vite dashboard on :5173)" -ForegroundColor White
Write-Host "   or .\run_demo.ps1   (launches both concurrently)" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
