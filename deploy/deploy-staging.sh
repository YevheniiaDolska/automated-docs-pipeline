#!/usr/bin/env bash
# Deploy VeriDoc to staging server
# Run this on the staging server after git pull
#
# Prerequisites:
#   - Docker + Docker Compose installed
#   - deploy/.env.staging filled with real secrets
#   - Host Nginx configured with deploy/nginx-staging.conf
#   - Let's Encrypt SSL for staging.veri-doc.app
#
# Usage: bash deploy/deploy-staging.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== VeriDoc Staging Deployment ==="
echo "Project dir: $PROJECT_DIR"
echo ""

# Check .env.staging exists
if [ ! -f deploy/.env.staging ]; then
    echo "ERROR: deploy/.env.staging not found. Copy from .env.example and fill in secrets."
    exit 1
fi

# Step 1: Copy nginx config to host nginx sites
echo "[1/5] Copying nginx-staging.conf to host Nginx..."
if [ -d /etc/nginx/sites-available ]; then
    sudo cp deploy/nginx-staging.conf /etc/nginx/sites-available/staging.veri-doc.app
    sudo ln -sf /etc/nginx/sites-available/staging.veri-doc.app /etc/nginx/sites-enabled/
    echo "  Copied to /etc/nginx/sites-available/staging.veri-doc.app"
elif [ -d /etc/nginx/conf.d ]; then
    sudo cp deploy/nginx-staging.conf /etc/nginx/conf.d/staging.veri-doc.app.conf
    echo "  Copied to /etc/nginx/conf.d/staging.veri-doc.app.conf"
else
    echo "  WARNING: Could not find nginx config directory. Copy manually."
fi

# Step 2: Test nginx config
echo "[2/5] Testing Nginx configuration..."
sudo nginx -t

# Step 3: Build and start Docker containers
echo "[3/5] Building and starting Docker containers..."
docker compose \
    -f docker-compose.production.yml \
    -f docker-compose.staging.yml \
    --env-file deploy/.env.staging \
    up -d --build

# Step 4: Wait for health checks
echo "[4/5] Waiting for services to become healthy..."
echo "  Waiting for API..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8010/health/ready > /dev/null 2>&1; then
        echo "  API is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  WARNING: API health check timed out after 60s"
        echo "  Check logs: docker compose -f docker-compose.production.yml -f docker-compose.staging.yml logs api"
    fi
    sleep 2
done

echo "  Waiting for Web..."
for i in $(seq 1 30); do
    if wget --spider -q http://127.0.0.1:3010 2>/dev/null; then
        echo "  Web is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  WARNING: Web health check timed out after 60s"
        echo "  Check logs: docker compose -f docker-compose.production.yml -f docker-compose.staging.yml logs web"
    fi
    sleep 2
done

# Step 5: Reload nginx
echo "[5/5] Reloading Nginx..."
sudo nginx -s reload

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Staging URLs:"
echo "  Landing page:  https://staging.veri-doc.app/"
echo "  Login:         https://staging.veri-doc.app/login"
echo "  Register:      https://staging.veri-doc.app/register"
echo "  Dashboard:     https://staging.veri-doc.app/dashboard"
echo "  API health:    https://staging.veri-doc.app/health"
echo ""
echo "Docker status:"
docker compose \
    -f docker-compose.production.yml \
    -f docker-compose.staging.yml \
    --env-file deploy/.env.staging \
    ps
