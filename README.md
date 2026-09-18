# AI-Powered Anti-Money-Laundering (AML) Investigation System

A modular, explainable, end-to-end system for detecting suspicious financial transactions using supervised ML, anomaly detection, graph analytics, and an investigator dashboard.

> **Disclaimer:** This is an academic/prototype system built for demonstration purposes using entirely synthetic data. It does not constitute legal or financial advice. Model outputs identify patterns for investigator review — they do not declare guilt.

---

## Architecture Overview

```
Transaction Sources
        ↓
Data Processing & Cleaning
        ↓
Feature Engineering
        ↓
┌───────────────────────────────────┐
│  Supervised ML  │ Anomaly │ Graph │
│  (RF / XGBoost) │  Forest │ (NX)  │
└───────────────────────────────────┘
        ↓
Risk Scoring Engine
        ↓
Explainability Layer (SHAP)
        ↓
FastAPI Backend  ←→  PostgreSQL
        ↓
React Investigator Dashboard
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+, JavaScript |
| Data | Pandas, NumPy |
| ML | Scikit-learn, XGBoost |
| Anomaly | Isolation Forest, Autoencoder (optional) |
| Graph | NetworkX |
| Backend | FastAPI, Uvicorn, SQLAlchemy |
| Database | PostgreSQL (SQLite for local dev) |
| Frontend | React, Tailwind CSS, Recharts / Plotly |
| Serialization | Joblib |
| Explainability | SHAP (optional) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL 15+ (or SQLite for local dev)
- Git

### 1. Create a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

```powershell
# Windows
Copy-Item .env.example .env
# Edit .env with your database credentials
```

```bash
# Linux / macOS
cp .env.example .env
```

### 4. Initialize the Database

```bash
python scripts/seed_database.py
```

### 5. Generate Synthetic Data

```bash
python scripts/generate_data.py
```

### 6. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Verify Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "models_loaded": false
}
```

### 8. API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

---

## Development Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Project setup, skeleton, health API | ✅ Complete |
| 2 | Synthetic data generator & AML typologies | ✅ Complete |
| 3 | Data preprocessing pipeline | ✅ Complete |
| 4 | Feature engineering | ✅ Complete |
| 5 | Rule-based AML detection & RBI 2026 KYC | ✅ Complete |
| 6 | Random Forest model | 🔄 Next |
| 7 | XGBoost model | ⏳ Pending |
| 8 | Isolation Forest anomaly detection | ⏳ Pending |
| 9 | Graph analysis | ⏳ Pending |
| 10 | Risk scoring engine | ⏳ Pending |
| 11 | Explainability layer | ⏳ Pending |
| 12 | FastAPI full implementation | ⏳ Pending |
| 13 | PostgreSQL integration | ⏳ Pending |
| 14 | React dashboard | ⏳ Pending |
| 15 | Investigation workflow | ⏳ Pending |
| 16 | Testing suite | ⏳ Pending |
| 17 | Deployment | ⏳ Pending |

---

## Reproducibility

A fixed random seed (`RANDOM_SEED=42`) is used throughout. Set it in `.env` to ensure identical results across data generation, model training, and evaluation.

---

## License

MIT License
