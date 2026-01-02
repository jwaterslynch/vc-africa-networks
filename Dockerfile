# Dockerfile for VC Africa Networks Replication
#
# This container provides a reproducible environment for running
# the analysis pipeline.
#
# Usage:
#   docker build -t vc-africa-networks .
#   docker run -it vc-africa-networks python scripts/replicate.py --demo
#
# With data mounted:
#   docker run -v /path/to/data:/app/data/raw vc-africa-networks python scripts/replicate.py --full

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.lock.txt requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.lock.txt

# Copy project files
COPY . .

# Set environment variables for reproducibility
ENV PYTHONHASHSEED=0
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create data directories
RUN mkdir -p data/raw data/processed data/synthetic outputs

# Default command: run demo mode
CMD ["python", "scripts/replicate.py", "--demo"]

# Labels
LABEL maintainer="[author email]"
LABEL description="Replication environment for VC Africa Networks paper"
LABEL version="1.0"
