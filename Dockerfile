# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Generate SSH key if it doesn't exist
RUN if [ ! -f ssh_key ]; then \
    ssh-keygen -t rsa -b 2048 -f ssh_key -N ""; \
    fi

# Make port 2222 available to the world outside this container
EXPOSE 2222

# Run the application
CMD ["python", "main.py"]