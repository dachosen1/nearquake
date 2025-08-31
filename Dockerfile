FROM python:3.13.5-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /usr/src/app

# Copy Python project files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

COPY . .

# Add crontab file in the cron directory
COPY crontab /etc/cron.d/my-cron-job

RUN chmod 0644 /etc/cron.d/my-cron-job && crontab /etc/cron.d/my-cron-job && touch /var/log/cron.log

CMD cron && tail -f /var/log/cron.log