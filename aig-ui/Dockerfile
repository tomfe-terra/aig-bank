# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_BASE_URL
ARG VITE_HOST=localhost
ARG VITE_PORT=3000

# Validate required build arguments
RUN test -n "$VITE_API_BASE_URL" || (echo "ERROR: VITE_API_BASE_URL is required" && exit 1)

# Create .env file for the build process
RUN echo "VITE_API_BASE_URL=$VITE_API_BASE_URL" > .env && \
    echo "VITE_HOST=$VITE_HOST" >> .env && \
    echo "VITE_PORT=$VITE_PORT" >> .env

# Build the application
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

