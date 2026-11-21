#!/bin/sh
set -e

# Миграции перед стартом приложения (идемпотентно)
echo "Applying database migrations..."
alembic upgrade head

exec "$@"
