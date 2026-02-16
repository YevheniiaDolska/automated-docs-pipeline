---
title: "[Component] reference"
description: "Complete parameter reference for the [Component] including [key feature 1], [key feature 2], and configuration examples."
content_type: reference
product: both
tags:

  - Reference

---

## [Component] reference

The [Component] [is/does what]. [One sentence with key capability.]

## Parameters

| Parameter | Type | Default | Description |
| ----------- | ------ | --------- | ------------- |
| **[param1]** | `string` | — | [What it does]. Required. |
| **[param2]** | `enum` | `option1` | [What it does]. Options: `option1`, `option2`, `option3` |
| **[param3]** | `number` | `0` | [What it does]. Range: 0-100 |
| **[param4]** | `boolean` | `false` | [What it does] |

## [Section 1: Main functionality]

[Detailed explanation of primary use case.]

### [Subsection]

[Specifics with examples.]

=== "Option A"

    [Details and code for option A]

    ```yaml
    config:
      option: A

```text

=== "Option B"

    [Details and code for option B]

    ```yaml
    config:
      option: B
```

## [Section 2: Secondary functionality]

[Explanation of secondary features.]

## Output

The [Component] outputs data in this structure:

```json
{
  "field1": "value",
  "field2": {
    "nested": "data"
  }
}

```text

| Field | Type | Description |
| ------- | ------ | ------------- |
| `field1` | `string` | [What it contains] |
| `field2` | `object` | [What it contains] |

## Environment variables

| Variable | Default | Description |
| ---------- | --------- | ------------- |
| `[VAR_NAME]` | `[default]` | [What it controls] |
| `[VAR_NAME_2]` | `[default]` | [What it controls] |

## Examples

### [Example 1: Common use case]

```yaml
# Configuration for [use case]
[complete working example]
```

### [Example 2: Advanced use case]

```yaml
# Configuration for [advanced use case]
[complete working example]

```text

## Limitations

- [Limitation 1]
- [Limitation 2]

## Related

- [Configure [component]](../how-to/configure-component.md) - Step-by-step setup
- [[Component] not working](../troubleshooting/component-issue.md) - Common issues
- [How [component] works](../concepts/component-concept.md) - Architecture explanation
