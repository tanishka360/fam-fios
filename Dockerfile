# ==============================================================================
# FAM-FIOS: Production Multi-Tenant Fitness OS Container
# Patent Invention Disclosure: 24BIT0370-24BIT0390-IDF-01
# ==============================================================================

FROM python:3.10-slim AS runner

# 1. Set environment parameters
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 2. Install essential system dependencies (curl for health probes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Create non-root user for security hardening
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# 4. Leverage Docker layer caching by copying dependencies first
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy application source code
COPY . /app

# 6. Ensure correct permissions for persistent storage directories
RUN mkdir -p /app/backend/app/storage/s3_sandbox && \
    chown -R appuser:appgroup /app

# 7. Switch to unprivileged user
USER appuser

# 8. Expose Streamlit application port
EXPOSE 8501

# 9. Healthcheck probe (monitored by AWS App Runner / ALB / ECS)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 10. Default container startup command
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
