FROM python:3.10-slim

# Install system dependencies for OpenCV, Audio, and FAISS
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libasound2 \
    libasound2-dev \
    libsndfile1 \
    portaudio19-dev \
    espeak \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p custom_system rag models

# Expose API/UI port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["python", "main.py"]
