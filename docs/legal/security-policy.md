---
title: VeriDoc security policy
description: Security policy for VeriDoc platform covering infrastructure security,
  encryption, authentication, access controls, and incident response procedures.
content_type: reference
product: cloud
tags:
- Reference
last_reviewed: '2026-03-28'
original_author: Kroha
---


# VeriDoc security policy

VeriDoc is an automated documentation pipeline platform that processes
customer documentation content. This security policy describes the
technical and organizational measures we implement to protect your data
and maintain service integrity.

## Infrastructure security

### Hosting environment

VeriDoc runs on dedicated infrastructure in Hetzner Cloud data centers
located in Germany (EU).

| Component | Technology | Security configuration |
|-----------|------------|----------------------|
| Application server | Ubuntu 22.04 LTS | Automated security patches, SSH key-only access |
| API service | FastAPI (Python 3.12) | CORS-restricted, rate-limited, JWT-authenticated |
| Database | PostgreSQL 16 | Encrypted at rest (AES-256), TLS connections |
| Cache | Redis 7 | Memory-only, no content persistence, private network |
| Task queue | Celery + Redis | Isolated worker processes, task timeout enforcement |
| Reverse proxy | Nginx | TLS 1.3, HTTP/2, security headers, rate limiting |

### Network security

1. All public endpoints require TLS 1.3 encryption. Older TLS versions
   are rejected.
1. Database and Redis ports are bound to `127.0.0.1` only -- no external
   access.
1. SSH access uses Ed25519 keys exclusively. Password authentication is
   disabled.
1. Firewall rules allow only ports 80 (redirect to 443), 443 (HTTPS), and
   22 (SSH from allowlisted IPs).

## Authentication and access control

### User authentication

| Mechanism | Implementation |
|-----------|---------------|
| Password hashing | PBKDF2-SHA256 with 600,000 iterations |
| Token format | JWT (PyJWT) with HS256 signing |
| Token expiry | 24 hours |
| Session management | Stateless JWT, no server-side sessions |
| Rate limiting | 60 requests per minute per user |

### API authentication

All API endpoints except `/health` and `/auth/register` require a valid
JWT token in the `Authorization: Bearer <token>` header.

```text
POST /auth/login
Content-Type: application/json

{"email": "user@example.com", "password": "your-password"}

Response: {"token": "eyJ...", "expires_in": 86400}
```

### Webhook verification

Incoming LemonSqueezy webhooks are verified using HMAC-SHA256 signatures.
Requests without a valid `X-Signature` header are rejected with HTTP 403.

## Encryption

### Data in transit

All data transmitted between clients and VeriDoc servers is encrypted
with TLS 1.3. The Nginx configuration enforces:

1. TLS 1.3 only (TLS 1.2 and below are disabled).
1. Strong cipher suites with forward secrecy.
1. HSTS headers with 1-year max-age.
1. OCSP stapling for certificate validation.

### Data at rest

| Data type | Encryption method |
|-----------|-------------------|
| PostgreSQL database | AES-256 (filesystem-level encryption) |
| Database backups | AES-256 encrypted archives |
| License files | AES-256-GCM with HKDF key derivation |
| Application secrets | Environment variables, not stored in code |

## Data processing security

### Pipeline execution

When VeriDoc processes your documentation:

1. Content is loaded into memory for processing.
1. Intermediate results are stored in the encrypted PostgreSQL database.
1. Pipeline workers run in isolated Celery processes with 1-hour timeouts.
1. Failed pipeline runs are logged to Sentry with PII scrubbing.

### LLM processing (opt-in)

When AI features are enabled, document sections are sent to LLM providers
over TLS-encrypted connections. Each request contains only the minimum
content necessary for the specific enhancement.

| Provider | Transport | Data retention by provider |
|----------|-----------|---------------------------|
| Anthropic (Claude) | HTTPS/TLS 1.3 | Not used for training |
| Groq | HTTPS/TLS 1.3 | Not used for training |
| DeepSeek | HTTPS/TLS 1.3 | Refer to provider policy |
| OpenAI | HTTPS/TLS 1.3 | Not used for training (API usage) |

Disable AI features to ensure no documentation content leaves VeriDoc
infrastructure.

## Backup and disaster recovery

| Measure | Configuration |
|---------|---------------|
| Backup frequency | Daily at 02:00 UTC |
| Backup retention | 30 days |
| Backup encryption | AES-256 |
| Restore testing | Weekly automated restore verification |
| Recovery time objective (RTO) | 4 hours |
| Recovery point objective (RPO) | 24 hours |

## Monitoring and incident response

### Monitoring

| System | Purpose | Alert threshold |
|--------|---------|-----------------|
| Health checks | Service availability | 2 consecutive failures (every 5 minutes) |
| Sentry | Error tracking | Real-time error capture |
| Log rotation | Log management | Daily rotation, 30-day retention |
| Latency monitoring | Performance tracking | Warning at 2,000 ms, critical at 5,000 ms |

### Incident response procedure

| Phase | Timeline | Actions |
|-------|----------|---------|
| **Detection** | Automated | Health check alerts via email within 10 minutes of failure |
| **Triage** | Within 1 hour | Assess severity, identify root cause |
| **Containment** | Within 2 hours | Isolate affected systems, prevent data loss |
| **Resolution** | Within 4 hours (critical) | Restore service, deploy fix |
| **Notification** | Within 72 hours | Notify affected customers per DPA obligations |
| **Post-mortem** | Within 7 days | Document root cause, implement preventive measures |

### Severity levels

| Level | Definition | Response time | Example |
|-------|------------|---------------|---------|
| **Critical** | Service down, data at risk | 1 hour | Database corruption, security breach |
| **High** | Feature degraded, no data risk | 4 hours | API errors, slow response times |
| **Medium** | Minor issue, workaround available | 24 hours | Non-critical feature bug |
| **Low** | Cosmetic or documentation issue | 72 hours | UI display issue |

## Vulnerability management

1. **Dependency scanning.** Python dependencies are reviewed weekly for
   known vulnerabilities using `pip-audit`.
1. **OS patching.** Security patches are applied within 48 hours of
   release.
1. **Container updates.** Docker base images are rebuilt monthly with
   latest security patches.
1. **Penetration testing.** External penetration testing is conducted
   annually.

## Responsible disclosure

If you discover a security vulnerability in VeriDoc:

1. Email <security@veri-doc.app> with a description of the vulnerability.
1. Include steps to reproduce the issue.
1. Allow 90 days for remediation before public disclosure.
1. Do not access or modify other users' data during testing.

We do not pursue legal action against security researchers who follow
responsible disclosure practices.

## Compliance standards

| Standard | Status |
|----------|--------|
| GDPR | Compliant (EU data processing, DPA available) |
| TLS 1.3 | Enforced on all endpoints |
| Password security | PBKDF2-SHA256, 600,000 iterations |
| Data retention | Defined retention periods with automated deletion |

## Contact information

For security inquiries or to report a vulnerability:

- Email: <security@veri-doc.app>
- Response time: within 24 hours for security reports

**Last updated:** March 28, 2026

## Next steps

- Review the [terms of service](terms-of-service.md)
- Review the [privacy policy](privacy-policy.md)
- Review the [data processing agreement](data-processing-agreement.md)
