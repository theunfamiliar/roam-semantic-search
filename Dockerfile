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

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create log directories with appropriate permissions
RUN mkdir -p /app/logs/{server,deploy,audit,performance,data,search} && \
    chmod -R 755 /app/logs

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "config/logging.yaml"]