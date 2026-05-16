# Multi-stage Dockerfile for AutoDocThinker
# To build: docker build -t auto-doc-thinker .

# --- Stage 1: Build Frontend ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Final Backend Image ---
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend assets to backend static folder
# Note: In the current structure, React is separate, but we can 
# serve it from FastAPI if we mount the 'dist' folder.
COPY --from=frontend-builder /app/frontend/dist ./frontend_dist

# Expose port
EXPOSE 5000

# Environment variables
ENV PORT=5000
ENV APP_ENV=production

# Run the backend
CMD ["python", "run.py"]
