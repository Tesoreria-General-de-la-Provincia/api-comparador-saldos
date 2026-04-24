FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv into the system python environment
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY . .

EXPOSE 8000

# When uvicorn is installed it will be in the system path
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --reload"]
