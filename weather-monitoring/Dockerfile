FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY weather_app.py .

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=weather_app.py
ENV FLASK_ENV=production

# Run application
CMD ["python", "weather_app.py"]