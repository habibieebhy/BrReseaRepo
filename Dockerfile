FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc git \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-api.txt requirements-workers.txt requirements-rag.txt requirements-plugins.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install \
      -r requirements-workers.txt \
      -r requirements-rag.txt \
      -r requirements-plugins.txt

FROM python:3.12-slim AS runner

ARG BRIXTA_VERSION=2.1.0
ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="BRIXTA Core" \
      org.opencontainers.image.version="${BRIXTA_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/BRIXTAOrg/BrReseaRepo"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    BRIXTA_ENVIRONMENT=production
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 brixta \
    && useradd --system --uid 10001 --gid brixta --home-dir /app brixta

COPY --from=builder /opt/venv /opt/venv
COPY pyproject.toml README.md ./
COPY api/ ./api/
COPY brixta_cli/ ./brixta_cli/
COPY brixta_mcp/ ./brixta_mcp/
COPY brixta_sdk/ ./brixta_sdk/
COPY core/ ./core/
COPY plugins/ ./plugins/
COPY runtime/ ./runtime/
COPY infra/ ./infra/

RUN python -m pip install --no-deps . \
    && cd infra && npm ci --omit=dev \
    && mkdir -p /app/storage \
    && chown -R brixta:brixta /app

USER 10001:10001
EXPOSE 8000 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
