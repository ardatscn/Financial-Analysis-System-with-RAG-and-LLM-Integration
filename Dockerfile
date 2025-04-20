# Start with a minimal Python environment
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy your entire project into the container
COPY . .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# By default, run your main script when the container starts
CMD ["python", "main.py"]
