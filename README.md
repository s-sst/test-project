# AI Governance & Compliance Platform

An enterprise **AI Governance Copilot** that automates governance assessments —
evidence extraction, requirement mapping, deterministic scoring, gap analysis,
recommendations and audit reporting — while keeping a **human responsible for
every final compliance decision**. It assists auditors; it never replaces them.

> **Status: Phase 1 (Foundation) complete.** Backend foundation, data model,
> configuration-driven framework engine, secure upload API, deterministic
> scoring engine, and audit trail are implemented and tested. Ingestion, RAG,
> LLM assessment, reports and the frontend are delivered in later phases (see
> [docs/PHASES.md](docs/PHASES.md)).

---

## Core architectural guarantees

| Guarantee | How it is enforced |
|-----------|--------------------|
| **LLMs never score** (Rule 1) | All scoring/weighting/aggregation/risk is pure Python in [`scoring/engine.py`](backend/scoring/engine.py). The LLM only classifies + quotes evidence. |
| **100% deterministic & reproducible** | `Decimal` arithmetic + `ROUND_HALF_UP`, stable sort order, no clock/RNG in the engine; framework configs pinned by SHA-256 hash. |
| **Frameworks are configuration** (Rule 4) | Control libraries live in `backend/frameworks_data/*.json` validated against a strict JSON Schema. Adding a framework is **config-only** — no Python changes. |
| **No hallucinated evidence** (Rule 2) | Every requirement verdict must cite a verbatim quote + page. Hallucination-prevention layer arrives in Phase 3; the data model already requires grounded, verifiable evidence. |
| **Strict JSON everywhere** (Rule 3) | Uniform response envelope; the LLM prompt contract mandates JSON-only output. |
| **Full audit trail** | Append-only `AuditLog`, request-correlation middleware; every mutation is recorded. |

---

## Tech stack

Backend: **Python 3.11 · Django 5 · Django REST Framework**  ·  Config: **JSON/YAML + JSON Schema**
Database: **SQLite (dev) / PostgreSQL (prod)**  ·  Vector DB: **ChromaDB** (Phase 2)
Embeddings: **Sentence Transformers / nomic-embed-text** (Phase 2)
LLM: **provider-agnostic** — Claude / GPT / Gemini / Qwen / Ollama (Phase 3)
OCR: **PyMuPDF · pdfplumber · pytesseract** (Phase 2)  ·  Reports: **ReportLab** (Phase 5)
Frontend: **React · TypeScript · Tailwind · Recharts** (later phase)

---

## Quickstart

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env                 # then edit as needed

python manage.py migrate
python manage.py sync_frameworks     # load the 5 seed control libraries into the DB
python manage.py runserver
```

Verify:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/frameworks
```

Run the test suite:

```bash
cd backend && ./.venv/bin/python -m pytest      # 60 tests
```

---

## Seed frameworks (config-driven)

Loaded from `backend/frameworks_data/`, each authored and **adversarially
fact-checked against the source standard** (122 requirements total):

| Framework | Requirements | Controls |
|-----------|:---:|:---:|
| ISO/IEC 42001:2023 (AIMS) | 34 | 10 |
| EU AI Act (Reg. 2024/1689) | 29 | 12 |
| NIST AI RMF 1.0 | 29 | 4 |
| OECD AI Principles | 16 | 6 |
| OWASP Top 10 for LLM Applications 2025 | 14 | 10 |

Adding a new framework? See [docs/ADDING_A_FRAMEWORK.md](docs/ADDING_A_FRAMEWORK.md).

---

## REST API (all JSON, uniform envelope)

Success: `{"success": true, "data": ..., "meta": {...}}`
Error: `{"success": false, "error": {"code", "message", "details"}}`

| Method & path | Purpose | Phase 1 behaviour |
|---|---|---|
| `GET  /api/health` | Liveness + version | ✅ |
| `POST /api/upload` | Upload document(s) (validated) | ✅ |
| `GET  /api/frameworks` | List frameworks | ✅ |
| `GET  /api/framework/{id}` | Framework + grouped requirements | ✅ |
| `POST /api/process` | Create an assessment | ✅ (creates `PENDING`; pipeline runs later phases) |
| `POST /api/reprocess` | Reset an assessment | ✅ |
| `GET  /api/assessment/{id}` | Full assessment | ✅ |
| `GET  /api/history` | Assessment history | ✅ |
| `GET  /api/dashboard` | KPIs + analytics | ✅ |
| `GET  /api/report/{id}` | Report record | ✅ (rendering: Phase 5) |
| `GET  /api/documents`, `/api/audit-logs`, `/api/auth/*` | Supporting endpoints | ✅ |

---

## Repository layout

```
backend/
  config/            Django project (split settings: base/dev/prod/test)
  common/            Shared: base models, enums, envelope, exceptions, hashing, validators
  users/             Custom User + roles
  authentication/    Token auth + /me
  audit_logs/        Append-only audit trail + request-context middleware
  documents/         UploadedDocument, DocumentChunk + secure upload
  frameworks/        Framework/Requirement + config engine (schema, loader, sync)
  frameworks_data/   JSON control libraries  (the source of truth for governance)
  assessments/       Assessment, Evidence + lifecycle
  scoring/           AssessmentScore + DETERMINISTIC scoring engine
  recommendations/   Recommendation (deterministic ranking)
  reports/           GeneratedReport + JSON assembly
  dashboard/         KPI analytics
  ingestion/ rag/    Document parsing + retrieval  (interfaces now, impl Phase 2)
  prompts/           Versioned auditor prompt library (implemented)
  api/               Public URL surface + health/root
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design decisions and
[docs/PHASES.md](docs/PHASES.md) for the delivery roadmap.
