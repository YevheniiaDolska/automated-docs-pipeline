---
title: " [version] release notes"
description: "What's new in  [version]: [headline feature], [second feature], performance improvements, and bug fixes."
content_type: release-note
product: both
tags:

  - Reference

---

## [version] release notes

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
## Example usage
[configuration or code]

```text

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

```text

**Migration steps:**

1. [Step 1]
1. [Step 2]

## Deprecations

The following features are deprecated and will be removed in [future version]:

| Feature | Deprecated | Removal | Alternative |
| --------- | ------------ | --------- | ------------- |
| [Feature] | v[current] | v[future] | [New approach] |

## Upgrade notes

### Prerequisites

- Minimum  version: [version]
- [Other requirements]

### Upgrade steps

=== " Cloud"

    Cloud instances are updated automatically. No action required.

=== "Self-hosted (Docker)"

    ```bash
    docker pull n8nio/:[version]
    docker-compose up -d
```

=== "Self-hosted (npm)"

    ```bash
    npm update -g

```text

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

See the [complete changelog on GitHub](https://github.com/-io//releases/tag/@[version]).
