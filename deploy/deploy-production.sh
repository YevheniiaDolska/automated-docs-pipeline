#!/usr/bin/env bash
# Deploy VeriDoc to production server
# Run this on the production server after git pull
#
# Architecture: Docker Nginx (inside compose) handles routing
#   api.veri-doc.app  -> FastAPI (port 8000 internal)
#   app.veri-doc.app  -> Next.js (port 3000 internal)
#   Nginx listens on 80/443 externally
#
# Prerequisites:
#   - Docker + Docker Compose installed
#   - deploy/.env.production filled with real secrets
#   - DNS records: api.veri-doc.app, app.veri-doc.app -> server IP
#   - SSL certs in deploy/ssl/ (or use Cloudflare proxy)
#
# Usage: bash deploy/deploy-production.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== VeriDoc Production Deployment ==="
echo "Project dir: $PROJECT_DIR"
echo ""

# Check .env.production exists
ENV_FILE="deploy/.env.production"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found."
    echo "Create it from deploy/.env.example and fill in all required secrets."
    exit 1
fi

# Validate required vars
source "$ENV_FILE"
for var in POSTGRES_PASSWORD VERIDOC_SECRET_KEY; do
    if [ -z "${!var:-}" ] || [ "${!var}" = "CHANGE_ME_STRONG_PASSWORD" ] || [ "${!var}" = "CHANGE_ME_GENERATE_WITH_openssl_rand_hex_32" ]; then
        echo "ERROR: $var is not set or still has placeholder value in $ENV_FILE"
        exit 1
    fi
done

# Step 1: Build and start all services
echo "[1/3] Building and starting Docker containers..."
docker compose \
    -f docker-compose.production.yml \
    --env-file "$ENV_FILE" \
    up -d --build

# Step 2: Wait for health checks
echo "[2/3] Waiting for services to become healthy..."

echo "  Waiting for PostgreSQL..."
for i in $(seq 1 20); do
    if docker compose -f docker-compose.production.yml --env-file "$ENV_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-veridoc}" > /dev/null 2>&1; then
        echo "  PostgreSQL is ready!"
        break
    fi
    [ "$i" -eq 20 ] && echo "  WARNING: PostgreSQL timed out"
    sleep 2
done

echo "  Waiting for API..."
for i in $(seq 1 30); do
    if docker compose -f docker-compose.production.yml --env-file "$ENV_FILE" exec -T api curl -sf http://localhost:8000/health/ready > /dev/null 2>&1; then
        echo "  API is healthy!"
        break
    fi
    [ "$i" -eq 30 ] && echo "  WARNING: API health check timed out"
    sleep 2
done

echo "  Waiting for Web..."
for i in $(seq 1 30); do
    if docker compose -f docker-compose.production.yml --env-file "$ENV_FILE" exec -T web wget --spider -q http://localhost:3000 2>/dev/null; then
        echo "  Web is healthy!"
        break
    fi
    [ "$i" -eq 30 ] && echo "  WARNING: Web health check timed out"
    sleep 2
done

# Step 3: Show status
echo "[3/3] Checking service status..."
echo ""
docker compose \
    -f docker-compose.production.yml \
    --env-file "$ENV_FILE" \
    ps

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Production URLs:"
echo "  Frontend:   https://app.veri-doc.app/"
echo "  API:        https://api.veri-doc.app/"
echo "  API health: https://api.veri-doc.app/health/ready"
echo ""
echo "Next steps:"
echo "  1. Verify health:  curl https://api.veri-doc.app/health/ready"
echo "  2. Check frontend: open https://app.veri-doc.app/"
echo "  3. View logs:      docker compose -f docker-compose.production.yml --env-file $ENV_FILE logs -f"
