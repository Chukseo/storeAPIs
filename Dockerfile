# Use official Python image as base (change to your app's language if needed)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (change if your app uses a different port)
EXPOSE 8080

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1



# Collect static files
RUN python manage.py collectstatic

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "core.wsgi:application"]


# Command to run your app (change as needed)
# CMD ["python", "app.py"]