# Deployment

## Backend (Docker Compose)

```bash
# From the repo root
export DJANGO_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(64))')"
export DJANGO_ALLOWED_HOSTS="your.domain.com"
docker compose up --build
```

This starts PostgreSQL + the Django/gunicorn backend. The entrypoint runs
migrations, syncs the framework control libraries, collects static files and
launches gunicorn on port 8000.

Key environment variables (see `backend/.env.example` for the full list):

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | **Required** in prod (a strong 64-char value). |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts. |
| `DATABASE_URL` | `postgres://user:pass@host:5432/db`. |
| `ENFORCE_RBAC` | `true` in prod: write/override endpoints require roles. |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s). |
| `LLM_PROVIDER` / `LLM_API_KEY` | `anthropic` + key to use real Claude; default is the offline deterministic mock. |
| `EMBEDDING_BACKEND` / `VECTOR_INDEX` | `sentence_transformers` / `chroma` to opt into the heavy RAG stack (install `requirements/rag.txt`). |
| `THROTTLE_ANON` / `THROTTLE_USER` | DRF rate limits. |

## Frontend (static build)

```bash
cd frontend
npm install
npm run build          # outputs frontend/dist
```

Serve `frontend/dist` from any static host / CDN / nginx, and point it at the
backend by setting `VITE_API_BASE` at build time (defaults to `/api`, i.e. a
same-origin reverse proxy). In development, `npm run dev` proxies `/api` to
`http://localhost:8000`.

## Production checklist

- [ ] Strong `DJANGO_SECRET_KEY` set (the prod settings refuse the dev default).
- [ ] `DJANGO_ALLOWED_HOSTS` restricted to real hosts.
- [ ] `ENFORCE_RBAC=true`; create users with appropriate roles.
- [ ] TLS terminated in front of gunicorn (`SECURE_SSL_REDIRECT=true`).
- [ ] Managed PostgreSQL with backups.
- [ ] For real LLM assessment at scale, move `POST /api/process` onto a task
      queue (Celery/RQ) instead of running synchronously in-request.
- [ ] `python manage.py check --deploy` passes.
