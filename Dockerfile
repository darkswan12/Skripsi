FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p storage

# Try to build index, but don't fail if it doesn't work
RUN python build_index.py || echo "Index build failed, will build at runtime"

# Expose port (Railway will handle this)
EXPOSE 8000

# Start the bot
CMD ["python", "main.py"] 