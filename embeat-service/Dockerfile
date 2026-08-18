FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY app/ app/
COPY checkpoints/ checkpoints/
COPY scripts/ scripts/

EXPOSE 7860

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=60s \
  CMD curl -sf http://localhost:7860/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]