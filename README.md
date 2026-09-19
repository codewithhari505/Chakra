# CHAKRA: AI-Powered Anti-Money-Laundering (AML) Investigation System

A modular, explainable, end-to-end production system for detecting financial crime, laundering typologies, and fraudulent payment flows using supervised machine learning, unsupervised anomaly detection, graph analytics, and an interactive investigator dashboard.

> **Statutory & Regulatory Notice:** This system is architected for financial intelligence triage. Model outputs and flagged typologies indicate statistical anomalies and pattern risks for human intelligence review under the **Prevention of Money Laundering Act (PMLA), 2002** and **RBI KYC Amendment Directions 2026**. They do not constitute judicial determinations of guilt.

---

## Complete 17-Phase Implementation Status

| Phase | Component Description | Verification Status | Artifacts & Metrics |
|:---:|---|:---:|---|
| **1** | Project Skeleton, Async SQLAlchemy, FastAPI Setup | ✅ **Complete** | Async SQLite / PostgreSQL session factory |
| **2** | Synthetic Data Generator (100k Txns / 10k Accounts) | ✅ **Complete** | Layering, Circular flows, Rapid burst, Structuring |
| **3** | Leak-Free Temporal Preprocessing Pipeline | ✅ **Complete** | `preprocessor.joblib`, `feature_scaler.pkl` |
| **4** | 25 Financial & Behavioral Feature Extractors | ✅ **Complete** | `train_features.csv`, `test_features.csv` |
| **5** | Heuristic AML Rule Engine & RBI 2026 Knowledge Base | ✅ **Complete** | PMLA §35A, Rule 9(14), FEMA 5(R), 6 Overseas Certifiers |
| **6** | Supervised Random Forest Classifier | ✅ **Complete** | ROC-AUC: 0.9986, Accuracy: 98.82%, Recall: 93.44% |
| **7** | Supervised XGBoost Classifier (UPI Switch Ready) | ✅ **Complete** | ROC-AUC: 0.9984, Recall: 94.94%, **Latency: 1.88 ms** |
| **8** | Unsupervised Isolation Forest Anomaly Detector | ✅ **Complete** | Accuracy: 94.56%, ROC-AUC: 0.9645 |
| **9** | NetworkX Directed Multi-Hop Graph Analytics | ✅ **Complete** | Cycle detection, Smurfing fan-in/out, Layering chains |
| **10** | Unified 4-Pillar Composite Risk Scoring Engine | ✅ **Complete** | $0.40 \times \text{ML} + 0.20 \times \text{Anom} + 0.20 \times \text{Rules} + 0.20 \times \text{Graph}$ |
| **11** | Explainable AI via TreeSHAP Attributions | ✅ **Complete** | Directional feature risk contributions & explanations |
| **12** | Complete FastAPI REST Suite (5 Active Routers) | ✅ **Complete** | `/transactions`, `/accounts`, `/alerts`, `/analytics`, `/investigations` |
| **13** | Production PostgreSQL Engine & Connection Pooling | ✅ **Complete** | `asyncpg`, `psycopg2-binary`, composite indexing |
| **14** | React + Vite Investigator Workspace & Sandbox | ✅ **Complete** | Triage Dashboard, Graph Explorer, UPI Simulator |
| **15** | Investigation Workflow & FIU-IND STR Filing Service | ✅ **Complete** | State machine, STR PMLA §12 filing, RBI 2026 EDD |
| **16** | Full End-to-End System Integration Tests | ✅ **Complete** | Continuous ingestion $\to$ scoring $\to$ triage $\to$ audit |
| **17** | Containerization, Deployment & Production Readiness | ✅ **Complete** | Multi-stage Dockerfiles, Docker Compose, launch scripts |

**Total Automated Test Coverage:** **55 / 55 unit and integration tests passing** (`pytest tests/ -v`).

---

## System Architecture

```
                                 [ UPI / Bank Switch Ingestion Stream ]
                                                 │
                                                 ▼
                             ┌───────────────────────────────────────┐
                             │  FastAPI Asynchronous Gateway (:8000) │
                             └───────────────────┬───────────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
         ┌───────────────────┐         ┌───────────────────┐         ┌───────────────────┐
         │  Pillar 1: ML     │         │ Pillar 2: Anomaly │         │  Pillar 3: Rules  │
         │  XGBoost & RF     │         │ Isolation Forest  │         │  PMLA & RBI 2026  │
         │  (Weight: 40%)    │         │ (Weight: 20%)     │         │  (Weight: 20%)    │
         └─────────┬─────────┘         └─────────┬─────────┘         └─────────┬─────────┘
                   │                             │                             │
                   └─────────────────────────────┼─────────────────────────────┘
                                                 │
                                                 ▼
                               ┌───────────────────────────────────┐
                               │  Pillar 4: NetworkX Graph Engine  │
                               │  Cycles & Funnels (Weight: 20%)   │
                               └─────────────────┬─────────────────┘
                                                 │
                                                 ▼
                               ┌───────────────────────────────────┐
                               │  Unified 4-Pillar Composite Score │
                               │        TreeSHAP Attribution       │
                               └─────────────────┬─────────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
         ┌───────────────────┐                                       ┌───────────────────┐
         │ PostgreSQL DB     │                                       │ React Workspace   │
         │ Alerts & Audits   │                                       │ Dashboard & Graph │
         └───────────────────┘                                       └───────────────────┘
```

---

## Banking & Switch Deployment Architecture (UPI Inline vs Out-of-Band)

The system is architected for dual-speed processing to satisfy NPCI's strict **50ms UPI transaction budget**:

1. **Synchronous In-Line Gating (< 5 ms):**
   - **XGBoost Classifier (1.88 ms p50, 3.77 ms p99)** + Heuristic Rule Engine evaluate transactions synchronously prior to bank core approval.
   - Blocks blatant fraud and structuring immediately.
2. **Asynchronous Out-of-Band Analysis (Background Queue):**
   - Multi-hop NetworkX cycle detection, deep Isolation Forest scoring, and TreeSHAP attribution calculations run asynchronously or via worker pools.
   - High-risk patterns generate alerts in the Investigator Queue without delaying end-user payments.

---

## Regulatory Compliance & Cybersecurity Standards

- **RBI 2026 Know Your Customer (KYC) Amendment Directions**:
  - Enforces mandatory verification under PMLA 2002 §35A, PML Rules 2005 Rule 9(14), and FEMA 5(R).
  - Enforces official OVD/Aadhaar certified copy recognition from **6 authorized overseas bodies**:
    1. Overseas branches of Scheduled Commercial Banks registered in India
    2. Branches of overseas banks with correspondent banking relationships
    3. Authorized foreign public notaries
    4. Judicial magistrates
    5. Law court judges
    6. Indian Embassy or Consulates
  - Enforces the **10% Ultimate Beneficial Ownership (UBO)** disclosure threshold.
- **10-Step Cybersecurity Framework**:
  - Embedded CSAM, IAM, anonymization, audit trails, and strict role-based access control.
- **FIU-IND Suspicious Transaction Report (STR)**:
  - Formally generated regulatory disclosure packets compliant with PMLA §12.

---

## Quick Start & Local Execution

### Option A: Docker Compose (Recommended for Production)

```bash
# Clone repository and launch multi-container stack
docker-compose up --build
```
- Frontend Dashboard: [http://localhost:3000](http://localhost:3000)
- Backend API & Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- PostgreSQL: `localhost:5432`

### Option B: Local Python + Node Environment

**1. Virtualenv & Dependencies:**
```powershell
# Windows
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

**2. One-Click Launch Script:**
```powershell
# Windows PowerShell
.\scripts\start_production.ps1

# Linux / macOS
./scripts/start_production.sh
```

**3. Run Complete Test Suite (55 Tests):**
```bash
venv\Scripts\python -m pytest tests/ -v
```

---

## Key API Endpoints

- `POST /api/v1/transactions/analyze`: Real-time 4-pillar risk assessment with SHAP drivers
- `GET  /api/v1/analytics/overview`: Real-time banking transaction and suspicion KPIs
- `GET  /api/v1/analytics/transaction-network`: Multi-hop NetworkX graph topology and cycle nodes
- `POST /api/v1/investigations/assign`: Assign alert to investigator (`NEW` $\to$ `UNDER_REVIEW`)
- `POST /api/v1/investigations/escalate`: Escalate case (`UNDER_REVIEW` $\to$ `ESCALATED`)
- `POST /api/v1/investigations/close`: Close case with audit resolution
- `POST /api/v1/investigations/str`: Generate formal FIU-IND STR regulatory report
- `POST /api/v1/investigations/edd`: Generate RBI 2026 Enhanced Due Diligence compliance docket
- `GET  /api/v1/investigations/{alert_id}/audit-trail`: Fetch immutable audit log

---

## License

MIT License. Designed and engineered for production-ready financial crime prevention and regulatory AML intelligence.
