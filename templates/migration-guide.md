---
title: "Migrate from [old] to [new]"
description: "Complete migration guide from [old version/system] to [new version/system]. Covers breaking changes, step-by-step migration, and rollback procedures."
content_type: how-to
product: both
tags:

  - How-To

---

## Migrate from [old] to [new]

This guide helps you migrate from [old version/system] to [new version/system]. Follow these steps to ensure a smooth transition.

## Why migrate?

[New version] provides:

- [Key benefit 1]
- [Key benefit 2]
- [Performance improvement]
- [New capability]

## Before you begin

### Prerequisites

- [ ] Current version: [minimum old version]
- [ ] Backup of [what to backup]
- [ ] [X] minutes of downtime window
- [ ] Test environment available

### Compatibility check

Verify your setup is compatible:

```bash
## Check current version
[version check command]

## Verify dependencies
[dependency check]

```text

## Breaking changes

!!! warning "Review before migrating"
    The following changes may affect your existing setup.

### [Breaking change 1]

**What changed:** [Description]

**Impact:** [Who is affected and how]

**Before (v[old]):**

```yaml
[old configuration or code]
```

**After (v[new]):**

```yaml
[new configuration or code]

```text

**Migration action:** [What to do]

### [Breaking change 2]

**What changed:** [Description]

**Before:**

```javascript
// Old API
[old code]
```

**After:**

```javascript
// New API
[new code]

```text

## Migration steps

### Step 1: Backup current setup

```bash
## Backup command
[backup command]
```

Verify backup:

```bash
[verification command]

```text

### Step 2: Update dependencies

```bash
## Update to compatible versions
[update commands]
```

### Step 3: Update configuration

Replace deprecated settings:

| Old setting | New setting | Notes |
| ------------- | ------------- | ------- |
| `[old_key]` | `[new_key]` | [Note] |
| `[old_key2]` | Removed | [Alternative] |

### Step 4: Update code

=== "Automated migration"

    Run the migration script:

    ```bash
    npx @/migrate [options]

```text

=== "Manual migration"

    1. [Manual step 1]
    1. [Manual step 2]
    1. [Manual step 3]

### Step 5: Test the migration

```bash
## Run tests
[test command]
```

**Checklist:**

- [ ] [Test case 1]
- [ ] [Test case 2]
- [ ] [Test case 3]

### Step 6: Deploy

=== " Cloud"

    [Cloud migration steps]

=== "Self-hosted"

    ```bash
    # Deploy new version
    [deployment command]

```text

## Post-migration verification

After migration, verify:

1. **Functionality:** [What to test]
1. **Performance:** [Metrics to check]
1. **Logs:** [What to look for]

```bash
## Verification commands
[commands]
```

## Rollback procedure

If issues occur, rollback to the previous version:

### Quick rollback

```bash
## Rollback command
[rollback command]

```text

### Full rollback

1. Stop current version
1. Restore from backup:

   ```bash
   [restore command]
```

1. Restart services
1. Verify functionality

## Troubleshooting migration issues

### [Common issue 1]

**Symptom:** [What you see]

**Cause:** [Why it happens]

**Fix:**

```bash
[fix command]

```text

### [Common issue 2]

**Symptom:** [What you see]

**Fix:** [Solution]

## Migration timeline

| Phase | Duration | Description |
| ------- | ---------- | ------------- |
| Preparation | [time] | Backup, test environment |
| Migration | [time] | Apply changes |
| Verification | [time] | Test functionality |
| **Total** | **[total time]** | |

## Getting help

- [Migration FAQ](./migration-faq.md)
- [Community forum](https://community..io)
- [Support contact](mailto:support@.io)

## Related

- [[New version] release notes](../reference/release-notes-new.md)
- [Breaking changes reference](../reference/breaking-changes.md)
