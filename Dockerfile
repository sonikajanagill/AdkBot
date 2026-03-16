FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent/ ./agent/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8080"]
