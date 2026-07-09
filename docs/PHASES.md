# Delivery roadmap

The platform is built in phases. Each phase is independently valuable, extends
(never rewrites) prior work, and keeps the REST API backward-compatible.

### ✅ Phase 1 — Foundation (this delivery)

- Django 5 + DRF project; split settings (base/dev/prod/test); env-driven config.
- All 11 core data models + migrations; custom user model.
- Configuration-driven framework engine: strict JSON Schema, JSON/YAML loader,
  deterministic `config_hash`, idempotent `sync_frameworks` command.
- 5 seed control libraries (122 requirements), adversarially fact-checked.
- Secure multi-document upload API (extension + size + magic-byte validation).
- Deterministic scoring engine (pure Python) + persistence service — tested for
  100% reproducibility.
- Append-only audit trail + request-correlation middleware.
- Dashboard KPI analytics endpoint.
- Versioned auditor prompt library.
- Full REST surface (all 9 spec routes + supporting endpoints); 60 tests.

### Phase 2 — Ingestion & RAG

- `ingestion/`: PyMuPDF/pdfplumber text extraction, pytesseract OCR fallback,
  table/scanned-page detection, metadata + XREF, DOCX support.
- `rag/`: recursive + page chunking, embeddings (Sentence Transformers /
  nomic-embed-text), ChromaDB vector store, framework-scoped retrieval.
- Wire `POST /api/process` to run ingestion + indexing; populate `DocumentChunk`.

### Phase 3 — LLM assessment & hallucination prevention

- Provider-agnostic LLM client (Claude/GPT/Gemini/Qwen/Ollama), temperature 0.
- Per-requirement assessment using the auditor prompts → strict JSON verdicts.
- Hallucination prevention: quote verifier, page verifier, JSON-schema
  validator, confidence threshold, retry logic, deterministic caching, human
  review queue. Populate `Evidence` + requirement-level `AssessmentScore`.

### Phase 4 — Scoring, risk & recommendations at runtime

- Invoke `scoring.services.score_and_persist` after verdicts land.
- Risk engine refinement; recommendation generation from gaps with deterministic
  ranking and full traceability.

### Phase 5 — Reports

- ReportLab PDF (executive summary, framework scores, evidence, missing
  controls, risk, recommendations, appendix) + JSON export; wire `report/{id}`.

### Phase 6 — Frontend, auth & hardening

- React + TypeScript + Tailwind + Recharts (Dashboard, Upload, Assessment,
  Framework Explorer, Reports, History, Settings).
- RBAC enforcement, human-override workflow, rate limiting, deployment.
