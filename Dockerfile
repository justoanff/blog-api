FROM python:3.10-alpine AS builder

WORKDIR /app

# Install build dependencies needed for Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    postgresql-dev \
    curl

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy requirements and create pyproject.toml for uv to use
COPY requirements.txt .
COPY pyproject.toml .

# Generate lockfile and install dependencies in one step
RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock && \
    uv sync --frozen --no-cache

# Copy the rest of the application
COPY . .

# Use multi-stage build for smaller final image
FROM python:3.10-alpine

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install only runtime dependencies
RUN apk add --no-cache \
    curl \
    libpq

# Copy the installed virtual environment and application from builder
COPY --from=builder /app /app

# Expose the port
EXPOSE 8000

# Run the application with proxy headers support
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
