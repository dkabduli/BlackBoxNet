# Production API image for Render (repo root context includes mock scenarios).
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git libpq-dev gcc && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /data/config-repo

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/ .
COPY packages/ /packages/

ENV GIT_REPO_PATH=/data/config-repo
ENV SCENARIOS_DIR=/packages/mock-scenarios
ENV REAL_DEVICE_ENABLED=false

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
