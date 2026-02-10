FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends sqlite3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY src/ src/

# Create data directories
RUN mkdir -p /var/lib/chatter/chroma_data && \
    chown -R nobody:nogroup /var/lib/chatter

ENV DATABASE_URL="sqlite+aiosqlite:////var/lib/chatter/chatter.db"
ENV CHROMADB_PATH="/var/lib/chatter/chroma_data"
ENV LOG_LEVEL="INFO"

USER nobody

# Expose web UI port
EXPOSE 8080

# Default: run both web UI and Slack bot
CMD ["python", "-m", "chatter", "run"]
