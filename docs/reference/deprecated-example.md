---
title: Old Webhook API (Deprecated)
description: This API is deprecated. Use the new Webhook node instead.
content_type: reference
status: deprecated
maturity: deprecated
deprecated_since: '2024-01-15'
removal_date: '2024-07-01'
replacement_url: /reference/nodes/webhook
sunset_date: '2024-07-01'
replaced_by: /reference/nodes/webhook
tags:
- Deprecated
- Webhook
last_reviewed: '2026-02-16'
original_author: JaneDo
---


## Old Webhook API

This is an example of a deprecated page. When you build the site with MkDocs, it will automatically:

\11. Show a deprecation warning banner at the top
\11. Lower its ranking in search results
\11. Add a canonical tag pointing to the replacement page

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

## Next steps

- [Documentation index](index.md)
