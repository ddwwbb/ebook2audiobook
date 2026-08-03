#!/usr/bin/env bash
# Start backend (uvicorn) and frontend (vite) for local development.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Starting backend (uvicorn) ==="
cd backend
uvicorn main:app --reload --port 7860 &
BACKEND_PID=$!
cd ..

echo "=== Starting frontend (vite) ==="
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

cleanup() {
    echo "=== Shutting down ==="
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
