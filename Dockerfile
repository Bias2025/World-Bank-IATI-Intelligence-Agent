# World Bank IATI Intelligence Agent - Docker Configuration
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install any Python dependencies (if needed)
RUN pip install --no-cache-dir -r requirements.txt || echo "No Python dependencies"

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/ || exit 1

# Start the application
CMD ["python3", "-m", "http.server", "8080"]