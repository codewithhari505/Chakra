# PowerShell Production Runner for AML Investigation System
# Starts FastAPI backend and React frontend concurrently

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  CHAKRA AI AML INVESTIGATION SYSTEM - PRODUCTION LAUNCHER" -ForegroundColor Cyan
Write-Host "  Statutory Compliance: PMLA 2002 §35A | RBI KYC 2026" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$ROOT_DIR = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT_DIR

# 1. Check Virtualenv
$VENV_PYTHON = Join-Path $ROOT_DIR "venv\Scripts\python.exe"
if (-Not (Test-Path $VENV_PYTHON)) {
    Write-Error "Virtualenv not found at $VENV_PYTHON. Please set up Python environment first."
    exit 1
}

# 2. Check Trained Models
$MODEL_FILE = Join-Path $ROOT_DIR "models\v1\xgboost_classifier.pkl"
if (-Not (Test-Path $MODEL_FILE)) {
    Write-Warning "Trained models not detected. Running training pipeline..."
    & $VENV_PYTHON scripts/train_models.py
}

# 3. Start Backend in Background Process
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$backendJob = Start-Process -FilePath $VENV_PYTHON -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory (Join-Path $ROOT_DIR "backend") -PassThru

# 4. Start Frontend
Write-Host "[2/2] Starting React Investigator Dashboard on http://localhost:3000..." -ForegroundColor Green
Set-Location (Join-Path $ROOT_DIR "frontend")
npm run preview -- --port 3000

# Cleanup on exit
if ($backendJob -and -not $backendJob.HasExited) {
    Stop-Process -Id $backendJob.Id -Force
}
