# Multi-stage build for better caching
FROM python:3.14.2-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /usr/src/app

# Create user early to avoid permission issues
RUN groupadd -r appuser && useradd -r -g appuser appuser -m

# Dependencies stage - changes rarely
FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Runtime stage
FROM base AS runtime
# Copy dependencies from deps stage
COPY --from=deps /usr/src/app/.venv /usr/src/app/.venv
COPY --from=deps /usr/src/app/pyproject.toml /usr/src/app/uv.lock ./

# Copy application code (changes frequently)
COPY . .

# Set ownership and permissions
RUN chown -R appuser:appuser /usr/src/app && \
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /home/appuser/.cache

USER appuser

# Default command - will be overridden by Batch job definition
CMD ["uv", "run", "main.py"]