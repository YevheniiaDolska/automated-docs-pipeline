---
title: "Changelog"
description: "[Product] changelog: all releases, new features, improvements, bug fixes, and breaking changes in chronological order."
content_type: reference
product: both
tags:

  - Reference

---

## Changelog

All notable changes to [Product] are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/). [Product] uses [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- [Feature in development]

### Changed

- [Change in development]

---

## [X.Y.Z] - YYYY-MM-DD

### Added

- **[Feature name]:** [Description of new feature and its benefits]
- [Another new feature]

### Changed

- **[Component]:** [Description of what changed and why]
- [Another change]

### Deprecated

- **[Feature name]:** [What's deprecated, timeline for removal, and migration path]

### Removed

- **[Feature name]:** [What was removed and what to use instead]

### Fixed

- **[Bug description]:** [What was fixed] ([#issue-number])
- [Another bug fix]

### Security

- **[Vulnerability]:** [Security fix description]

---

## [X.Y.Z-1] - YYYY-MM-DD

### Added

- [Feature]

### Fixed

- [Bug fix]

---

## [X.Y.Z-2] - YYYY-MM-DD

### Breaking Changes

!!! warning "Breaking changes in this release"
    Review these changes before upgrading.

#### [Breaking change 1]

**What changed:** [Description]

**Migration:**

```diff

- old_method(arg)
+ new_method(arg, options)

```

#### [Breaking change 2]

**What changed:** [Description]

**Migration:** See [migration guide](../how-to/migrate-x-to-y.md).

### Added

- [New feature]

### Changed

- [Change]

---

## Version history

| Version | Date | Highlights |
| --------- | ------ | ------------ |
| [X.Y.Z] | YYYY-MM-DD | [Key feature] |
| [X.Y.Z-1] | YYYY-MM-DD | [Key feature] |
| [X.Y.Z-2] | YYYY-MM-DD | [Key feature] |

---

## Upgrade guides

- [Upgrade from X.0 to X.1](../how-to/upgrade-x0-x1.md)
- [Upgrade from (X-1).x to X.0](../how-to/upgrade-major.md)

## API changelog

For API-specific changes, see [API Changelog](./api-changelog.md).

---

[Unreleased]: <https://github.com/[org]/[repo]/compare/vX.Y.Z...HEAD>
[X.Y.Z]: <https://github.com/[org]/[repo]/compare/vX.Y.Z-1...vX.Y.Z>
[X.Y.Z-1]: <https://github.com/[org]/[repo]/compare/vX.Y.Z-2...vX.Y.Z-1>
[X.Y.Z-2]: <https://github.com/[org]/[repo]/releases/tag/vX.Y.Z-2>
