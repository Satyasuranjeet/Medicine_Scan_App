# Use a slim version of Python 3.9 as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (including tesseract-ocr)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files into the container
COPY . /app

# Set environment variable to prevent Python from writing .pyc files
ENV PYTHONUNBUFFERED 1

# Expose the port that your FastAPI app will run on
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
