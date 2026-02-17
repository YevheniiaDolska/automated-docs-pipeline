---
title: "Changelog"
description: "Track product releases with clear impact, upgrade guidance, and migration steps for every audience."
content_type: reference
product: both
tags:
  - Reference
---

# Changelog

Use this template to publish releases that users can trust and act on quickly. Every entry should answer: what changed, who is affected, and what action is required.

## Publishing rules

- Keep newest release at the top.
- Use exact date format: `YYYY-MM-DD`.
- Separate additive changes from breaking changes.
- Link migration guide for any behavior change.
- Include security fixes in a dedicated section.

## Versioning policy

This changelog follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- [New capability in development]

### Changed

- [Behavior improvement in development]

### Deprecated

- [Feature planned for removal]

### Fixed

- [Bug fix in development]

### Security

- [Security hardening in development]

---

## [X.Y.Z] - YYYY-MM-DD

### Release summary

One paragraph with the most important impact for users and operators.

### Added

- **[Feature name]:** [What it does and why it matters]
- **[Feature name]:** [Any limits, regions, or plans]

### Changed

- **[Component]:** [What changed, old behavior vs new behavior]
- **[API]:** [Payload/response/latency changes if relevant]

### Deprecated

- **[Deprecated item]:** [Removal date and replacement]

### Removed

- **[Removed item]:** [Migration target link]

### Fixed

- **[Issue]:** [Customer-visible symptom and fix]

### Security

- **[CVE/issue]:** [Scope, severity, recommended action]

### Upgrade action required

- [ ] [Any required environment/config change]
- [ ] [Any migration command or script]
- [ ] [Any client SDK minimum version]

### Migration example

```diff
- client.createTask({ retries: 0 })
+ client.createTask({ retryPolicy: { maxAttempts: 1 } })
```

## Support window

| Version line | Status | End of support |
| --- | --- | --- |
| `X.y` | Active | YYYY-MM-DD |
| `W.y` | Security fixes only | YYYY-MM-DD |
| `V.y` | End-of-life | YYYY-MM-DD |

## Template QA checklist

- [ ] Frontmatter complete
- [ ] Date and version are concrete
- [ ] Breaking changes called out explicitly
- [ ] Migration link included when needed
- [ ] No ambiguous wording like "may" or "might"
