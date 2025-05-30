FROM python:3.11-bullseye

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for faiss, torch, and building Python wheels
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libopenblas-dev \
    libomp-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (this layer will be cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create log directories (this layer will be cached)
RUN mkdir -p /app/logs/{server,deploy,audit,performance,data,search} && \
    chmod -R 755 /app/logs

# Copy configuration files first (changes less frequently)
COPY config/ ./config/
COPY scripts/ ./scripts/

# Copy application code without requirements.txt (prevents cache invalidation)
COPY app/ ./app/
COPY .coveragerc pytest.ini ./

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ping || exit 1

# Start uvicorn with increased timeout
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "config/logging.yaml", "--timeout-keep-alive", "600"]