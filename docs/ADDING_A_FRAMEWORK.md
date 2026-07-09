# Adding a governance framework (config only)

Adding or updating a framework is a **configuration change** — you never touch
Python (Rule 4). The steps:

1. **Create a config file** in `backend/frameworks_data/`, named `<id>.json`
   (or `.yaml`). It must conform to `backend/frameworks_data/_schema.json`
   (the machine-readable contract, generated from `frameworks/config/schema.py`).

   Minimal shape:

   ```json
   {
     "framework": {
       "id": "my_framework",
       "name": "My Framework 1.0",
       "version": "1.0",
       "publisher": "…",
       "category": "…",
       "description": "…",
       "source_url": "https://…",
       "scoring": {
         "status_scores": {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0, "CANNOT_DETERMINE": 0.0},
         "aggregation": "weighted_mean",
         "cannot_determine_policy": "exclude"
       },
       "controls": [
         {
           "id": "C1",
           "title": "Control group title",
           "description": "…",
           "requirements": [
             {
               "identifier": "MYFW-C1-1",
               "title": "…",
               "description": "…",
               "control": "The concrete control that satisfies it",
               "weight": 3,
               "category": "…",
               "evidence_expectations": ["documented X", "records of Y"],
               "pass_criteria": "…",
               "partial_criteria": "…",
               "fail_criteria": "…",
               "references": ["Clause 1.2.3"]
             }
           ]
         }
       ]
     }
   }
   ```

   Rules the schema enforces: `id` is `^[a-z0-9_]+$`; `weight` is an integer
   1–5; every requirement has non-empty criteria, ≥1 evidence expectation and
   ≥1 reference; identifiers are unique within the framework;
   `additionalProperties` are rejected.

2. **Validate without touching the DB:**

   ```bash
   python manage.py sync_frameworks --check
   ```

   All schema violations are reported at once.

3. **Sync into the database:**

   ```bash
   python manage.py sync_frameworks          # only changed frameworks
   python manage.py sync_frameworks --force  # re-sync everything
   ```

   The sync is idempotent and driven by the config's SHA-256 hash. Requirements
   removed from the config are pruned (their evidence/score references are
   `SET_NULL`, so assessment history is preserved). A `SYNC` audit entry is
   written.

4. It now appears at `GET /api/frameworks` and `GET /api/framework/<id>`.

That's it — no migrations, no code changes.
