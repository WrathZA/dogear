# ── Stage 1: build the Vite SPA ──────────────────────────────────────────────
FROM node:20-slim AS frontend-build

RUN corepack enable && corepack prepare pnpm@10.32.1 --activate

WORKDIR /build/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm run build

# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends supervisor && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built SPA from stage 1
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

VOLUME ["/app/data"]

ENV DATABASE_URL=sqlite+aiosqlite:////app/data/bookmarks.db

EXPOSE 8000 3000

COPY supervisord.conf /etc/supervisor/conf.d/bookmark-it.conf

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
