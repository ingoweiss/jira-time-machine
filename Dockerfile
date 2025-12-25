# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
# Note: The || fallback with --trusted-host is ONLY used if the initial install fails
# This handles corporate proxies/firewalls with SSL interception
# The primary install attempt ALWAYS uses full SSL verification
# To force SSL verification in all cases, remove the "|| pip install..." fallback
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy the application code
COPY . .

# Install the package in development mode
# Note: The || fallback with --trusted-host is ONLY used if the initial install fails
# This handles corporate proxies/firewalls with SSL interception
# The primary install attempt ALWAYS uses full SSL verification
# To force SSL verification in all cases, remove the "|| pip install..." fallback
RUN pip install -e . || \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .

# Default command - run Python shell
CMD ["python"]
