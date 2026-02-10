---
title: "Security guide"
description: "Security best practices for [Product]. Covers credential management, data protection, secure integration, compliance, and incident response."
content_type: concept
product: both
tags:
  - Concept
  - How-To
---

# Security guide

This guide covers security best practices for integrating with [Product] and protecting your data.

## Security overview

[Product] implements multiple layers of security:

| Layer | Protection |
|-------|------------|
| **Transport** | TLS 1.3 encryption |
| **Authentication** | API keys, OAuth 2.0, JWT |
| **Authorization** | Role-based access control |
| **Data** | AES-256 encryption at rest |
| **Infrastructure** | SOC 2 compliant hosting |

## Credential security

### API key management

| Do | Don't |
|----|-------|
| Store keys in environment variables | Hardcode keys in source code |
| Use secrets managers (Vault, AWS Secrets) | Commit keys to version control |
| Rotate keys regularly (quarterly) | Share keys via chat/email |
| Use separate keys per environment | Use production keys in development |
| Restrict key permissions | Use admin keys everywhere |

### Secure storage

=== "Environment variables"

    ```bash
    # .env (add to .gitignore)
    [PRODUCT]_API_KEY=sk_live_...
    [PRODUCT]_WEBHOOK_SECRET=whsec_...
    ```

    ```javascript
    const apiKey = process.env.[PRODUCT]_API_KEY;
    ```

=== "AWS Secrets Manager"

    ```javascript
    import { SecretsManager } from '@aws-sdk/client-secrets-manager';

    const getApiKey = async () => {
      const client = new SecretsManager();
      const { SecretString } = await client.getSecretValue({
        SecretId: '[product]-api-key'
      });
      return JSON.parse(SecretString).apiKey;
    };
    ```

=== "HashiCorp Vault"

    ```javascript
    import vault from 'node-vault';

    const client = vault({ endpoint: process.env.VAULT_ADDR });
    const { data } = await client.read('secret/data/[product]');
    const apiKey = data.data.api_key;
    ```

### Key rotation

Rotate API keys regularly:

1. **Generate new key** in [Dashboard]([URL])
2. **Update configuration** in your application
3. **Deploy** the change
4. **Verify** functionality
5. **Revoke old key** after confirming

```javascript
// Support graceful rotation with fallback
const apiKeys = [
  process.env.[PRODUCT]_API_KEY_NEW,
  process.env.[PRODUCT]_API_KEY_OLD
].filter(Boolean);
```

## Authentication security

### API key authentication

```javascript
// Secure: Use environment variables
const client = new [Product]Client({
  apiKey: process.env.[PRODUCT]_API_KEY
});

// Never do this
const client = new [Product]Client({
  apiKey: 'sk_live_abc123' // Exposed in code!
});
```

### OAuth security

When implementing OAuth:

1. **Validate state parameter** to prevent CSRF
2. **Store tokens securely** (encrypted, server-side)
3. **Use PKCE** for public clients
4. **Implement token refresh** before expiry
5. **Revoke tokens** when users disconnect

```javascript
// Validate state to prevent CSRF
app.get('/callback', (req, res) => {
  if (req.query.state !== req.session.oauthState) {
    return res.status(403).send('Invalid state');
  }
  // Continue with token exchange
});
```

## Webhook security

### Always verify signatures

```javascript
import crypto from 'crypto';

const verifyWebhookSignature = (payload, signature, secret) => {
  const timestamp = signature.split(',')[0].split('=')[1];
  const sig = signature.split(',')[1].split('=')[1];

  // Prevent replay attacks
  const tolerance = 300; // 5 minutes
  if (Math.abs(Date.now() / 1000 - timestamp) > tolerance) {
    return false;
  }

  // Verify signature
  const expected = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${payload}`)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(sig),
    Buffer.from(expected)
  );
};
```

!!! danger "Never skip signature verification"
    Unsigned webhooks can be forged. Always verify before processing.

### Webhook endpoint security

```javascript
// Rate limit webhook endpoint
import rateLimit from 'express-rate-limit';

const webhookLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100
});

app.post('/webhooks',
  webhookLimiter,
  express.raw({ type: 'application/json' }),
  webhookHandler
);
```

## Data protection

### Data in transit

All API communication uses TLS 1.3:

```javascript
// The SDK enforces HTTPS
const client = new [Product]Client({
  apiKey: process.env.API_KEY
  // All requests use https://api.[product].com
});
```

### Data at rest

[Product] encrypts all data at rest with AES-256.

### Sensitive data handling

| Data type | Recommendation |
|-----------|----------------|
| API keys | Environment variables or secrets manager |
| Webhook secrets | Secrets manager, rotate regularly |
| Access tokens | Encrypted storage, short TTL |
| User data | Minimize collection, encrypt if stored |
| Logs | Redact sensitive fields |

### Log sanitization

```javascript
// Don't log sensitive data
const sanitize = (obj) => {
  const sanitized = { ...obj };
  if (sanitized.apiKey) sanitized.apiKey = '[REDACTED]';
  if (sanitized.password) sanitized.password = '[REDACTED]';
  if (sanitized.token) sanitized.token = '[REDACTED]';
  return sanitized;
};

logger.info('Request', sanitize(requestData));
```

## Input validation

### Validate all input

```javascript
import Joi from 'joi';

const schema = Joi.object({
  email: Joi.string().email().required(),
  amount: Joi.number().positive().max(1000000).required(),
  metadata: Joi.object().unknown(true)
});

const createResource = async (input) => {
  const { error, value } = schema.validate(input);
  if (error) {
    throw new ValidationError(error.details);
  }
  return client.[resources].create(value);
};
```

### Prevent injection

```javascript
// Use parameterized queries, never string concatenation
const resource = await client.[resources].get(sanitizedId);

// Don't construct queries with user input
const bad = `/resources/${userInput}`; // Dangerous!
```

## Network security

### IP allowlisting (optional)

If your infrastructure requires it:

```javascript
// [Product] IP ranges for webhooks
const allowedIPs = [
  '[IP_RANGE_1]',
  '[IP_RANGE_2]'
];

app.post('/webhooks', (req, res, next) => {
  const clientIP = req.ip;
  if (!allowedIPs.some(range => isInRange(clientIP, range))) {
    return res.status(403).send('Forbidden');
  }
  next();
});
```

### Firewall rules

Allow outbound connections to:

| Destination | Port | Purpose |
|-------------|------|---------|
| `api.[product].com` | 443 | API requests |
| `webhooks.[product].com` | 443 | Webhook delivery |

## Error handling security

### Don't expose internal errors

```javascript
// Good: Generic error to client
app.use((error, req, res, next) => {
  logger.error('Internal error', {
    error: error.message,
    stack: error.stack,
    requestId: req.id
  });

  res.status(500).json({
    error: 'An unexpected error occurred',
    requestId: req.id
  });
});

// Bad: Exposing internal details
res.status(500).json({
  error: error.message,
  stack: error.stack // Never expose stack traces!
});
```

## Access control

### Principle of least privilege

```javascript
// Create restricted API key with minimal permissions
const restrictedKey = await client.apiKeys.create({
  name: 'webhook-processor',
  permissions: ['[resources]:read'], // Only what's needed
  ipRestrictions: ['10.0.0.0/8']
});
```

### Role-based access

| Role | Permissions |
|------|-------------|
| Viewer | Read-only access |
| Editor | Create, update |
| Admin | Full access including delete |

## Compliance

### SOC 2

[Product] is SOC 2 Type II certified. Request our report at [security email].

### GDPR

- Data processing agreement available
- Data export via API
- Account deletion upon request

### PCI DSS

[If applicable: compliance level and details]

## Security checklist

### Before going live

- [ ] API keys in environment variables (not code)
- [ ] Different keys for test/production
- [ ] Webhook signatures verified
- [ ] Input validation implemented
- [ ] Error messages don't expose internals
- [ ] Logs don't contain sensitive data
- [ ] HTTPS enforced everywhere
- [ ] Tokens stored securely
- [ ] Minimum necessary permissions

### Regular maintenance

- [ ] Rotate API keys quarterly
- [ ] Review access permissions
- [ ] Audit logs for anomalies
- [ ] Update dependencies
- [ ] Review security advisories

## Incident response

### If credentials are compromised

1. **Immediately revoke** the compromised key in [Dashboard]([URL])
2. **Generate new credentials**
3. **Update your application**
4. **Review logs** for unauthorized access
5. **Contact [security email]** if needed

### Report vulnerabilities

Report security vulnerabilities to [security@product.com].

We follow responsible disclosure and do not pursue legal action against good-faith researchers.

## Related

- [Authentication guide](./authentication.md)
- [Webhooks guide](./webhooks.md)
- [Best practices](./best-practices.md)
