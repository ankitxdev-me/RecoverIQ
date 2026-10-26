# RecoverIQ — Autonomous AI Revenue Recovery Agent

Our Team Gladiators consits of Two members
1.  Ankit Gupta
2.  Satyam Vishwakarma

[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2026-blueviolet.svg)](https://hacktoberfest.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React + Vite](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20Tailwind-61dafb.svg)](https://vitejs.dev/)
[![Ollama](https://img.shields.io/badge/AI%20Model-Google%20Gemma%204%20(4.6B)-orange.svg)](https://ollama.ai/)
[![Test Suite](https://img.shields.io/badge/Tests-45%20Passed%20(100%25)-brightgreen.svg)](#10-running-tests)

> **Hacktoberfest Hackathon Project**: RecoverIQ is an autonomous AI revenue recovery agent built with Google Gemma 4. It ingests live business data, detects transaction failures, aging invoices, and abandoned carts, and executes safe recovery workflows under strict financial guardrails.

**RecoverIQ** is an autonomous, financial-grade AI revenue recovery system built for finance and billing operations. It identifies revenue at risk and manages recovery workflows across three core business domains:

1. **Failed payments** (card declines, temporary limits, expired payment methods)
2. **Overdue invoices** (aging receivables, payment notice schedules)
3. **Abandoned checkouts** (cart abandonment recovery under strict safety guardrails)

---

## 1. Core Workflow & Architectural Flow

RecoverIQ strictly adheres to an 8-stage financial state machine:

```mermaid
flowchart LR
    DETECT --> INVESTIGATE
    INVESTIGATE --> PRIORITIZE
    PRIORITIZE --> RECOMMEND
    RECOMMEND --> VALIDATE
    VALIDATE --> APPROVE
    APPROVE --> EXECUTE
    EXECUTE --> VERIFY
    VERIFY --> REPORT
```

### Critical Financial Rule & Metric Separation
RecoverIQ strictly segregates financial outcomes:
- **Revenue at Risk**: Total unsettled value of open, unrecovered cases.
- **Revenue Eligible for Recovery**: Subtotal of open cases that satisfy cooldown periods and retry limits.
- **Confirmed Recovered Revenue (LIVE)**: Cleared through verified production payment gateways.
- **Simulated Recovered Revenue (SANDBOX)**: Verified in sandbox test providers. *Never combined with or reported as real live revenue.*
- **Unverified / Attempted Outcomes**: Merely dispatching a reminder or initiating an action is **never** counted as revenue recovered until verification succeeds.

---

## 2. Technology Stack

- **Backend**: Python 3.11+ / 3.14, FastAPI, SQLAlchemy 2.0 (SQLite with `PRAGMA foreign_keys=ON`), Pydantic v2, Pytest.
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons.
- **Local AI Engine**: Local Ollama server (`http://localhost:11434`) running Google Gemma 4 (`gemma4:e2b`, 4.6B).
- **Persistence & Privacy**: Local device session logging (`backend/sessions/audit_session.jsonl`) and browser `localStorage`.

---

## 3. Prerequisites

Before running RecoverIQ on Windows:

1. **Python 3.11+** installed and available in PATH (`python --version`).
2. **Node.js 18+** and npm installed and available in PATH (`node --version`, `npm --version`).
3. **Ollama** installed and running on `http://localhost:11434`.
   - Verify Ollama and the installed model:
     ```powershell
     curl.exe http://localhost:11434/api/tags
     ```
   - Target model: `qwen2.5:3b`. If not yet pulled, pull it once with:
     ```powershell
     ollama pull qwen2.5:3b
     ```
   - *Note: If Ollama is offline or starting up, RecoverIQ automatically activates its high-performance deterministic rule-based fallback so the app remains 100% usable.*

---

## 4. Windows PowerShell Execution Policy

If PowerShell restricts running local scripts, grant execution rights for your current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## 5. Quick Setup (Windows)

Run the automated setup script from the project root:

```powershell
.\setup.ps1
```

This script will:
1. Verify Python and create the virtual environment (`.venv`).
2. Install all Python dependencies from `backend/requirements.txt`.
3. Install frontend NPM packages and compile the production bundle.
4. Verify the local Ollama connection and `qwen2.5:3b` model status.

---

## 6. Launching the Application

### Option A: Master Launch (Runs both Backend & Frontend)
```powershell
.\run_demo.ps1
```

### Option B: Separate Terminal Windows

**Terminal 1 — Backend (FastAPI on Port 8000):**
```powershell
.\run_backend.ps1
```
*API Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)*

**Terminal 2 — Frontend (Vite on Port 5173):**
```powershell
.\run_frontend.ps1
```
*Web Application URL: [http://localhost:5173](http://localhost:5173)*

---

## 7. Guided Demo Walkthrough

Follow this step-by-step path to experience the full end-to-end recovery lifecycle:

1. **Explore the Dashboard ([http://localhost:5173](http://localhost:5173))**:
   - Inspect the distinct separation between **Confirmed Recovered (Live)** and **Simulated Recovered (Sandbox)**.
   - Observe the **Recovery Success Rate** with its transparent denominator calculation.
   - Review the **Recent Recovery Activity** audit stream.

2. **Inspect a Case (Recovery Cases Tab)**:
   - Click on case **`CASE-PAY-1001`** (Acme Corporation, $1,450.00).
   - The slide-over inspection drawer opens showing:
     - Multi-factor priority score calculation (Amount + Urgency + Soft Decline code).
     - Customer contact references.
     - Action history and cooldown indicators.

3. **Consult the AI Copilot (AI Copilot Tab)**:
   - Ask: *"Which five cases should I handle first?"*
   - Ask: *"Investigate case CASE-PAY-1001"*
   - Ask: *"Draft a polite reminder for CASE-PAY-1001"*
   - Watch the agent invoke allowlisted Python tools and display the exact verified parameters and database output.

4. **Review Protected Actions (Approval Center Tab)**:
   - View pending action for **`CASE-PAY-5005`** (Enterprise Cloud Inc, $12,500.00).
   - Review the consequence warning (High value balance exceeded threshold).
   - Click **Authorize** to grant human approval.

5. **Execute Simulated Recovery Action**:
   - Click **Execute Simulated Action** from the case drawer.
   - The mock payment adapter processes the charge with an idempotency key and generates receipt `sim_ch_xxx`.

6. **Verify Recovery Outcome**:
   - Notice the status shifts to `VERIFYING RECEIPT`.
   - Click **Verify Recovery Outcome**. Once cryptographically confirmed, the case transitions to `RECOVERED (SIMULATED)` and the sandbox recovered revenue counter increments.

7. **Review Audit Trail (Audit Log Tab)**:
   - Filter by case ID or event type to verify complete chronological record-keeping.

8. **Reset Demo Data**:
   - Click **Reset Demo** in the top navbar at any time to instantly restore the original deterministic test records.

---

## 8. Integration Layer & CSV Import

RecoverIQ includes an integration layer with clean interfaces for future payment gateways, store checkouts, and accounting platforms:

- `BasePaymentProvider` ([backend/app/integrations/base.py](file:///c:/Users/ankit/OneDrive/Documents/RevenuePilot%20Ai/backend/app/integrations/base.py))
- `BaseEcommerceProvider` ([backend/app/integrations/base.py](file:///c:/Users/ankit/OneDrive/Documents/RevenuePilot%20Ai/backend/app/integrations/base.py))
- `BaseAccountingProvider` ([backend/app/integrations/base.py](file:///c:/Users/ankit/OneDrive/Documents/RevenuePilot%20Ai/backend/app/integrations/base.py))

### Importing Custom CSV Data
Navigate to the **Integrations & Diagnostics** tab to import raw CSV records:
- **Sample files available**:
  - `backend/sample_data/failed_payments.csv`
  - `backend/sample_data/overdue_invoices.csv`
  - `backend/sample_data/abandoned_checkouts.csv`
- The CSV importer validates amounts, standardizes timestamps to UTC, rejects malformed rows with diagnostics, ignores duplicates, and triggers the detection engine automatically.

---

## 9. Deterministic AI Agent Allowlist & Guardrails

The local `qwen2.5:3b` model is strictly restricted to an allowlist of Pydantic-validated tools:

| Tool Name | Scope | Safety Guardrail |
| :--- | :--- | :--- |
| `get_dashboard_summary` | Read-only | Returns exact DB financial aggregates |
| `list_recovery_cases` | Read-only | Filterable case listings |
| `get_case_details` | Read-only | Verified customer & case state |
| `investigate_case` | Read-only | Multi-factor diagnostics |
| `calculate_recovery_priority` | Deterministic | Transparent 0-100 scoring |
| `recommend_recovery_action` | Deterministic | Enforces retry limits & cart guardrails |
| `draft_customer_message` | Reasoning | Context-tailored dunning notices |
| `request_action_approval` | State change | Submits to human oversight queue |
| `get_action_status` | Read-only | Action lifecycle checks |
| `verify_recovery_outcome` | Verification | Gateway receipt audit |

**Agent Safety Guarantees:**
- No arbitrary Python or shell code execution.
- No direct database queries or schema manipulation by the LLM.
- **Abandoned Checkout Safety Rule**: Abandoned carts are **never** retried as card charges; only customer checkout links or incentives are permitted.
- **Idempotency Keys**: Every proposed recovery action generates a unique idempotency key preventing duplicate gateway charges.

---

## 10. Running Tests

Execute the automated test suite covering financial precision, priority scoring, safety rules, duplicate CSV prevention, and REST API endpoints:

```powershell
.\.venv\Scripts\pytest.exe -v
```

*All 31 unit and integration tests run offline without requiring external internet or cloud subscriptions.*

---

## 11. Troubleshooting & Diagnostics

- **Ollama Offline**: If Ollama is not running, RecoverIQ displays a diagnostic pill in the navbar and automatically switches to deterministic fallback mode.
- **Port Conflict (8000 or 5173 in use)**:
  - Backend: edit `run_backend.ps1` and specify a different port (e.g. `--port 8080`).
  - Frontend: Vite will automatically offer the next available port (e.g. `5174`).
- **Database Reset**: If you wish to purge local state manually, delete `recoveriq.db`; the backend will recreate and reseed it automatically on the next launch.
