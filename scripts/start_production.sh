#!/usr/bin/env bash
# Production launcher script for Linux/macOS
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=========================================================="
echo "  CHAKRA AI AML INVESTIGATION SYSTEM - PRODUCTION LAUNCHER"
echo "  Statutory Compliance: PMLA 2002 §35A | RBI KYC 2026"
echo "=========================================================="

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please initialize venv."
    exit 1
fi

source venv/bin/activate

# Check models
if [ ! -f "models/v1/xgboost_classifier.pkl" ]; then
    echo "Training ML models..."
    python scripts/train_models.py
fi

# Launch backend
echo "[1/2] Starting FastAPI Backend on :8000..."
(cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

trap "kill $BACKEND_PID" EXIT

# Launch frontend
echo "[2/2] Starting React Investigator Dashboard on :3000..."
cd frontend
npm run preview -- --port 3000
