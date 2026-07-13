# ==========================================
# Stage 1: Base
# ==========================================
FROM python:3.12-slim AS base

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ==========================================
# Stage 2: Builder
# ==========================================
FROM base AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependencies file
COPY requirements.txt .
COPY requirements-api.txt .
COPY requirements-workers.txt .
ARG CACHE_DATE=1
RUN pip install --upgrade pip && \
    pip install -r requirements.txt -r requirements-api.txt -r requirements-workers.txt

# ==========================================
# Stage 3: Production Runner
# ==========================================
FROM base AS runner

# Install Node.js and npm for Drizzle ORM migrations
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the application code AND the infra directory
COPY api/ ./api/
COPY core/ ./core/
COPY plugins/ ./plugins/
COPY runtime/ ./runtime/
COPY brixta_sdk/ ./brixta_sdk/
COPY infra/ ./infra/

# Install drizzle deps inside infra folder
RUN cd infra && npm install

# Create empty storage directories with correct permissions
COPY --chown=appuser:appuser storage/ ./storage/

# Set ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]