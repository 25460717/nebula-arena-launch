# Multi-stage optimized Dockerfile for Nebula Arena Dedicated Game Server
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Image
FROM python:3.11-slim

LABEL org.opencontainers.image.title="nebula-arena-game-server" \
      org.opencontainers.image.description="Dedicated 20Hz Tickrate Game Server for Nebula Arena on Agones/GKE" \
      org.opencontainers.image.authors="Nebula Arena DevOps Team"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    PORT=8080

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
COPY app.py .

# Non-root user setup for security hardening
RUN groupadd -g 10001 nebula && \
    useradd -u 10001 -g nebula -s /bin/bash -m nebulauser && \
    chown -R nebulauser:nebula /app

USER 10001

EXPOSE 8080 7000-8000/udp

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

ENTRYPOINT ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
