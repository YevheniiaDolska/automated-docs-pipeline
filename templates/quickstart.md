---
title: "[Product] quickstart"
description: "Get started with [Product] in under [X] minutes. Make your first [API call/workflow/integration] with this step-by-step guide."
content_type: tutorial
product: both
tags:
  - Tutorial
---

# [Product] quickstart

Get [Product] running and make your first [API call/workflow] in under [X] minutes. No prior experience required.

## What you'll accomplish

By the end of this quickstart, you'll have:

- [ ] [First outcome]
- [ ] [Second outcome]
- [ ] [Third outcome]

**Time required:** [X] minutes

## Prerequisites

- [ ] [Requirement 1 - with link to get it]
- [ ] [Requirement 2]

## Step 1: [Install/Set up] [Product]

Choose your installation method:

=== "Cloud (Recommended)"

    1. Go to [signup URL]
    2. Create an account
    3. You're ready — skip to Step 2

=== "Docker"

    ```bash
    docker run -d --name [product] \
      -p [port]:[port] \
      [image-name]
    ```

=== "npm"

    ```bash
    npm install -g [package-name]
    [package-name] start
    ```

Verify installation:

```bash
[verification command]
# Expected output: [expected output]
```

## Step 2: [Get credentials/Configure]

[Brief explanation of what credentials are needed and why.]

1. [Go to dashboard/settings]
2. [Create/Copy credential]
3. Save it securely — you'll need it in the next step

```bash
# Set as environment variable
export [VAR_NAME]="your-credential-here"
```

!!! warning "Keep credentials secure"
    Never commit credentials to version control. Use environment variables or a secrets manager.

## Step 3: [Make your first request/Create your first thing]

[One sentence about what this step accomplishes.]

=== "cURL"

    ```bash
    curl -X [METHOD] [URL] \
      -H "Authorization: Bearer $[VAR_NAME]" \
      -H "Content-Type: application/json" \
      -d '{
        "[field]": "[value]"
      }'
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch('[URL]', {
      method: '[METHOD]',
      headers: {
        'Authorization': `Bearer ${process.env.[VAR_NAME]}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        [field]: '[value]'
      })
    });

    const data = await response.json();
    console.log(data);
    ```

=== "Python"

    ```python
    import requests
    import os

    response = requests.[method](
        '[URL]',
        headers={
            'Authorization': f'Bearer {os.environ["[VAR_NAME]"]}',
            'Content-Type': 'application/json'
        },
        json={
            '[field]': '[value]'
        }
    )

    print(response.json())
    ```

**Expected response:**

```json
{
  "status": "success",
  "[field]": "[value]"
}
```

## Step 4: [Verify/Test] the result

[How to confirm it worked.]

1. [Verification step 1]
2. [Verification step 2]
3. You should see: [expected result]

## You're done!

You've successfully [what they accomplished]. Here's what you built:

[Brief summary or diagram of what was created]

## Next steps

Now that you have [Product] running:

| Goal | Resource |
|------|----------|
| Learn the basics | [Tutorial: Build your first [thing]](../getting-started/first-thing.md) |
| Explore features | [How-to guides](../how-to/index.md) |
| Go to production | [Deployment guide](../how-to/deployment.md) |
| API reference | [Complete API docs](../reference/api.md) |

## Common issues

### [Issue 1]

**Error:** `[error message]`

**Fix:** [Solution]

### [Issue 2]

**Error:** `[error message]`

**Fix:** [Solution]

## Get help

- [Community forum]([URL])
- [Discord/Slack]([URL])
- [Support]([URL])
