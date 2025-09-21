# Use Python 3.13 slim base
FROM python:3.13-slim

WORKDIR /app

# Copy project files into /app
COPY . .

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install \
    fastapi>=0.116.1 \
    fastmcp==2.11.1 \
    google-adk>=1.14.0 \
    langchain>=0.3.27 \
    langchain-google-genai>=2.1.10 \
    langchain-mcp>=0.2.1 \
    requests>=2.32.5 \
    uvicorn>=0.35.0

# Expose port for Cloud Run
EXPOSE 8080

# Run FastAPI app with uvicorn (not adk web)
CMD ["uvicorn", "fastapi_sessions.main:app", "--host", "0.0.0.0", "--port", "8080"]




