---
title: "Deployment guide"
description: "Deploy [Product] integrations to production. Covers environment setup, configuration, Docker, Kubernetes, CI/CD, monitoring, and rollback procedures."
content_type: how-to
product: both
tags:
  - How-To
---

# Deployment guide

This guide covers deploying [Product] integrations to production, including environment configuration, containerization, orchestration, and operational best practices.

## Pre-deployment checklist

Before deploying, verify:

- [ ] Using production API keys (not test)
- [ ] Environment variables configured
- [ ] Error handling implemented
- [ ] Retry logic for transient failures
- [ ] Webhook signatures verified
- [ ] Logging with request IDs
- [ ] Health checks implemented
- [ ] Monitoring and alerts set up

## Environment configuration

### Configuration hierarchy

```
1. Environment variables (highest priority)
2. Configuration file
3. Default values (lowest priority)
```

### Production configuration

```javascript
// config/production.js
module.exports = {
  [product]: {
    apiKey: process.env.[PRODUCT]_API_KEY,
    environment: 'live',
    timeout: 30000,
    retries: {
      max: 3,
      initialDelay: 1000
    }
  },
  logging: {
    level: 'info',
    format: 'json'
  }
};
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `[PRODUCT]_API_KEY` | Yes | Production API key |
| `[PRODUCT]_WEBHOOK_SECRET` | If using webhooks | Webhook signing secret |
| `NODE_ENV` | Yes | Set to `production` |
| `LOG_LEVEL` | No | Logging level (default: `info`) |

## Docker deployment

### Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
WORKDIR /app

# Security: Run as non-root
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup
USER appuser

COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json ./

ENV NODE_ENV=production
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - [PRODUCT]_API_KEY=${[PRODUCT]_API_KEY}
      - [PRODUCT]_WEBHOOK_SECRET=${[PRODUCT]_WEBHOOK_SECRET}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

### Build and run

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -d \
  --name myapp \
  -p 3000:3000 \
  -e [PRODUCT]_API_KEY=$[PRODUCT]_API_KEY \
  -e [PRODUCT]_WEBHOOK_SECRET=$[PRODUCT]_WEBHOOK_SECRET \
  myapp:latest
```

## Kubernetes deployment

### Deployment manifest

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: myapp:latest
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: "production"
            - name: [PRODUCT]_API_KEY
              valueFrom:
                secretKeyRef:
                  name: [product]-secrets
                  key: api-key
            - name: [PRODUCT]_WEBHOOK_SECRET
              valueFrom:
                secretKeyRef:
                  name: [product]-secrets
                  key: webhook-secret
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
```

### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: [product]-secrets
type: Opaque
data:
  api-key: <base64-encoded-api-key>
  webhook-secret: <base64-encoded-webhook-secret>
```

```bash
# Create secrets
kubectl create secret generic [product]-secrets \
  --from-literal=api-key=$[PRODUCT]_API_KEY \
  --from-literal=webhook-secret=$[PRODUCT]_WEBHOOK_SECRET
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## CI/CD pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
          docker tag myapp:${{ github.sha }} registry.example.com/myapp:${{ github.sha }}
          docker push registry.example.com/myapp:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/myapp myapp=registry.example.com/myapp:${{ github.sha }}
          kubectl rollout status deployment/myapp
```

### Environment promotion

```
Development → Staging → Production
     ↓           ↓          ↓
 test keys   test keys   live keys
```

## Health checks

### Implementation

```javascript
// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Readiness check (includes dependencies)
app.get('/ready', async (req, res) => {
  try {
    // Check [Product] API connectivity
    await client.ping();

    // Check other dependencies
    await db.ping();

    res.json({ status: 'ready' });
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      error: error.message
    });
  }
});
```

## Monitoring

### Key metrics

| Metric | Alert threshold |
|--------|-----------------|
| API error rate | > 1% |
| API latency (p95) | > 2s |
| Webhook processing time | > 5s |
| Rate limit usage | > 80% |

### Logging

```javascript
// Structured logging for production
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'myapp' },
  transports: [
    new winston.transports.Console()
  ]
});

// Log API requests
logger.info('[Product] request', {
  method: 'create[Resource]',
  duration: 150,
  requestId: result._requestId
});
```

### Alerting

Set up alerts for:

- High error rates
- Increased latency
- Failed health checks
- Rate limit warnings
- Webhook delivery failures

## Rollback procedures

### Quick rollback

```bash
# Kubernetes
kubectl rollout undo deployment/myapp

# Docker Compose
docker-compose pull
docker-compose up -d --force-recreate

# Verify
kubectl rollout status deployment/myapp
```

### Blue-green deployment

```yaml
# Switch traffic from blue to green
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
    version: green  # Change to 'blue' to rollback
```

## Scaling considerations

### Horizontal scaling

- Use stateless application design
- Store sessions externally (Redis)
- Use connection pooling for databases

### Rate limit handling

```javascript
// Distribute load to avoid rate limits
const rateLimiter = new RateLimiter({
  requestsPerMinute: 100,
  burstLimit: 10
});

const makeRequest = async () => {
  await rateLimiter.acquire();
  return client.[resources].create(data);
};
```

## Troubleshooting

### Common deployment issues

| Issue | Solution |
|-------|----------|
| Container won't start | Check logs: `kubectl logs <pod>` |
| Health checks failing | Verify endpoint and dependencies |
| API errors after deploy | Check API key configuration |
| High latency | Review resource limits |

### Debug commands

```bash
# Kubernetes
kubectl logs -f deployment/myapp
kubectl describe pod <pod-name>
kubectl exec -it <pod-name> -- /bin/sh

# Docker
docker logs -f myapp
docker exec -it myapp /bin/sh
```

## Related

- [Configuration reference](../reference/configuration.md)
- [Best practices](./best-practices.md)
- [Error handling](./error-handling.md)
- [Monitoring](../reference/metrics.md)
