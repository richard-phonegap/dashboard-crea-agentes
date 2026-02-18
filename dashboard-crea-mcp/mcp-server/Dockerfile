FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports: 8000 (MCP), 8002 (Config API)
EXPOSE 8000 8002

# Make start script executable
RUN chmod +x start.sh

# Run the startup script
CMD ["/bin/bash", "start.sh"]
