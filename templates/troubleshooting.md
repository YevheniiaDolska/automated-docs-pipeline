---
title: "Fix: [Problem description]"
description: "Troubleshoot [problem] in n8n. Common causes include [cause 1], [cause 2], and [cause 3] with step-by-step solutions."
content_type: troubleshooting
product: both
n8n_component: webhook
tags:
  - Troubleshooting
---

# Fix: [Problem description]

[Brief description of the problem symptoms - what the user sees or experiences. Keep factual and specific.]

## Quick diagnosis

| Symptom | Likely cause | Jump to |
|---------|--------------|---------|
| [Symptom 1] | [Cause] | [Cause 1](#cause-1-name) |
| [Symptom 2] | [Cause] | [Cause 2](#cause-2-name) |
| [Symptom 3] | [Cause] | [Cause 3](#cause-3-name) |

## Cause 1: [Most common cause] {#cause-1-name}

**Symptom:** [What specifically indicates this cause - error message, behavior]

**Why this happens:** [Technical explanation of the root cause]

**Fix:**

1. [First step to resolve]
2. [Second step]
3. Verify: [How to confirm the fix worked]

```bash
# Example command or configuration
[fix example]
```

## Cause 2: [Second common cause] {#cause-2-name}

**Symptom:** [Indicator]

**Why this happens:** [Explanation]

**Fix:**

=== "n8n Cloud"

    [Cloud-specific fix]

=== "Self-hosted"

    [Self-hosted fix]

    ```bash
    # Self-hosted specific command
    [command]
    ```

## Cause 3: [Less common cause] {#cause-3-name}

**Symptom:** [Indicator]

**Why this happens:** [Explanation]

**Fix:**

[Solution steps]

!!! warning "Data loss risk"
    [Warning if the fix has risks]

## Cause 4: [Edge case] {#cause-4-name}

**Symptom:** [Indicator]

**Why this happens:** [Explanation]

**Fix:** [Solution]

## Still not working?

If none of the above solutions work:

1. **Check logs:** [Where to find relevant logs]
   ```bash
   [log command]
   ```

2. **Gather information:**
   - n8n version: [how to check]
   - Deployment type: Cloud / Self-hosted
   - Error message (full text)

3. **Get help:**
   - Search [n8n Community](https://community.n8n.io) for similar issues
   - Create a new topic with the information above

## Prevention

To avoid this issue in the future:

- [Preventive measure 1]
- [Preventive measure 2]

## Related

- [[Component] reference](../reference/component.md) - Full parameter documentation
- [Configure [component]](../how-to/configure-component.md) - Correct setup guide
