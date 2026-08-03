#!/bin/sh
# Entrypoint for Audiobook Studio Docker container.
# Starts the FastAPI backend with uvicorn.

set -e

echo "=== Audiobook Studio ==="
echo "Starting backend on port 7860..."

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg not found"
    exit 1
fi

# Check ebook-convert (Calibre)
if ! command -v ebook-convert &> /dev/null; then
    echo "WARNING: ebook-convert (Calibre) not found — EPUB conversion may fail"
fi

exec uvicorn backend.main:app --host 0.0.0.0 --port 7860
