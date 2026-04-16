# =============================================================================
# RASA-ID Frontend Dockerfile
# =============================================================================
# Development server using Node.js + Vite
# Base: Node 20 Alpine
# =============================================================================

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first (for better caching)
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start: install any new deps (from mounted package.json), then run dev server
# This ensures newly added packages are available without manual rebuild
CMD ["sh", "-c", "npm install --prefer-offline && npm run dev"]
