#!/bin/sh
set -e

uv run alembic upgrade head

if [ -f /data/reference.geojsonseq ]; then
    echo "Importing reference segments from /data/reference.geojsonseq..."
    uv run python -m may_walk.cli import-reference-segments \
        --file /data/reference.geojsonseq --replace-if-changed
fi

exec uv run uvicorn may_walk.main:app --host 0.0.0.0 --port 8000
