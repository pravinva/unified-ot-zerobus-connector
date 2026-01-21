# Unified OT/IoT Connector - Production Container
# Multi-stage build for minimal image size

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash connector && \
    mkdir -p /app /data && \
    chown -R connector:connector /app /data

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=connector:connector . /app/

# Create directories for runtime data
RUN mkdir -p /data/spool /data/logs && \
    chown -R connector:connector /data

# Switch to non-root user
USER connector

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    CONNECTOR_LOG_LEVEL=INFO \
    CONNECTOR_DATA_DIR=/data

# Expose ports
EXPOSE 8080
EXPOSE 8081
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run connector
CMD ["python", "-m", "unified_connector"]
