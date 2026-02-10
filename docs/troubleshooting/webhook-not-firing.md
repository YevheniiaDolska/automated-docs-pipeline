---
title: "Fix: n8n Webhook trigger not firing"
description: "Troubleshoot n8n Webhook nodes that do not receive requests. Common causes include inactive workflows, wrong URL type, and network configuration."
content_type: troubleshooting
product: both
n8n_component: webhook
tags:
  - Troubleshooting
  - Webhook
  - Nodes
  - Cloud
  - Self-hosted
---

# Fix: n8n Webhook trigger not firing

The Webhook node does not respond to incoming HTTP requests. The sender receives a timeout, connection refused, or 404 error.

## Cause 1: Using Test URL with an inactive editor

**Symptom:** Requests to the Test URL return a timeout or 404 after you close the n8n editor tab.

**Why:** The Test URL (`/webhook-test/...`) is only active while the workflow editor is open and the workflow is in Listening mode. Closing the browser tab deactivates it.

**Fix:** Toggle the workflow to **Active** and use the **Production URL** (`/webhook/...`) instead. The Production URL remains active as long as the workflow is enabled.

## Cause 2: Workflow not activated

**Symptom:** Requests to the Production URL return 404 Not Found.

**Why:** The Production URL only works when the workflow toggle is set to **Active** (green). An inactive workflow does not register its webhook endpoints.

**Fix:** Open the workflow in the editor. Toggle the **Active** switch in the top-right corner. Verify the Production URL returns a response.

## Cause 3: Firewall or reverse proxy blocking requests

**Symptom:** Requests from external services timeout. Local `curl` requests work fine.

**Why:** n8n listens on port 5678 by default. If your server firewall or reverse proxy (Nginx, Caddy, Traefik) does not forward traffic to this port, external requests never reach n8n.

**Fix:**

=== "Docker with Nginx"

    Verify your Nginx config forwards to the n8n container:

    ```nginx
    location /webhook/ {
        proxy_pass http://n8n:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

=== "Direct install"

    Check that port 5678 is open:

    ```bash
    sudo ufw allow 5678
    # or
    sudo firewall-cmd --add-port=5678/tcp --permanent
    ```

## Cause 4: Incorrect WEBHOOK_URL environment variable

**Symptom:** The Webhook node shows a URL that does not match your domain. External services cannot reach it.

**Why:** n8n uses the `WEBHOOK_URL` environment variable to generate webhook URLs. If this is set to `http://localhost:5678` (the default), external services cannot resolve `localhost`.

**Fix:** Set `WEBHOOK_URL` to your public-facing URL:

```bash
export WEBHOOK_URL=https://n8n.yourdomain.com
```

## Still not working?

1. Check the n8n logs for errors: `docker logs n8n` or the n8n process output.
2. Test with a minimal `curl` command from the same network as n8n.
3. Verify the HTTP method matches (the Webhook node only responds to the configured method).

## Related

- [Webhook node reference](../reference/nodes/webhook.md)
- [Configure Webhook authentication](../how-to/configure-webhook-trigger.md)
