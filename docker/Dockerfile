# Audiobook Studio — x86_64 Docker image
# Multi-stage: build frontend → Python backend + deps

# ===== Stage 1: Build frontend =====
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent || npm install --silent
COPY frontend/ ./
RUN npm run build

# ===== Stage 2: Python backend =====
FROM python:3.11-slim AS runtime

# Install system deps: ffmpeg, calibre (ebook-convert), espeak
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    calibre \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
