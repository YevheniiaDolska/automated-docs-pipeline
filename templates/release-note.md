---
title: "n8n [version] release notes"
description: "What's new in n8n [version]: [headline feature], [second feature], performance improvements, and bug fixes."
content_type: release-note
product: both
n8n_version: "[version]"
tags:
  - Reference
---

# n8n [version] release notes

**Released:** [YYYY-MM-DD]

## Highlights

This release includes:

- [Major feature or improvement - 1 sentence]
- [Second highlight - 1 sentence]
- [Third highlight if significant]

## New features

### [Feature name]

[Description of what the feature does and why it's useful. Include a screenshot or code example if helpful.]

```yaml
# Example usage
[configuration or code]
```

### [Second feature name]

[Description]

## Improvements

- **[Area]:** [Improvement description]
- **[Area]:** [Improvement description]
- **Performance:** [Specific performance improvement with numbers if available]

## Bug fixes

- Fixed [issue description] ([#issue-number] if applicable)
- Fixed [issue description]
- Fixed [issue description]

## Breaking changes

[None in this release. OR:]

### [Breaking change title]

**What changed:** [Description]

**Migration required:** [Yes/No]

**Before (v[old]):**

```yaml
[old configuration]
```

**After (v[new]):**

```yaml
[new configuration]
```

**Migration steps:**

1. [Step 1]
2. [Step 2]

## Deprecations

The following features are deprecated and will be removed in [future version]:

| Feature | Deprecated | Removal | Alternative |
|---------|------------|---------|-------------|
| [Feature] | v[current] | v[future] | [New approach] |

## Upgrade notes

### Prerequisites

- Minimum n8n version: [version]
- [Other requirements]

### Upgrade steps

=== "n8n Cloud"

    Cloud instances are updated automatically. No action required.

=== "Self-hosted (Docker)"

    ```bash
    docker pull n8nio/n8n:[version]
    docker-compose up -d
    ```

=== "Self-hosted (npm)"

    ```bash
    npm update -g n8n
    ```

### Post-upgrade checklist

- [ ] Verify workflows are executing correctly
- [ ] Check [specific area] functionality
- [ ] Review [changed feature] configuration

## Known issues

- [Known issue description] - Workaround: [workaround]

## Contributors

Thanks to our community contributors:

- @[username] - [contribution]
- @[username] - [contribution]

## Full changelog

See the [complete changelog on GitHub](https://github.com/n8n-io/n8n/releases/tag/n8n@[version]).
