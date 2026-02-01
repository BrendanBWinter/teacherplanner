# =============================================================================
# Backend Dockerfile - FastAPI with SQLite
# =============================================================================
# This Dockerfile builds a container for the Teacher Planner API.
#
# DOCKERFILE CONCEPTS:
# --------------------
# - FROM: Base image to build upon (Python in this case)
# - WORKDIR: Set the working directory inside the container
# - COPY: Copy files from host to container
# - RUN: Execute commands during build
# - EXPOSE: Document which port the app uses (doesn't publish it)
# - CMD: Default command to run when container starts
#
# MULTI-STAGE BUILD:
# ------------------
# We use a single stage here since Python doesn't need compilation.
# For compiled languages, you'd use multi-stage to keep the final image small.
# =============================================================================

# -----------------------------------------------------------------------------
# Base Image
# -----------------------------------------------------------------------------
# We use the official Python slim image to keep the container size small.
# 'slim' variants have minimal packages but still include what's needed
# for most Python applications.
# -----------------------------------------------------------------------------
FROM python:3.11-slim

# -----------------------------------------------------------------------------
# Set Working Directory
# -----------------------------------------------------------------------------
# All subsequent commands will run from this directory.
# This becomes the "root" of our application inside the container.
# -----------------------------------------------------------------------------
WORKDIR /app

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# Some Python packages require system libraries to compile.
# We install them, then clean up to keep the image small.
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Copy Requirements First (Docker Layer Caching)
# -----------------------------------------------------------------------------
# By copying requirements.txt first and installing dependencies before
# copying the rest of the code, Docker can cache this layer.
# This means if you only change your code (not dependencies), Docker
# won't re-download all packages - it uses the cached layer.
# -----------------------------------------------------------------------------
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Copy Application Code
# -----------------------------------------------------------------------------
# Now copy the rest of the application.
# This layer will be rebuilt whenever your code changes.
# -----------------------------------------------------------------------------
COPY . .

# -----------------------------------------------------------------------------
# Create Data Directory
# -----------------------------------------------------------------------------
# Create a directory for the SQLite database.
# This directory will be mounted as a volume to persist data.
# -----------------------------------------------------------------------------
RUN mkdir -p /app/data

# -----------------------------------------------------------------------------
# Document the Port
# -----------------------------------------------------------------------------
# EXPOSE doesn't actually publish the port - it's documentation.
# The actual port mapping happens in docker-compose.yml or docker run -p.
# -----------------------------------------------------------------------------
EXPOSE 8000

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Docker can periodically check if the container is healthy.
# This helps orchestrators know when to restart unhealthy containers.
# -----------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# Run the FastAPI app with Uvicorn.
# - --host 0.0.0.0: Listen on all interfaces (required in Docker)
# - --port 8000: Port to listen on
# - main:app: Module:variable for the FastAPI application
# -----------------------------------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
