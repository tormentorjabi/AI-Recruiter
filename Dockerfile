# Build stage
FROM python:3.13-alpine AS builder

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY alembic.ini .

FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache \
    libpq \
    openssl

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /app /app

RUN adduser -D appuser && \
    mkdir -p /app/logs && \
    chown -R appuser /app
USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

COPY tests/ ./tests/

CMD ["sh", "-c", "alembic upgrade head && python -m src.main"]