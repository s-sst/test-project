# Architecture

This document records the key architectural decisions of the platform and the
rationale behind them. It complements the code, which is the source of truth.

## Guiding principles

The platform is built to the eight non-negotiable rules in the product brief.
The two that most shape the architecture:

1. **LLMs never calculate scores (Rule 1).** There is a hard wall between
   *interpretation* (LLM: classify PASS/PARTIAL/FAIL/CANNOT_DETERMINE, quote
   evidence, explain) and *computation* (Python: score, weight, aggregate,
   rank, risk). This wall is physical, not conventional: scoring lives in
   `scoring/engine.py`, a pure module with no LLM access, no I/O, no clock and
   no randomness.

2. **Frameworks are configuration (Rule 4).** Governance content is data, not
   code. The `Framework`/`Requirement` tables are a *projection* of the
   `frameworks_data/*.json` control libraries, synced by an idempotent command.
   You never edit Python to add a framework.

## The pipeline

```
Upload → OCR → Parse → Metadata → Chunk → Embed → ChromaDB → Retrieve
      → LLM (classify + quote) → Evidence validation → Scoring engine
      → Risk engine → Recommendation engine → Report → Dashboard
```

Phase 1 delivers the two ends that anchor determinism and trust — **secure
upload** and the **deterministic scoring engine** — plus the data model and
config engine the whole pipeline hangs off. Middle stages (OCR/RAG/LLM) have
stable interface scaffolds so later phases slot in without schema churn.

## Data model

Eleven core entities (UUID primary keys, timestamped):

- `User` — extends `AbstractUser` with a governance `role` (RBAC-ready).
- `UploadedDocument` / `DocumentChunk` — the artifact and its retrievable
  segments (chunks populated in Phase 2).
- `Framework` / `Requirement` — config projection; `Framework.config_hash`
  pins the exact loaded content for reproducibility.
- `Assessment` / `Evidence` — one governance run and its grounded quotes.
- `AssessmentScore` — a single polymorphic table discriminated by `level`
  (REQUIREMENT → CONTROL → FRAMEWORK → OVERALL). Requirement rows hold the LLM
  verdict (`status`, `confidence`, `reasoning`) **and** the Python-computed
  numbers; higher levels are Python rollups.
- `Recommendation` — with a Python-computed `priority_rank` and a
  `traceability` link back to the requirement/evidence (100% traceability KPI).
- `AuditLog` — append-only.
- `GeneratedReport` — report registry.

### Why one `AssessmentScore` table with a `level` discriminator?

It keeps the whole rollup hierarchy in one queryable place, matches the spec's
named model exactly, and makes "explain the deduction" trivial: walk from an
OVERALL row down to the REQUIREMENT rows that fed it. The clean separation of
LLM-sourced vs. Python-computed columns makes Rule 1 auditable at the schema
level.

## The scoring engine

`scoring/engine.py` is pure and deterministic:

- **`Decimal` + `ROUND_HALF_UP`** — no binary float drift; quantised to fixed
  precision.
- **Stable ordering** — requirements sorted by identifier before aggregation.
- **No side effects** — no DB, clock or RNG, so identical inputs always yield
  byte-identical output (100% reproducibility KPI). Proven by
  `test_determinism_identical_across_runs_and_order`.
- **Configurable `cannot_determine_policy`** — `exclude` (drop from the
  denominator) or `penalize` (count as zero), read from framework config.

`scoring/services.py` bridges the engine to the ORM: it reads persisted
requirement verdicts, runs the engine, and writes back the rollup rows +
assessment summary — idempotently.

## Configuration engine

- `frameworks/config/schema.py` — a strict JSON Schema
  (`additionalProperties: false`) exported to `frameworks_data/_schema.json`.
- `frameworks/config/loader.py` — parses JSON **or** YAML, validates (reporting
  *all* errors at once), rejects duplicate identifiers, computes a canonical
  SHA-256 `config_hash`, and flattens controls→requirements with stable order.
- `frameworks/services.py` + `sync_frameworks` command — idempotent upsert
  keyed on the config hash; prunes removed requirements; writes an audit entry.

## API design

- One uniform JSON envelope for success and error (`common/responses.py`,
  `common/exceptions.py`) so the frontend contract is stable across phases
  (Rule 7).
- The entire public URL surface is defined in one file (`api/urls.py`) to make
  the contract easy to review and preserve.
- `RequestContextMiddleware` assigns an `X-Request-ID` and captures the actor
  for the audit trail without threading the request through every service.

## Security posture (Phase 1)

- Uploads validated by extension allow-list **+ size limit + magic-byte MIME
  sniffing** (never trusting client `Content-Type`), dependency-free.
- All secrets via environment variables; nothing in source.
- Split settings with a production profile that fails fast on an unset secret
  key and enables HSTS/secure cookies.
- Append-only audit log; `role` field present for the RBAC enforcement that
  arrives in a later phase.

## Testing

60 tests spanning config validation/determinism, upload security, the scoring
engine's arithmetic + reproducibility, the full API surface, audit recording,
and the dashboard's empty-state safety. Run with `pytest` (in-memory SQLite).
