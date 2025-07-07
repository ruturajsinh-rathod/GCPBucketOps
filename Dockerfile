# Builder stage
FROM python:3.12-alpine AS builder

# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Make Python output unbuffered
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apk add --no-cache build-base libffi-dev postgresql-dev curl

# Set workdir
WORKDIR /code

# Copy only dependency-related files first (for better caching)
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir pip==25.1.1 poetry==1.6.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the code
COPY . .

# Runner stage
FROM python:3.12-alpine AS runner

# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Make Python output unbuffered
ENV PYTHONUNBUFFERED=1

# Set Python path for imports
ENV PYTHONPATH="/code"

# Install runtime system dependencies
RUN apk add --no-cache libffi postgresql-libs curl

# Create a non-root user
RUN addgroup -S app && adduser -S app -G app

# Switch to non-root user
USER app

# Set working directory
WORKDIR /code

# Copy installed dependencies, binaries, and source code from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /code /code

# Healthcheck to ensure the app is running
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${DOCKER_PORT}/healthcheck || exit 1

# Default command: run alembic migrations then start app
CMD alembic upgrade head && python main.py run
