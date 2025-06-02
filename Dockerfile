FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Install pipenv or pip requirements (assuming requirements.txt exists)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose the port Cloud Run expects
EXPOSE 8080

# Environment variable for Cloud Run
ENV PORT 8080

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
