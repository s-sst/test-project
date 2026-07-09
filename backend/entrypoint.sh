#!/usr/bin/env sh
# Container entrypoint: migrate, load framework control libraries, collect
# static, then serve via gunicorn.
set -e

echo "==> Applying migrations"
python manage.py migrate --noinput

echo "==> Syncing framework control libraries"
python manage.py sync_frameworks

echo "==> Collecting static files"
python manage.py collectstatic --noinput || true

echo "==> Starting gunicorn"
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}"
