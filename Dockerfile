FROM python:3.12-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
# Compile bytecode prevents python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: Sync with exact versions from uv.lock
# --no-dev: Do not install development dependencies
RUN uv sync --frozen --no-dev

# Add the virtual environment to the PATH
# This ensures that 'uvicorn' and 'python' use the installed dependencies
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application code
COPY src/ src/
COPY app.py .
COPY kmeans_model.pkl .
COPY wallet_power_transformer.pkl .

# Create cache directory
RUN mkdir -p cache_data

EXPOSE 8000

# Use the venv's uvicorn directly (thanks to PATH)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
