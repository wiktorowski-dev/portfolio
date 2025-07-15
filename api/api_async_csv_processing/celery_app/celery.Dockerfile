FROM python:3.11-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN addgroup --system appuser \
 && adduser --system --ingroup appuser appuser

# Prepare app folder owned by the new user
WORKDIR /app
COPY . /app
RUN chown -R appuser:appuser /app

# Install Python dependencies (as root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY celery_app/celery.requirements.txt .
RUN pip install --no-cache-dir -r celery.requirements.txt
RUN pip install --no-cache-dir -U "celery[redis]"

# Switch to non-root user
USER appuser

ENV PYTHONPATH=/app
CMD ["celery", "-A", "celery_app.celery_worker", "worker", "-Q", "celery", "--loglevel=info"]

