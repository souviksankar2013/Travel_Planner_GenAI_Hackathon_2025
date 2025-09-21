FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . .

ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN uv sync --frozen

# Expose Cloud Run default port
EXPOSE 8080

# Start FastAPI server
CMD ["uv", "run", "server.py"]
