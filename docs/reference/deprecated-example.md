---
title: "Old Webhook API (Deprecated)"
description: "This API is deprecated. Use the new Webhook node instead."
content_type: reference
maturity: deprecated
deprecated_since: "2024-01-15"
sunset_date: "2024-07-01"
replaced_by: "/reference/nodes/webhook"
tags:
 - Deprecated
 - Webhook
---

## Old Webhook API

This is an example of a deprecated page. When you build the site with MkDocs, it will automatically:

1. Show a deprecation warning banner at the top
1. Lower its ranking in search results
1. Add a canonical tag pointing to the replacement page

## Example Code

```javascript
// OLD WAY (deprecated)
const webhook = new OldWebhook({
 port: 5678
});

// NEW WAY
const webhook = new WebhookNode({
 port: {{ default_port }}
});
```
