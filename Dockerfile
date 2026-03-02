# Dockerfile for running the drama-emcee test suite in an isolated container.
#
# Usage:
#   docker build -t drama-emcee-test .
#   docker run --rm drama-emcee-test

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependency manifest first to leverage layer caching
COPY requirements.txt .

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Default command: run the full test suite with verbose output
CMD ["python3", "-m", "pytest", "tests/", "-v"]
