# =============================================================================
# Frontend Dockerfile - React App with Nginx
# =============================================================================
# This Dockerfile uses a MULTI-STAGE BUILD:
# 1. Stage 1 (build): Install dependencies and build the React app
# 2. Stage 2 (production): Serve the built files with Nginx
#
# WHY MULTI-STAGE?
# ----------------
# - The build stage needs Node.js, npm, and all dev dependencies (~1GB)
# - The final stage only needs Nginx and the built static files (~50MB)
# - This results in a much smaller production image
# =============================================================================

# =============================================================================
# STAGE 1: Build the React Application
# =============================================================================
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# -----------------------------------------------------------------------------
# Copy Package Files First (Docker Layer Caching)
# -----------------------------------------------------------------------------
# By copying package.json and package-lock.json first, Docker can cache
# the npm install layer. Only if these files change will npm reinstall.
# -----------------------------------------------------------------------------
COPY package*.json ./

# Install dependencies
RUN npm ci

# -----------------------------------------------------------------------------
# Copy Source Code and Build
# -----------------------------------------------------------------------------
# Now copy the rest of the source code and build the production bundle.
# The build output goes to /app/dist (Vite's default output directory).
# -----------------------------------------------------------------------------
COPY . .

# Build argument for API URL (can be overridden at build time)
# In production, the frontend will call the API through Nginx proxy
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

# Build the production bundle
RUN npm run build

# =============================================================================
# STAGE 2: Serve with Nginx
# =============================================================================
# Use the official Nginx Alpine image - small and efficient
FROM nginx:alpine

# -----------------------------------------------------------------------------
# Copy Built Files
# -----------------------------------------------------------------------------
# Copy the built React app from the build stage to Nginx's serve directory.
# --from=build refers to the first stage named "build".
# -----------------------------------------------------------------------------
COPY --from=build /app/dist /usr/share/nginx/html

# -----------------------------------------------------------------------------
# Copy Nginx Configuration
# -----------------------------------------------------------------------------
# Use our custom Nginx config for SPA routing and API proxying.
# -----------------------------------------------------------------------------
COPY nginx.conf /etc/nginx/conf.d/default.conf

# -----------------------------------------------------------------------------
# Expose Port
# -----------------------------------------------------------------------------
# Nginx will listen on port 80 inside the container.
# We'll map this to port 3000 on the host in docker-compose.yml.
# -----------------------------------------------------------------------------
EXPOSE 80

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# -----------------------------------------------------------------------------
# Start Nginx
# -----------------------------------------------------------------------------
# Run Nginx in the foreground (required for Docker).
# -g 'daemon off;' prevents Nginx from running as a background daemon.
# -----------------------------------------------------------------------------
CMD ["nginx", "-g", "daemon off;"]
