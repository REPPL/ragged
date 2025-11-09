# Multi-stage Dockerfile for ragged
# Stage 1: Builder - compile dependencies and prepare environment
FROM python:3.11-slim as builder

LABEL maintainer="ragged"
LABEL description="Privacy-first local RAG system"

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# Stage 2: Runtime - minimal image for running the application
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN groupadd -r ragged && useradd -r -g ragged -u 1000 ragged

# Create necessary directories
RUN mkdir -p /app/data /app/src /app/docs /app/tests && \
    chown -R ragged:ragged /app

# Copy application code (will be mounted as volume in development)
COPY --chown=ragged:ragged . /app/

# Switch to non-root user
USER ragged

# Expose application port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
