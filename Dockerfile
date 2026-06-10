# ==============================================================================
# Builder Stage: Install build dependencies and build wheels/venv
# ==============================================================================
FROM python:3.11-slim AS builder

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install compilation dependencies if needed (e.g. for C-extensions in some dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies first for caching optimization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn for production execution (since it's not in requirements.txt)
RUN pip install --no-cache-dir gunicorn

# ==============================================================================
# Runner Stage: Lean production-ready final image
# ==============================================================================
FROM python:3.11-slim AS runner

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_APP=app.py

WORKDIR /app

# Create a non-privileged user to run the app
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the rest of the application files
# Note: .dockerignore will filter out unnecessary files like .venv, tests, cache
COPY --chown=appuser:appgroup . .

# Ensure upload directory and db path are writeable by appuser
RUN mkdir -p /app/uploads /app/instance && \
    chown -R appuser:appgroup /app

# Switch to the non-privileged user
USER appuser

# Expose the application port
EXPOSE 5000

# Health check using standard library urllib to avoid needing curl/wget
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/')" || exit 1

# Start gunicorn by default (optimized for production)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "app:app"]
