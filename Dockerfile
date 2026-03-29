# Use standard Python slim image
FROM python:3.13-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first to utilize Docker build layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into the virtual environment using uv
RUN uv sync --frozen --no-cache

# Copy the rest of the application
COPY . .

# Cloud Run dynamically assigns the port to the $PORT environment variable (default 8080)
# We use bash to properly evaluate the $PORT variable into the uvicorn command
CMD ["bash", "-c", "uv run uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
