"""Built-in template library for technical documentation.

This module provides a comprehensive collection of reusable templates for
various documentation types following industry standards and best practices.
All templates support variable substitution and multiple style guides.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class TemplateCategory(Enum):
    """Categories of documentation templates."""
    TUTORIAL = "tutorial"
    HOW_TO = "how_to"
    CONCEPT = "concept"
    REFERENCE = "reference"
    TROUBLESHOOTING = "troubleshooting"
    RELEASE = "release"
    API = "api"
    ARCHITECTURE = "architecture"
    ONBOARDING = "onboarding"
    SECURITY = "security"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    QUICKSTART = "quickstart"
    CHANGELOG = "changelog"
    FAQ = "faq"
    WEBHOOK = "webhook"
    SDK = "sdk"
    DATA_MODEL = "data_model"
    DEPLOYMENT = "deployment"
    PERFORMANCE = "performance"
    TESTING = "testing"
    CONTRIBUTING = "contributing"
    GLOSSARY = "glossary"
    ADMIN_GUIDE = "admin_guide"
    CONFIGURATION = "configuration"
    CLI_REFERENCE = "cli_reference"


@dataclass
class BuiltInTemplate:
    """Built-in documentation template."""
    id: str
    name: str
    category: TemplateCategory
    description: str
    content: str
    variables: Dict[str, str]
    tags: List[str]
    style_guide: str = "technical"


class TemplateLibrary:
    """Collection of built-in documentation templates."""

    def __init__(self) -> None:
        """Initialize the template library."""
        self.templates: Dict[str, BuiltInTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all built-in templates."""
        # Tutorial Template
        self.templates["tutorial"] = BuiltInTemplate(
            id="tutorial",
            name="Step-by-Step Tutorial",
            category=TemplateCategory.TUTORIAL,
            description="Learning-oriented guide for beginners",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: tutorial
product: {{ product | default('both') }}
tags:
  - tutorial
  - {{ primary_tag }}
---

# {{ title }}

{{ intro_paragraph }}

## What you'll learn

By the end of this tutorial, you'll be able to:
- {{ learning_outcome_1 }}
- {{ learning_outcome_2 }}
- {{ learning_outcome_3 }}

## Prerequisites

Before you begin, make sure you have:
- {{ prerequisite_1 }}
- {{ prerequisite_2 }}
- {{ prerequisite_3 | default('Basic understanding of the topic') }}

## Step 1: {{ step_1_title }}

{{ step_1_description }}

```{{ code_language | default('bash') }}
{{ step_1_code }}
```

**What's happening here:**
{{ step_1_explanation }}

## Step 2: {{ step_2_title }}

{{ step_2_description }}

```{{ code_language | default('bash') }}
{{ step_2_code }}
```

!!! tip "Pro tip"
    {{ step_2_tip | default('Take your time with this step') }}

## Step 3: {{ step_3_title }}

{{ step_3_description }}

```{{ code_language | default('bash') }}
{{ step_3_code }}
```

## Testing your work

To verify everything is working:

1. {{ test_step_1 }}
2. {{ test_step_2 }}
3. {{ test_step_3 }}

You should see:
```
{{ expected_output }}
```

## Common issues

### Issue: {{ common_issue_1_title }}

**Solution:** {{ common_issue_1_solution }}

### Issue: {{ common_issue_2_title | default('Installation fails') }}

**Solution:** {{ common_issue_2_solution | default('Check prerequisites') }}

## Next steps

Now that you've completed this tutorial:
- {{ next_step_1 }}
- {{ next_step_2 }}
- Check out [{{ related_tutorial }}]({{ related_tutorial_link }})

## Summary

In this tutorial, you learned how to:
✅ {{ summary_point_1 }}
✅ {{ summary_point_2 }}
✅ {{ summary_point_3 }}

{{ closing_message | default('Great job completing this tutorial!') }}
""",
            variables={
                "title": "Tutorial Title",
                "description": "What this tutorial teaches",
                "intro_paragraph": "Brief introduction to the topic",
                "learning_outcome_1": "First learning outcome",
                "step_1_title": "Setting up",
                "step_1_code": "# Your code here"
            },
            tags=["tutorial", "learning", "step-by-step"],
            style_guide="technical"
        )

        # How-To Guide Template
        self.templates["how_to"] = BuiltInTemplate(
            id="how_to",
            name="Task-Oriented How-To Guide",
            category=TemplateCategory.HOW_TO,
            description="Problem-solving guide for specific tasks",
            content="""---
title: "How to {{ task_action }}"
description: "{{ task_description }}"
content_type: how-to
product: {{ product | default('both') }}
tags:
  - how-to
  - {{ primary_tag }}
---

# How to {{ task_action }}

{{ problem_statement }}

## When to use this

This approach is useful when:
- {{ use_case_1 }}
- {{ use_case_2 }}
- {{ use_case_3 }}

## Requirements

- {{ requirement_1 }}
- {{ requirement_2 }}
- {{ requirement_3 | default('Access to the system') }}

## Solution

### Option 1: {{ option_1_name }}

{{ option_1_description }}

```{{ code_language | default('bash') }}
{{ option_1_code }}
```

**Pros:**
- {{ option_1_pro_1 }}
- {{ option_1_pro_2 }}

**Cons:**
- {{ option_1_con_1 }}
- {{ option_1_con_2 | default('May require additional setup') }}

### Option 2: {{ option_2_name | default('Alternative approach') }}

{{ option_2_description | default('An alternative way to achieve the same result') }}

```{{ code_language | default('bash') }}
{{ option_2_code | default('# Alternative code') }}
```

## Verification

To confirm it worked:

```{{ verification_language | default('bash') }}
{{ verification_code }}
```

Expected result:
```
{{ expected_result }}
```

## Troubleshooting

If you encounter `{{ error_message }}`:
1. {{ troubleshooting_step_1 }}
2. {{ troubleshooting_step_2 }}
3. {{ troubleshooting_step_3 | default('Check the logs for more details') }}

## Related tasks

- [How to {{ related_task_1 }}]({{ related_task_1_link }})
- [How to {{ related_task_2 }}]({{ related_task_2_link }})

## Additional resources

- {{ resource_1 }}
- {{ resource_2 | default('Official documentation') }}
""",
            variables={
                "task_action": "accomplish specific task",
                "task_description": "Clear description of what this achieves",
                "problem_statement": "The specific problem this solves",
                "use_case_1": "Primary use case",
                "requirement_1": "Main requirement"
            },
            tags=["how-to", "task", "solution"],
            style_guide="technical"
        )

        # Concept Explanation Template
        self.templates["concept"] = BuiltInTemplate(
            id="concept",
            name="Concept Explanation",
            category=TemplateCategory.CONCEPT,
            description="Understanding-oriented conceptual documentation",
            content="""---
title: "Understanding {{ concept_name }}"
description: "{{ concept_description }}"
content_type: concept
product: {{ product | default('both') }}
tags:
  - concept
  - {{ primary_tag }}
---

# Understanding {{ concept_name }}

{{ concept_definition }}

## Overview

{{ concept_overview }}

## Why {{ concept_name }} matters

{{ concept_importance }}

Key benefits:
- **{{ benefit_1_title }}**: {{ benefit_1_description }}
- **{{ benefit_2_title }}**: {{ benefit_2_description }}
- **{{ benefit_3_title }}**: {{ benefit_3_description }}

## How it works

{{ how_it_works_intro }}

```mermaid
{{ diagram_type | default('graph LR') }}
    {{ diagram_content }}
```

### Core components

1. **{{ component_1_name }}**
   {{ component_1_description }}

2. **{{ component_2_name }}**
   {{ component_2_description }}

3. **{{ component_3_name }}**
   {{ component_3_description }}

## Key principles

### {{ principle_1_title }}

{{ principle_1_explanation }}

### {{ principle_2_title }}

{{ principle_2_explanation }}

## Common patterns

### Pattern: {{ pattern_1_name }}

**When to use:** {{ pattern_1_when }}

**Example:**
```{{ code_language | default('python') }}
{{ pattern_1_code }}
```

### Pattern: {{ pattern_2_name | default('Alternative pattern') }}

**When to use:** {{ pattern_2_when | default('In different scenarios') }}

## Comparison with alternatives

| Aspect | {{ concept_name }} | {{ alternative_1 }} | {{ alternative_2 | default('Other') }} |
|--------|-------------------|---------------------|------------------------|
| {{ comparison_aspect_1 }} | {{ concept_value_1 }} | {{ alt1_value_1 }} | {{ alt2_value_1 }} |
| {{ comparison_aspect_2 }} | {{ concept_value_2 }} | {{ alt1_value_2 }} | {{ alt2_value_2 }} |
| {{ comparison_aspect_3 }} | {{ concept_value_3 }} | {{ alt1_value_3 }} | {{ alt2_value_3 }} |

## Best practices

1. **{{ best_practice_1 }}**
   {{ best_practice_1_details }}

2. **{{ best_practice_2 }}**
   {{ best_practice_2_details }}

3. **{{ best_practice_3 }}**
   {{ best_practice_3_details }}

## Common misconceptions

❌ **Misconception:** {{ misconception_1 }}
✅ **Reality:** {{ reality_1 }}

❌ **Misconception:** {{ misconception_2 | default('It\'s too complex') }}
✅ **Reality:** {{ reality_2 | default('It\'s actually straightforward when understood properly') }}

## Further reading

- {{ further_reading_1 }}
- {{ further_reading_2 }}
- [Deep dive into {{ related_concept }}]({{ related_concept_link }})

## Summary

{{ summary_paragraph }}

Key takeaways:
- {{ takeaway_1 }}
- {{ takeaway_2 }}
- {{ takeaway_3 }}
""",
            variables={
                "concept_name": "Core Concept",
                "concept_description": "What this concept is about",
                "concept_definition": "A clear, concise definition",
                "concept_overview": "High-level explanation",
                "concept_importance": "Why this matters"
            },
            tags=["concept", "explanation", "understanding"],
            style_guide="technical"
        )

        # API Reference Template
        self.templates["api_reference"] = BuiltInTemplate(
            id="api_reference",
            name="API Reference Documentation",
            category=TemplateCategory.REFERENCE,
            description="Detailed API endpoint or function reference",
            content="""---
title: "{{ api_name }} API Reference"
description: "{{ api_description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - api
  - reference
  - {{ primary_tag }}
---

# {{ api_name }} API Reference

{{ api_overview }}

## Base URL

```
{{ base_url }}
```

## Authentication

{{ auth_description }}

```{{ auth_example_language | default('bash') }}
{{ auth_example }}
```

## Endpoints

### {{ endpoint_1_method }} {{ endpoint_1_path }}

{{ endpoint_1_description }}

**Parameters**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| {{ param_1_name }} | {{ param_1_type }} | {{ param_1_required }} | {{ param_1_desc }} | {{ param_1_default | default('None') }} |
| {{ param_2_name }} | {{ param_2_type }} | {{ param_2_required }} | {{ param_2_desc }} | {{ param_2_default | default('None') }} |

**Request Example**

```{{ request_language | default('bash') }}
{{ request_example }}
```

**Response Example**

```json
{{ response_example }}
```

**Response Schema**

| Field | Type | Description |
|-------|------|-------------|
| {{ response_field_1 }} | {{ response_type_1 }} | {{ response_desc_1 }} |
| {{ response_field_2 }} | {{ response_type_2 }} | {{ response_desc_2 }} |

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | {{ status_200_desc | default('Success') }} |
| 400 | {{ status_400_desc | default('Bad Request') }} |
| 401 | {{ status_401_desc | default('Unauthorized') }} |
| 404 | {{ status_404_desc | default('Not Found') }} |
| 500 | {{ status_500_desc | default('Internal Server Error') }} |

### {{ endpoint_2_method | default('POST') }} {{ endpoint_2_path | default('/api/v2/resource') }}

{{ endpoint_2_description | default('Another endpoint description') }}

## Error Handling

All errors follow this format:

```json
{
  "error": {
    "code": "{{ error_code }}",
    "message": "{{ error_message }}",
    "details": {{ error_details | default('{}') }}
  }
}
```

## Rate Limiting

{{ rate_limit_description | default('API calls are rate limited') }}

- **Limit:** {{ rate_limit | default('100 requests per minute') }}
- **Headers:** `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Pagination

{{ pagination_description | default('Large result sets are paginated') }}

```{{ pagination_example_language | default('bash') }}
{{ pagination_example | default('GET /api/resource?page=2&limit=50') }}
```

## Webhooks

{{ webhook_description | default('Webhooks for real-time events') }}

### Webhook Events

| Event | Description | Payload |
|-------|-------------|---------|
| {{ webhook_event_1 }} | {{ webhook_desc_1 }} | {{ webhook_payload_1 }} |
| {{ webhook_event_2 }} | {{ webhook_desc_2 }} | {{ webhook_payload_2 }} |

## SDKs and Libraries

- **Python**: `pip install {{ sdk_python | default('api-client') }}`
- **Node.js**: `npm install {{ sdk_node | default('api-client') }}`
- **Go**: `go get {{ sdk_go | default('github.com/org/api-client') }}`

## Changelog

### {{ version | default('v2.0.0') }} - {{ release_date | default('2024-01-01') }}

- {{ changelog_item_1 | default('Added new endpoint') }}
- {{ changelog_item_2 | default('Improved error messages') }}
- {{ changelog_item_3 | default('Performance optimizations') }}

## Support

{{ support_info | default('For API support, contact api@example.com') }}
""",
            variables={
                "api_name": "API Name",
                "api_description": "What this API does",
                "base_url": "https://api.example.com/v1",
                "endpoint_1_method": "GET",
                "endpoint_1_path": "/resource"
            },
            tags=["api", "reference", "endpoints"],
            style_guide="technical"
        )

        # Troubleshooting Template
        self.templates["troubleshooting"] = BuiltInTemplate(
            id="troubleshooting",
            name="Troubleshooting Guide",
            category=TemplateCategory.TROUBLESHOOTING,
            description="Problem-diagnosis-solution format",
            content="""---
title: "Troubleshooting {{ feature_name }}"
description: "{{ troubleshooting_description }}"
content_type: troubleshooting
product: {{ product | default('both') }}
tags:
  - troubleshooting
  - {{ primary_tag }}
---

# Troubleshooting {{ feature_name }}

{{ intro_paragraph }}

## Quick diagnostics

Run these checks first:

```{{ diagnostic_language | default('bash') }}
{{ diagnostic_commands }}
```

## Common issues

### Issue: {{ issue_1_title }}

**Symptoms:**
- {{ issue_1_symptom_1 }}
- {{ issue_1_symptom_2 }}
- {{ issue_1_symptom_3 | default('System not responding as expected') }}

**Possible causes:**
1. {{ issue_1_cause_1 }}
2. {{ issue_1_cause_2 }}
3. {{ issue_1_cause_3 | default('Configuration issue') }}

**Solutions:**

#### Solution 1: {{ issue_1_solution_1_title }}

```{{ solution_language | default('bash') }}
{{ issue_1_solution_1_code }}
```

{{ issue_1_solution_1_explanation }}

#### Solution 2: {{ issue_1_solution_2_title | default('Alternative fix') }}

```{{ solution_language | default('bash') }}
{{ issue_1_solution_2_code | default('# Alternative solution') }}
```

{{ issue_1_solution_2_explanation | default('Try this if the first solution doesn\'t work') }}

**Prevention:**
{{ issue_1_prevention }}

---

### Issue: {{ issue_2_title }}

**Symptoms:**
- {{ issue_2_symptom_1 }}
- {{ issue_2_symptom_2 }}

**Root cause:**
{{ issue_2_root_cause }}

**Solution:**

```{{ solution_language | default('bash') }}
{{ issue_2_solution }}
```

**Verification:**

```{{ verification_language | default('bash') }}
{{ issue_2_verification }}
```

---

### Issue: {{ issue_3_title | default('Performance degradation') }}

**Symptoms:**
- {{ issue_3_symptom_1 | default('Slow response times') }}
- {{ issue_3_symptom_2 | default('High resource usage') }}

**Diagnosis:**

Check these metrics:
```{{ metrics_language | default('bash') }}
{{ issue_3_metrics | default('# Check system metrics') }}
```

**Solution:**

{{ issue_3_solution | default('Optimize configuration settings') }}

## Error messages reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `{{ error_1 }}` | {{ error_1_meaning }} | {{ error_1_solution }} |
| `{{ error_2 }}` | {{ error_2_meaning }} | {{ error_2_solution }} |
| `{{ error_3 | default('TIMEOUT_ERROR') }}` | {{ error_3_meaning | default('Operation timed out') }} | {{ error_3_solution | default('Increase timeout value') }} |

## Debug mode

Enable debug logging:

```{{ debug_language | default('bash') }}
{{ debug_enable_command }}
```

Debug log location: `{{ debug_log_path | default('/var/log/app/debug.log') }}`

## Getting help

If these solutions don't resolve your issue:

1. Collect diagnostic information:
   ```{{ diagnostic_collection_language | default('bash') }}
   {{ diagnostic_collection_command | default('# Collect logs and system info') }}
   ```

2. Check the [FAQ]({{ faq_link | default('#') }})

3. Contact support with:
   - Error messages
   - Steps to reproduce
   - Diagnostic output

## Related documentation

- [{{ related_doc_1 }}]({{ related_doc_1_link }})
- [{{ related_doc_2 }}]({{ related_doc_2_link }})
- [Known issues]({{ known_issues_link | default('#') }})
""",
            variables={
                "feature_name": "Feature or Component",
                "troubleshooting_description": "Common issues and solutions",
                "issue_1_title": "Main problem",
                "issue_1_symptom_1": "First symptom",
                "issue_1_solution_1_title": "Primary fix"
            },
            tags=["troubleshooting", "debugging", "problems"],
            style_guide="technical"
        )

        # Architecture Decision Record Template
        self.templates["adr"] = BuiltInTemplate(
            id="adr",
            name="Architecture Decision Record",
            category=TemplateCategory.ARCHITECTURE,
            description="Document architectural decisions",
            content="""# ADR-{{ adr_number }}: {{ decision_title }}

## Status

{{ status | default('Proposed') }}

## Context

{{ context_description }}

### Problem Statement

{{ problem_statement }}

### Constraints

- {{ constraint_1 }}
- {{ constraint_2 }}
- {{ constraint_3 | default('Budget/time limitations') }}

### Assumptions

- {{ assumption_1 }}
- {{ assumption_2 | default('Current architecture remains stable') }}

## Decision

{{ decision_description }}

### Chosen Option: {{ chosen_option }}

{{ chosen_option_details }}

## Rationale

{{ rationale }}

Key factors in this decision:
1. {{ factor_1 }}
2. {{ factor_2 }}
3. {{ factor_3 }}

## Consequences

### Positive

- ✅ {{ positive_consequence_1 }}
- ✅ {{ positive_consequence_2 }}
- ✅ {{ positive_consequence_3 }}

### Negative

- ❌ {{ negative_consequence_1 }}
- ❌ {{ negative_consequence_2 | default('Increased complexity') }}

### Neutral

- ➖ {{ neutral_consequence_1 | default('Requires team training') }}

## Alternatives Considered

### Option 1: {{ alternative_1_name }}

**Description:** {{ alternative_1_description }}

**Pros:**
- {{ alternative_1_pro_1 }}
- {{ alternative_1_pro_2 }}

**Cons:**
- {{ alternative_1_con_1 }}
- {{ alternative_1_con_2 }}

**Rejection reason:** {{ alternative_1_rejection }}

### Option 2: {{ alternative_2_name | default('Do nothing') }}

**Description:** {{ alternative_2_description | default('Keep current approach') }}

**Pros:**
- {{ alternative_2_pro_1 | default('No migration needed') }}

**Cons:**
- {{ alternative_2_con_1 | default('Technical debt accumulation') }}

## Implementation

### Migration Strategy

{{ migration_strategy }}

### Timeline

- {{ timeline_phase_1 }}
- {{ timeline_phase_2 }}
- {{ timeline_phase_3 | default('Completion and validation') }}

### Success Metrics

- {{ metric_1 }}
- {{ metric_2 }}
- {{ metric_3 | default('System stability maintained') }}

## References

- {{ reference_1 }}
- {{ reference_2 | default('Internal architecture documentation') }}

## History

- {{ date | default('2024-01-01') }}: Initial proposal
- {{ review_date | default('2024-01-15') }}: Review and approval

## Authors

- {{ author_1 }}
- {{ author_2 | default('Architecture Team') }}

## Reviewers

- {{ reviewer_1 }}
- {{ reviewer_2 | default('Technical Lead') }}
""",
            variables={
                "adr_number": "001",
                "decision_title": "Architectural Decision",
                "status": "Proposed",
                "context_description": "Why this decision is needed",
                "chosen_option": "Selected solution"
            },
            tags=["architecture", "adr", "decision"],
            style_guide="technical"
        )

        # Release Notes Template
        self.templates["release_notes"] = BuiltInTemplate(
            id="release_notes",
            name="Release Notes",
            category=TemplateCategory.RELEASE,
            description="Product release documentation",
            content="""---
title: "Release Notes - {{ version }}"
description: "{{ release_description }}"
content_type: release-note
product: {{ product | default('both') }}
tags:
  - release
  - {{ version_tag }}
---

# Release Notes - {{ version }}

**Release Date:** {{ release_date | default('2024-01-01') }}
**Release Type:** {{ release_type | default('Minor') }}

## Highlights

{{ release_highlights }}

### Key Features

- 🎉 **{{ highlight_feature_1 }}**: {{ highlight_feature_1_desc }}
- 🚀 **{{ highlight_feature_2 }}**: {{ highlight_feature_2_desc }}
- 💡 **{{ highlight_feature_3 }}**: {{ highlight_feature_3_desc }}

## New Features

### {{ new_feature_1_title }}

{{ new_feature_1_description }}

**Usage:**
```{{ code_language | default('bash') }}
{{ new_feature_1_example }}
```

### {{ new_feature_2_title }}

{{ new_feature_2_description }}

## Improvements

- **{{ improvement_1_area }}**: {{ improvement_1_description }}
- **{{ improvement_2_area }}**: {{ improvement_2_description }}
- **{{ improvement_3_area }}**: {{ improvement_3_description }}

## Bug Fixes

- Fixed: {{ bug_fix_1 }}
- Fixed: {{ bug_fix_2 }}
- Fixed: {{ bug_fix_3 }}
- Fixed: {{ bug_fix_4 | default('Minor UI inconsistencies') }}

## Breaking Changes

{% if breaking_changes %}
⚠️ **This release contains breaking changes**

### {{ breaking_change_1_title }}

**Impact:** {{ breaking_change_1_impact }}

**Migration:**
```{{ migration_language | default('bash') }}
{{ breaking_change_1_migration }}
```

### {{ breaking_change_2_title | default('API Changes') }}

{{ breaking_change_2_description | default('Some API endpoints have changed') }}
{% else %}
No breaking changes in this release.
{% endif %}

## Deprecations

{% if deprecations %}
The following features are deprecated and will be removed in {{ deprecation_removal_version | default('v3.0.0') }}:

- {{ deprecation_1 }}
- {{ deprecation_2 | default('Legacy API endpoints') }}

**Recommended alternatives:**
- Use {{ alternative_1 }} instead of {{ deprecation_1 }}
{% else %}
No deprecations in this release.
{% endif %}

## Security Updates

{% if security_updates %}
🔒 **Security fixes included:**

- {{ security_fix_1 }}
- {{ security_fix_2 | default('Updated dependencies') }}
{% else %}
No security updates in this release.
{% endif %}

## Performance Improvements

- {{ performance_improvement_1 }}
- {{ performance_improvement_2 | default('Optimized database queries') }}
- {{ performance_improvement_3 | default('Reduced memory usage') }}

## Known Issues

- {{ known_issue_1 | default('None reported') }}
- Workaround: {{ known_issue_1_workaround | default('Will be fixed in next release') }}

## Upgrade Instructions

### From {{ previous_version | default('v1.0.0') }}

1. {{ upgrade_step_1 | default('Back up your data') }}
2. {{ upgrade_step_2 | default('Stop the application') }}
3. {{ upgrade_step_3 | default('Install the new version') }}
4. {{ upgrade_step_4 | default('Run migration scripts') }}
5. {{ upgrade_step_5 | default('Restart the application') }}

### Database Migrations

{% if database_migrations %}
Run the following migrations:
```sql
{{ database_migration_script }}
```
{% else %}
No database migrations required.
{% endif %}

### Configuration Changes

{% if config_changes %}
Update your configuration:
```{{ config_language | default('yaml') }}
{{ config_changes_example }}
```
{% else %}
No configuration changes required.
{% endif %}

## Contributors

Thanks to all contributors who made this release possible:

- {{ contributor_1 }}
- {{ contributor_2 }}
- {{ contributor_3 | default('And all our community members') }}

## Downloads

- [Download {{ version }}]({{ download_link }})
- [Docker Image]({{ docker_image_link | default('docker.io/org/app:' + version) }})
- [Release Assets]({{ assets_link }})

## Documentation

- [Upgrade Guide]({{ upgrade_guide_link }})
- [API Documentation]({{ api_docs_link }})
- [Migration Guide]({{ migration_guide_link }})

## Support

For questions or issues:
- 📧 Email: {{ support_email | default('support@example.com') }}
- 💬 Slack: {{ slack_channel | default('#support') }}
- 🐛 Issues: {{ issues_link }}

## Next Release

**Planned for:** {{ next_release_date | default('Q2 2024') }}
**Preview:** {{ next_release_preview | default('Performance improvements and new integrations') }}
""",
            variables={
                "version": "v2.0.0",
                "release_description": "Major feature release",
                "release_date": "2024-01-01",
                "release_highlights": "Summary of key changes",
                "new_feature_1_title": "New Feature Name"
            },
            tags=["release", "changelog", "version"],
            style_guide="technical"
        )

        # Security Documentation Template
        self.templates["security"] = BuiltInTemplate(
            id="security",
            name="Security Documentation",
            category=TemplateCategory.SECURITY,
            description="Security policies and procedures",
            content="""---
title: "{{ security_doc_title }}"
description: "{{ security_doc_description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - security
  - {{ security_tag }}
---

# {{ security_doc_title }}

**Classification:** {{ classification | default('Internal') }}
**Last Updated:** {{ last_updated | default('2024-01-01') }}
**Owner:** {{ owner | default('Security Team') }}

## Overview

{{ security_overview }}

## Security Architecture

```mermaid
graph TB
    {{ security_architecture_diagram }}
```

## Authentication

### Methods Supported

| Method | Description | Use Case |
|--------|-------------|----------|
| {{ auth_method_1 }} | {{ auth_method_1_desc }} | {{ auth_method_1_use }} |
| {{ auth_method_2 }} | {{ auth_method_2_desc }} | {{ auth_method_2_use }} |
| {{ auth_method_3 | default('API Keys') }} | {{ auth_method_3_desc | default('Token-based auth') }} | {{ auth_method_3_use | default('API access') }} |

### Implementation

```{{ auth_code_language | default('python') }}
{{ auth_implementation_example }}
```

## Authorization

### Role-Based Access Control (RBAC)

| Role | Permissions | Description |
|------|------------|-------------|
| {{ role_1 }} | {{ role_1_perms }} | {{ role_1_desc }} |
| {{ role_2 }} | {{ role_2_perms }} | {{ role_2_desc }} |
| {{ role_3 | default('Admin') }} | {{ role_3_perms | default('Full access') }} | {{ role_3_desc | default('System administrator') }} |

### Permission Model

```{{ permission_code_language | default('yaml') }}
{{ permission_model }}
```

## Data Protection

### Encryption at Rest

- **Algorithm:** {{ encryption_algorithm | default('AES-256') }}
- **Key Management:** {{ key_management }}
- **Scope:** {{ encryption_scope }}

### Encryption in Transit

- **Protocol:** {{ transit_protocol | default('TLS 1.3') }}
- **Certificate:** {{ certificate_type }}
- **Cipher Suites:** {{ cipher_suites | default('Modern cipher suites only') }}

### Data Classification

| Classification | Description | Handling Requirements |
|----------------|-------------|----------------------|
| {{ class_1 | default('Public') }} | {{ class_1_desc }} | {{ class_1_handling }} |
| {{ class_2 | default('Internal') }} | {{ class_2_desc }} | {{ class_2_handling }} |
| {{ class_3 | default('Confidential') }} | {{ class_3_desc }} | {{ class_3_handling }} |
| {{ class_4 | default('Restricted') }} | {{ class_4_desc }} | {{ class_4_handling }} |

## Security Controls

### Input Validation

```{{ validation_language | default('python') }}
{{ input_validation_example }}
```

### Output Encoding

```{{ encoding_language | default('python') }}
{{ output_encoding_example }}
```

### Rate Limiting

- **Default Limit:** {{ default_rate_limit | default('100 req/min') }}
- **Authenticated Limit:** {{ auth_rate_limit | default('1000 req/min') }}
- **Implementation:** {{ rate_limit_implementation }}

## Security Headers

```{{ headers_language | default('nginx') }}
{{ security_headers_config }}
```

## Vulnerability Management

### Scanning Schedule

- **SAST:** {{ sast_schedule | default('Every commit') }}
- **DAST:** {{ dast_schedule | default('Weekly') }}
- **Dependencies:** {{ dep_scan_schedule | default('Daily') }}
- **Infrastructure:** {{ infra_scan_schedule | default('Monthly') }}

### Response Procedures

1. **Critical (CVSS 9.0-10.0):** {{ critical_response }}
2. **High (CVSS 7.0-8.9):** {{ high_response }}
3. **Medium (CVSS 4.0-6.9):** {{ medium_response }}
4. **Low (CVSS 0.1-3.9):** {{ low_response }}

## Incident Response

### Contact Information

- **Security Team:** {{ security_email | default('security@example.com') }}
- **Hotline:** {{ security_hotline | default('+1-555-SEC-RITY') }}
- **On-Call:** {{ oncall_procedure }}

### Response Phases

1. **Detection & Analysis**
   - {{ detection_procedure }}

2. **Containment**
   - {{ containment_procedure }}

3. **Eradication**
   - {{ eradication_procedure }}

4. **Recovery**
   - {{ recovery_procedure }}

5. **Post-Incident**
   - {{ postincident_procedure }}

## Compliance

### Standards

- ✅ {{ compliance_standard_1 | default('SOC 2 Type II') }}
- ✅ {{ compliance_standard_2 | default('ISO 27001') }}
- ✅ {{ compliance_standard_3 | default('GDPR') }}

### Audit Log Requirements

```{{ audit_language | default('json') }}
{{ audit_log_format }}
```

## Security Testing

### Penetration Testing

- **Frequency:** {{ pentest_frequency | default('Annually') }}
- **Scope:** {{ pentest_scope }}
- **Last Test:** {{ last_pentest | default('2023-12-01') }}

### Security Review Checklist

- [ ] {{ checklist_item_1 | default('Authentication properly implemented') }}
- [ ] {{ checklist_item_2 | default('Authorization checks in place') }}
- [ ] {{ checklist_item_3 | default('Input validation complete') }}
- [ ] {{ checklist_item_4 | default('Sensitive data encrypted') }}
- [ ] {{ checklist_item_5 | default('Security headers configured') }}
- [ ] {{ checklist_item_6 | default('Logging and monitoring enabled') }}
- [ ] {{ checklist_item_7 | default('Error handling secure') }}
- [ ] {{ checklist_item_8 | default('Dependencies up to date') }}

## Best Practices

1. **{{ practice_1_title }}**
   {{ practice_1_description }}

2. **{{ practice_2_title }}**
   {{ practice_2_description }}

3. **{{ practice_3_title }}**
   {{ practice_3_description }}

## References

- [OWASP Top 10](https://owasp.org/top10/)
- {{ reference_1 }}
- {{ reference_2 | default('Internal Security Policy') }}
""",
            variables={
                "security_doc_title": "Security Documentation",
                "security_doc_description": "Security policies and procedures",
                "security_overview": "Overview of security measures",
                "auth_method_1": "OAuth 2.0",
                "role_1": "User"
            },
            tags=["security", "compliance", "authentication"],
            style_guide="technical"
        )

        # Integration Guide Template
        self.templates["integration_guide"] = BuiltInTemplate(
            id="integration_guide",
            name="Integration Guide",
            category=TemplateCategory.HOW_TO,
            description="Step-by-step third-party integration guide",
            content="""---
title: "Integrating {{ service_name }} with {{ product_name }}"
description: "Complete guide to integrate {{ service_name }} with your application"
content_type: how-to
tags:
  - integration
  - {{ service_tag }}
---

# Integrating {{ service_name }}

{{ intro_paragraph }}

## Prerequisites

- {{ prerequisite_1 }}
- {{ prerequisite_2 }}
- {{ service_name }} account with {{ required_plan | default('Basic') }} plan

## Step 1: Get API Credentials

1. Log in to [{{ service_name }} Dashboard]({{ service_dashboard_url }})
2. Navigate to **Settings** → **API Keys**
3. Create a new API key with the following permissions:
   - {{ permission_1 }}
   - {{ permission_2 }}
4. Copy your credentials:
   - API Key: `{{ api_key_example | default('sk_live_...') }}`
   - Secret: `{{ secret_example | default('secret_...') }}`

## Step 2: Install Dependencies

```{{ package_manager | default('npm') }}
{{ install_command }}
```

## Step 3: Configure {{ service_name }}

```{{ config_language | default('javascript') }}
{{ config_code }}
```

## Step 4: Implement Core Functionality

### {{ functionality_1_title }}

```{{ code_language | default('javascript') }}
{{ functionality_1_code }}
```

### {{ functionality_2_title }}

```{{ code_language | default('javascript') }}
{{ functionality_2_code }}
```

## Step 5: Handle Webhooks

Configure webhook endpoint:

```{{ webhook_language | default('javascript') }}
{{ webhook_code }}
```

Register webhook URL in {{ service_name }}:
1. Go to [Webhook Settings]({{ webhook_settings_url }})
2. Add endpoint: `{{ webhook_endpoint | default('https://your-app.com/webhooks/service') }}`
3. Select events:
   - {{ webhook_event_1 }}
   - {{ webhook_event_2 }}

## Testing

### Test in Development

```bash
{{ test_dev_command }}
```

### Test in Production

```bash
{{ test_prod_command }}
```

## Error Handling

| Error Code | Meaning | Solution |
|------------|---------|----------|
| {{ error_1_code }} | {{ error_1_meaning }} | {{ error_1_solution }} |
| {{ error_2_code }} | {{ error_2_meaning }} | {{ error_2_solution }} |

## Best Practices

1. **{{ best_practice_1_title }}**
   {{ best_practice_1_description }}

2. **{{ best_practice_2_title }}**
   {{ best_practice_2_description }}

## Monitoring

Set up monitoring for:
- API rate limits: {{ rate_limit | default('100 req/min') }}
- Webhook failures
- Response times

## Support

- Documentation: [{{ service_name }} Docs]({{ service_docs_url }})
- Support: {{ support_email | default('support@service.com') }}
- Status Page: [{{ service_name }} Status]({{ status_page_url }})
""",
            variables={
                "service_name": "Third-Party Service",
                "product_name": "Your Product",
                "intro_paragraph": "This guide walks through integrating...",
                "prerequisite_1": "Node.js 18+",
                "install_command": "npm install service-sdk"
            },
            tags=["integration", "guide", "third-party"],
            style_guide="technical"
        )

        # Migration Guide Template
        self.templates["migration_guide"] = BuiltInTemplate(
            id="migration_guide",
            name="Migration Guide",
            category=TemplateCategory.HOW_TO,
            description="Version migration and upgrade guide",
            content="""---
title: "Migrating from {{ from_version }} to {{ to_version }}"
description: "Step-by-step guide to upgrade from {{ from_version }} to {{ to_version }}"
content_type: how-to
tags:
  - migration
  - upgrade
  - {{ version_tag }}
---

# Migration Guide: {{ from_version }} → {{ to_version }}

**Estimated time:** {{ estimated_time | default('30-60 minutes') }}
**Difficulty:** {{ difficulty | default('Medium') }}
**Downtime required:** {{ downtime | default('Yes, ~10 minutes') }}

## Overview

{{ migration_overview }}

### What's Changed

#### Breaking Changes
- {{ breaking_change_1 }}
- {{ breaking_change_2 }}

#### New Features
- {{ new_feature_1 }}
- {{ new_feature_2 }}

#### Deprecations
- {{ deprecation_1 }}
- {{ deprecation_2 | default('Legacy API endpoints') }}

## Pre-Migration Checklist

- [ ] Current version confirmed: `{{ from_version }}`
- [ ] Backup created
- [ ] Dependencies checked
- [ ] Test environment ready
- [ ] Rollback plan prepared
- [ ] Team notified

## Step 1: Backup Current System

```bash
# Backup database
{{ backup_db_command | default('pg_dump mydb > backup.sql') }}

# Backup configuration
{{ backup_config_command | default('cp -r /etc/myapp /backup/config') }}

# Backup application
{{ backup_app_command | default('tar -czf app-backup.tar.gz /app') }}
```

## Step 2: Update Dependencies

### Package Updates

```{{ package_manager | default('npm') }}
{{ update_dependencies_command }}
```

### Compatibility Matrix

| Dependency | Old Version | New Version | Action Required |
|------------|-------------|-------------|-----------------|
| {{ dep_1_name }} | {{ dep_1_old }} | {{ dep_1_new }} | {{ dep_1_action }} |
| {{ dep_2_name }} | {{ dep_2_old }} | {{ dep_2_new }} | {{ dep_2_action }} |

## Step 3: Code Changes

### Change 1: {{ code_change_1_title }}

**Before ({{ from_version }}):**
```{{ code_language | default('javascript') }}
{{ old_code_1 }}
```

**After ({{ to_version }}):**
```{{ code_language | default('javascript') }}
{{ new_code_1 }}
```

### Change 2: {{ code_change_2_title }}

**Before:**
```{{ code_language | default('javascript') }}
{{ old_code_2 }}
```

**After:**
```{{ code_language | default('javascript') }}
{{ new_code_2 }}
```

## Step 4: Database Migrations

```sql
-- Migration script for {{ to_version }}
{{ migration_sql }}
```

Run migration:
```bash
{{ run_migration_command }}
```

## Step 5: Configuration Updates

Update `{{ config_file | default('config.yml') }}`:

```yaml
# Old configuration
{{ old_config }}

# New configuration
{{ new_config }}
```

## Step 6: Deploy New Version

```bash
# Stop application
{{ stop_command }}

# Deploy new version
{{ deploy_command }}

# Start application
{{ start_command }}
```

## Step 7: Verification

### Smoke Tests

```bash
{{ smoke_test_command }}
```

### Health Checks

- [ ] API responding: `curl {{ health_endpoint | default('http://localhost/health') }}`
- [ ] Database connected
- [ ] Background jobs running
- [ ] Metrics reporting

## Rollback Procedure

If issues occur:

```bash
# Stop new version
{{ rollback_stop_command }}

# Restore database
{{ rollback_db_command }}

# Deploy old version
{{ rollback_deploy_command }}

# Start old version
{{ rollback_start_command }}
```

## Post-Migration

- [ ] Monitor error rates for 24 hours
- [ ] Check performance metrics
- [ ] Update documentation
- [ ] Remove deprecated code (after 30 days)
- [ ] Archive backups

## Troubleshooting

### Issue: {{ common_issue_1 }}
**Solution:** {{ solution_1 }}

### Issue: {{ common_issue_2 }}
**Solution:** {{ solution_2 }}

## Resources

- [Detailed Changelog]({{ changelog_url }})
- [API Migration Guide]({{ api_migration_url }})
- [Support Channel]({{ support_url }})
""",
            variables={
                "from_version": "v1.0.0",
                "to_version": "v2.0.0",
                "migration_overview": "This major version includes...",
                "breaking_change_1": "API endpoint changes",
                "estimated_time": "30-60 minutes"
            },
            tags=["migration", "upgrade", "version"],
            style_guide="technical"
        )

        # Authentication Flow Template
        self.templates["auth_flow"] = BuiltInTemplate(
            id="auth_flow",
            name="Authentication Flow Documentation",
            category=TemplateCategory.ARCHITECTURE,
            description="OAuth2, SSO, and authentication flow documentation",
            content="""---
title: "{{ auth_type }} Authentication Flow"
description: "Implementation guide for {{ auth_type }} authentication"
content_type: reference
tags:
  - authentication
  - security
  - {{ auth_tag }}
---

# {{ auth_type }} Authentication Flow

{{ auth_overview }}

## Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant AuthServer as Auth Server
    participant API
    participant ResourceServer as Resource Server

    {{ mermaid_sequence }}
```

## Prerequisites

- {{ prerequisite_1 }}
- {{ prerequisite_2 }}
- Registered OAuth application with:
  - Client ID: `{{ client_id_format | default('your-client-id') }}`
  - Client Secret: `{{ client_secret_format | default('your-client-secret') }}`
  - Redirect URI: `{{ redirect_uri | default('https://app.com/callback') }}`

## Step 1: Authorization Request

```{{ code_language | default('javascript') }}
{{ auth_request_code }}
```

**Parameters:**
- `response_type`: {{ response_type | default('code') }}
- `client_id`: Your application's client ID
- `redirect_uri`: Registered callback URL
- `scope`: {{ scopes | default('openid profile email') }}
- `state`: Random string for CSRF protection

## Step 2: User Authorization

User is redirected to:
```
{{ auth_url_example }}
```

User actions:
1. Enter credentials
2. Review permissions
3. Approve/Deny access

## Step 3: Authorization Code

After approval, user is redirected to:
```
{{ callback_example }}
```

Extract authorization code:
```{{ code_language | default('javascript') }}
{{ extract_code }}
```

## Step 4: Token Exchange

Exchange authorization code for tokens:

```{{ code_language | default('javascript') }}
{{ token_exchange_code }}
```

**Response:**
```json
{
  "access_token": "{{ access_token_format | default('eyJhbGc...') }}",
  "token_type": "Bearer",
  "expires_in": {{ expires_in | default('3600') }},
  "refresh_token": "{{ refresh_token_format | default('def502...') }}",
  "id_token": "{{ id_token_format | default('eyJhbGc...') }}"
}
```

## Step 5: Access Protected Resources

Use access token in requests:

```{{ code_language | default('javascript') }}
{{ api_request_code }}
```

## Token Management

### Refresh Token Flow

```{{ code_language | default('javascript') }}
{{ refresh_token_code }}
```

### Token Storage

{% if storage_method == 'cookie' %}
**Secure Cookie Storage:**
```{{ code_language | default('javascript') }}
{{ cookie_storage_code }}
```
{% else %}
**Secure Local Storage:**
```{{ code_language | default('javascript') }}
{{ local_storage_code }}
```
{% endif %}

## Security Considerations

### PKCE (Proof Key for Code Exchange)

For public clients (SPAs, mobile apps):

```{{ code_language | default('javascript') }}
{{ pkce_code }}
```

### State Parameter

Always validate state to prevent CSRF:

```{{ code_language | default('javascript') }}
{{ state_validation_code }}
```

### Token Validation

```{{ code_language | default('javascript') }}
{{ token_validation_code }}
```

## Implementation Examples

### {{ framework_1 | default('Express.js') }}

```javascript
{{ express_implementation }}
```

### {{ framework_2 | default('React') }}

```javascript
{{ react_implementation }}
```

## Error Handling

| Error Code | Description | Action |
|------------|-------------|--------|
| `invalid_request` | {{ invalid_request_desc }} | {{ invalid_request_action }} |
| `unauthorized_client` | {{ unauthorized_desc }} | {{ unauthorized_action }} |
| `access_denied` | {{ denied_desc }} | {{ denied_action }} |
| `invalid_grant` | {{ invalid_grant_desc }} | {{ invalid_grant_action }} |

## Logout Flow

```{{ code_language | default('javascript') }}
{{ logout_flow_code }}
```

## Testing

### Test Credentials

- Test User: `{{ test_user | default('test@example.com') }}`
- Test Password: `{{ test_password | default('TestPass123!') }}`
- Test Client ID: `{{ test_client_id }}`

### Testing Tools

```bash
# Test authorization flow
{{ test_auth_command }}

# Test token refresh
{{ test_refresh_command }}
```

## Compliance

- ✅ {{ compliance_1 | default('OAuth 2.0 RFC 6749') }}
- ✅ {{ compliance_2 | default('OpenID Connect 1.0') }}
- ✅ {{ compliance_3 | default('PKCE RFC 7636') }}

## Resources

- [OAuth 2.0 Specification](https://oauth.net/2/)
- [{{ auth_provider | default('Auth Provider') }} Documentation]({{ provider_docs_url }})
- [Security Best Practices]({{ security_docs_url }})
""",
            variables={
                "auth_type": "OAuth 2.0",
                "auth_overview": "This document describes the OAuth 2.0 flow",
                "client_id_format": "your-client-id",
                "auth_url_example": "https://auth.example.com/authorize?..."
            },
            tags=["authentication", "oauth", "security"],
            style_guide="technical"
        )

        # Runbook Template
        self.templates["runbook"] = BuiltInTemplate(
            id="runbook",
            name="Operations Runbook",
            category=TemplateCategory.OPERATIONS,
            description="Step-by-step operational procedures",
            content="""# Runbook: {{ runbook_title }}

**Purpose:** {{ runbook_purpose }}
**Criticality:** {{ criticality | default('Medium') }}
**Expected Duration:** {{ duration | default('30 minutes') }}
**Last Updated:** {{ last_updated | default('2024-01-01') }}

## Prerequisites

### Access Requirements

- [ ] {{ access_req_1 }}
- [ ] {{ access_req_2 }}
- [ ] {{ access_req_3 | default('VPN access') }}

### Tools Required

- {{ tool_1 }}
- {{ tool_2 }}
- {{ tool_3 | default('SSH client') }}

### Pre-checks

```{{ precheck_language | default('bash') }}
{{ precheck_commands }}
```

Expected output:
```
{{ expected_precheck_output }}
```

## Procedure

### Step 1: {{ step_1_title }}

**Time:** {{ step_1_time | default('5 minutes') }}

```{{ step_1_language | default('bash') }}
{{ step_1_commands }}
```

**Verification:**
```{{ step_1_verify_language | default('bash') }}
{{ step_1_verification }}
```

✅ **Success Criteria:** {{ step_1_success }}

⚠️ **If this fails:** {{ step_1_failure_action }}

---

### Step 2: {{ step_2_title }}

**Time:** {{ step_2_time | default('10 minutes') }}

```{{ step_2_language | default('bash') }}
{{ step_2_commands }}
```

**Verification:**
```{{ step_2_verify_language | default('bash') }}
{{ step_2_verification }}
```

✅ **Success Criteria:** {{ step_2_success }}

---

### Step 3: {{ step_3_title }}

**Time:** {{ step_3_time | default('5 minutes') }}

```{{ step_3_language | default('bash') }}
{{ step_3_commands }}
```

**Verification:**
```{{ step_3_verify_language | default('bash') }}
{{ step_3_verification }}
```

✅ **Success Criteria:** {{ step_3_success }}

## Rollback Procedure

⚠️ **When to rollback:** {{ rollback_criteria }}

### Rollback Step 1: {{ rollback_step_1 }}

```{{ rollback_language | default('bash') }}
{{ rollback_step_1_commands }}
```

### Rollback Step 2: {{ rollback_step_2 }}

```{{ rollback_language | default('bash') }}
{{ rollback_step_2_commands }}
```

### Rollback Verification

```{{ rollback_verify_language | default('bash') }}
{{ rollback_verification }}
```

## Post-Procedure Checklist

- [ ] {{ post_check_1 | default('Verify service health') }}
- [ ] {{ post_check_2 | default('Check monitoring dashboards') }}
- [ ] {{ post_check_3 | default('Review logs for errors') }}
- [ ] {{ post_check_4 | default('Update documentation if needed') }}
- [ ] {{ post_check_5 | default('Notify stakeholders of completion') }}

## Monitoring

### Key Metrics to Watch

| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| {{ metric_1 }} | {{ metric_1_normal }} | {{ metric_1_alert }} |
| {{ metric_2 }} | {{ metric_2_normal }} | {{ metric_2_alert }} |
| {{ metric_3 | default('CPU Usage') }} | {{ metric_3_normal | default('< 70%') }} | {{ metric_3_alert | default('> 90%') }} |

### Dashboard Links

- [{{ dashboard_1_name }}]({{ dashboard_1_link }})
- [{{ dashboard_2_name }}]({{ dashboard_2_link }})

## Troubleshooting

### Common Issues

#### Issue: {{ common_issue_1 }}

**Solution:**
```{{ issue_1_solution_language | default('bash') }}
{{ common_issue_1_solution }}
```

#### Issue: {{ common_issue_2 }}

**Solution:**
```{{ issue_2_solution_language | default('bash') }}
{{ common_issue_2_solution }}
```

## Emergency Contacts

| Role | Name | Contact | Escalation Level |
|------|------|---------|------------------|
| {{ contact_role_1 }} | {{ contact_name_1 }} | {{ contact_info_1 }} | Primary |
| {{ contact_role_2 }} | {{ contact_name_2 }} | {{ contact_info_2 }} | Secondary |
| {{ contact_role_3 | default('Manager') }} | {{ contact_name_3 | default('On-call') }} | {{ contact_info_3 | default('PagerDuty') }} | Escalation |

## Automation

This procedure can be automated using:
```{{ automation_language | default('ansible') }}
{{ automation_script | default('# Automation script/playbook') }}
```

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| {{ change_date_1 | default('2024-01-01') }} | {{ change_author_1 }} | {{ change_desc_1 | default('Initial version') }} |
| {{ change_date_2 | default('2024-01-15') }} | {{ change_author_2 }} | {{ change_desc_2 | default('Added rollback procedure') }} |

## References

- {{ reference_1 }}
- {{ reference_2 | default('Internal Operations Guide') }}
- [Related Runbook: {{ related_runbook }}]({{ related_runbook_link }})
""",
            variables={
                "runbook_title": "Operational Procedure",
                "runbook_purpose": "What this runbook accomplishes",
                "step_1_title": "Preparation",
                "step_1_commands": "# Commands for step 1",
                "rollback_criteria": "If any step fails"
            },
            tags=["operations", "runbook", "procedure"],
            style_guide="technical"
        )

        # Quickstart Template
        self.templates["quickstart"] = BuiltInTemplate(
            id="quickstart",
            name="Quickstart Guide",
            category=TemplateCategory.QUICKSTART,
            description="Get started in under 5 minutes",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: tutorial
product: {{ product | default('both') }}
tags:
  - quickstart
  - {{ primary_tag }}
---

# {{ title }}

{{ intro_paragraph }}

## Before you begin

You need:

- {{ prerequisite_1 }}
- {{ prerequisite_2 }}

## Install {{ product_name | default('the product') }}

```{{ install_language | default('bash') }}
{{ install_command }}
```

Verify the installation:

```bash
{{ verify_install_command }}
```

Expected output:

```
{{ verify_install_output }}
```

## Create your first {{ resource_name | default('project') }}

```{{ code_language | default('bash') }}
{{ create_resource_code }}
```

## Run {{ resource_name | default('project') }}

```{{ run_language | default('bash') }}
{{ run_command }}
```

You should see:

```
{{ run_output }}
```

## What just happened

{{ explanation_paragraph }}

## Next steps

- {{ next_step_1 }}
- {{ next_step_2 }}
- [Read the full tutorial]({{ tutorial_link | default('#') }})
""",
            variables={
                "title": "Quickstart title",
                "description": "Get started in 5 minutes",
                "intro_paragraph": "Get up and running fast",
                "install_command": "pip install package",
                "create_resource_code": "# Create resource",
            },
            tags=["quickstart", "getting-started", "tutorial"],
            style_guide="technical",
        )

        # Changelog Template
        self.templates["changelog"] = BuiltInTemplate(
            id="changelog",
            name="Changelog",
            category=TemplateCategory.CHANGELOG,
            description="Keep a changelog for the project",
            content="""---
title: "Changelog"
description: "{{ description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - changelog
  - releases
---

# Changelog

All notable changes to {{ product_name | default('this project') }} are documented on this page.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [{{ version_1 }}] - {{ version_1_date }}

### Added

- {{ v1_added_1 }}
- {{ v1_added_2 }}

### Changed

- {{ v1_changed_1 }}

### Fixed

- {{ v1_fixed_1 }}
- {{ v1_fixed_2 }}

### Deprecated

- {{ v1_deprecated_1 | default('None') }}

### Removed

- {{ v1_removed_1 | default('None') }}

### Security

- {{ v1_security_1 | default('None') }}

## [{{ version_2 | default('0.1.0') }}] - {{ version_2_date | default('2024-01-01') }}

### Added

- {{ v2_added_1 | default('Initial release') }}

[{{ version_1 }}]: {{ repo_url | default('#') }}/compare/{{ version_2 | default('0.1.0') }}...{{ version_1 }}
[{{ version_2 | default('0.1.0') }}]: {{ repo_url | default('#') }}/releases/tag/{{ version_2 | default('0.1.0') }}
""",
            variables={
                "description": "All notable changes to this project",
                "version_1": "1.0.0",
                "version_1_date": "2024-06-15",
                "v1_added_1": "New feature",
                "v1_fixed_1": "Bug fix",
            },
            tags=["changelog", "releases", "history"],
            style_guide="technical",
        )

        # FAQ Template
        self.templates["faq"] = BuiltInTemplate(
            id="faq",
            name="Frequently Asked Questions",
            category=TemplateCategory.FAQ,
            description="Common questions with answers",
            content="""---
title: "{{ title | default('Frequently asked questions') }}"
description: "{{ description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - faq
  - {{ primary_tag | default('support') }}
---

# {{ title | default('Frequently asked questions') }}

{{ intro_paragraph }}

## General

### {{ general_q1 }}

{{ general_a1 }}

### {{ general_q2 }}

{{ general_a2 }}

## Setup and installation

### {{ setup_q1 }}

{{ setup_a1 }}

```{{ setup_code_language | default('bash') }}
{{ setup_code_example }}
```

### {{ setup_q2 | default('How do I update to the latest version?') }}

{{ setup_a2 | default('Run the update command for your package manager.') }}

## Configuration

### {{ config_q1 }}

{{ config_a1 }}

```{{ config_code_language | default('yaml') }}
{{ config_code_example }}
```

## Troubleshooting

### {{ trouble_q1 }}

{{ trouble_a1 }}

### {{ trouble_q2 | default('Where can I find the logs?') }}

{{ trouble_a2 | default('Check the default log directory for your installation.') }}

## Billing and licensing

### {{ billing_q1 | default('What license is this project under?') }}

{{ billing_a1 | default('Check the LICENSE file in the repository root.') }}

## Still have questions?

{{ support_paragraph | default('Open an issue on GitHub or contact support.') }}
""",
            variables={
                "description": "Answers to common questions",
                "intro_paragraph": "Find answers to the most common questions",
                "general_q1": "What is this project?",
                "general_a1": "Answer to general question 1",
                "setup_q1": "How do I install it?",
            },
            tags=["faq", "support", "questions"],
            style_guide="technical",
        )

        # Webhook Guide Template
        self.templates["webhook"] = BuiltInTemplate(
            id="webhook",
            name="Webhook Integration Guide",
            category=TemplateCategory.WEBHOOK,
            description="Webhook setup, events, and verification",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: how-to
product: {{ product | default('both') }}
tags:
  - webhook
  - {{ primary_tag | default('integration') }}
---

# {{ title }}

{{ intro_paragraph }}

## How webhooks work

```mermaid
sequenceDiagram
    participant App as Your Application
    participant Service as {{ service_name | default('Service') }}
    participant Endpoint as Webhook Endpoint

    App->>Service: Subscribe to events
    Service-->>App: Confirmation
    Service->>Endpoint: POST event payload
    Endpoint-->>Service: 200 OK
```

## Register a webhook endpoint

```{{ code_language | default('bash') }}
{{ register_webhook_code }}
```

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | {{ param_url_desc | default('Your HTTPS endpoint URL') }} |
| `events` | array | Yes | {{ param_events_desc | default('Events to subscribe to') }} |
| `secret` | string | No | {{ param_secret_desc | default('Signing secret for verification') }} |

## Available events

| Event | Description | Payload |
|-------|-------------|---------|
| `{{ event_1_name }}` | {{ event_1_desc }} | [Schema](#{{ event_1_name | lower }}) |
| `{{ event_2_name }}` | {{ event_2_desc }} | [Schema](#{{ event_2_name | lower }}) |
| `{{ event_3_name | default('resource.deleted') }}` | {{ event_3_desc | default('Resource was deleted') }} | [Schema](#resource-deleted) |

## Handle webhook payloads

```{{ handler_language | default('python') }}
{{ handler_code }}
```

## Verify webhook signatures

Always verify the signature before processing:

```{{ verify_language | default('python') }}
{{ verify_signature_code }}
```

## Retry policy

{{ retry_policy_description | default('Failed deliveries are retried up to 5 times with exponential backoff.') }}

| Attempt | Delay |
|---------|-------|
| 1 | {{ retry_delay_1 | default('1 minute') }} |
| 2 | {{ retry_delay_2 | default('5 minutes') }} |
| 3 | {{ retry_delay_3 | default('30 minutes') }} |
| 4 | {{ retry_delay_4 | default('2 hours') }} |
| 5 | {{ retry_delay_5 | default('24 hours') }} |

## Test webhooks locally

```bash
{{ local_test_command }}
```

## Troubleshooting

### Webhook not received

1. {{ troubleshoot_step_1 | default('Verify the endpoint URL is publicly accessible') }}
1. {{ troubleshoot_step_2 | default('Check your firewall rules allow inbound HTTPS') }}
1. {{ troubleshoot_step_3 | default('Review the webhook delivery logs') }}

### Signature verification fails

{{ signature_troubleshoot | default('Ensure you are using the raw request body for verification, not the parsed JSON.') }}
""",
            variables={
                "title": "Webhooks guide",
                "description": "Set up and manage webhook integrations",
                "intro_paragraph": "Webhooks let you receive real-time notifications",
                "register_webhook_code": "# Register webhook",
                "event_1_name": "resource.created",
            },
            tags=["webhook", "events", "integration"],
            style_guide="technical",
        )

        # SDK Reference Template
        self.templates["sdk"] = BuiltInTemplate(
            id="sdk",
            name="SDK Reference",
            category=TemplateCategory.SDK,
            description="SDK installation, initialization, and method reference",
            content="""---
title: "{{ sdk_name }} SDK Reference"
description: "{{ description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - sdk
  - {{ primary_tag | default('reference') }}
---

# {{ sdk_name }} SDK Reference

{{ intro_paragraph }}

## Installation

=== "Python"

    ```bash
    pip install {{ python_package }}
    ```

=== "Node.js"

    ```bash
    npm install {{ node_package }}
    ```

=== "Go"

    ```bash
    go get {{ go_module }}
    ```

## Initialize the client

=== "Python"

    ```python
    {{ python_init_code }}
    ```

=== "Node.js"

    ```javascript
    {{ node_init_code }}
    ```

=== "Go"

    ```go
    {{ go_init_code }}
    ```

## Authentication

{{ auth_description }}

```{{ auth_language | default('python') }}
{{ auth_code }}
```

## Methods

### {{ method_1_name }}

{{ method_1_description }}

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| {{ method_1_param_1_name }} | `{{ method_1_param_1_type }}` | {{ method_1_param_1_required | default('Yes') }} | {{ method_1_param_1_desc }} |
| {{ method_1_param_2_name | default('options') }} | `{{ method_1_param_2_type | default('dict') }}` | {{ method_1_param_2_required | default('No') }} | {{ method_1_param_2_desc | default('Additional options') }} |

**Example**

```{{ code_language | default('python') }}
{{ method_1_example }}
```

**Returns**

```json
{{ method_1_response }}
```

### {{ method_2_name }}

{{ method_2_description }}

**Example**

```{{ code_language | default('python') }}
{{ method_2_example }}
```

## Error handling

```{{ code_language | default('python') }}
{{ error_handling_code }}
```

| Error Code | Description | Solution |
|------------|-------------|----------|
| `{{ error_1_code }}` | {{ error_1_desc }} | {{ error_1_solution }} |
| `{{ error_2_code }}` | {{ error_2_desc }} | {{ error_2_solution }} |

## Configuration options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `timeout` | int | {{ default_timeout | default('30') }} | {{ timeout_desc | default('Request timeout in seconds') }} |
| `retries` | int | {{ default_retries | default('3') }} | {{ retries_desc | default('Maximum retry attempts') }} |
| `base_url` | string | {{ default_base_url | default('https://api.example.com') }} | {{ base_url_desc | default('API base URL') }} |

## Changelog

{{ sdk_changelog | default('See the GitHub releases page for version history.') }}
""",
            variables={
                "sdk_name": "Product",
                "description": "Complete SDK reference documentation",
                "python_package": "product-sdk",
                "node_package": "product-sdk",
                "method_1_name": "create()",
            },
            tags=["sdk", "reference", "library"],
            style_guide="technical",
        )

        # Data Model Reference Template
        self.templates["data_model"] = BuiltInTemplate(
            id="data_model",
            name="Data Model Reference",
            category=TemplateCategory.DATA_MODEL,
            description="Database schema and entity relationship docs",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - data-model
  - {{ primary_tag | default('reference') }}
---

# {{ title }}

{{ intro_paragraph }}

## Entity relationship diagram

```mermaid
erDiagram
    {{ er_diagram_content }}
```

## Entities

### {{ entity_1_name }}

{{ entity_1_description }}

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | {{ entity_1_id_type | default('UUID') }} | No | auto | Primary key |
| `{{ entity_1_col_1 }}` | `{{ entity_1_col_1_type }}` | {{ entity_1_col_1_nullable | default('No') }} | {{ entity_1_col_1_default | default('-') }} | {{ entity_1_col_1_desc }} |
| `{{ entity_1_col_2 }}` | `{{ entity_1_col_2_type }}` | {{ entity_1_col_2_nullable | default('Yes') }} | {{ entity_1_col_2_default | default('NULL') }} | {{ entity_1_col_2_desc }} |
| `created_at` | timestamp | No | now() | Record creation time |
| `updated_at` | timestamp | No | now() | Last update time |

**Indexes**

| Name | Columns | Type | Description |
|------|---------|------|-------------|
| `{{ entity_1_idx_1_name }}` | {{ entity_1_idx_1_cols }} | {{ entity_1_idx_1_type | default('btree') }} | {{ entity_1_idx_1_desc }} |

### {{ entity_2_name }}

{{ entity_2_description }}

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | {{ entity_2_id_type | default('UUID') }} | No | auto | Primary key |
| `{{ entity_2_col_1 }}` | `{{ entity_2_col_1_type }}` | {{ entity_2_col_1_nullable | default('No') }} | {{ entity_2_col_1_default | default('-') }} | {{ entity_2_col_1_desc }} |

## Relationships

| From | To | Type | Description |
|------|----|------|-------------|
| {{ entity_1_name }} | {{ entity_2_name }} | {{ rel_1_type | default('one-to-many') }} | {{ rel_1_desc }} |

## Migrations

```sql
{{ migration_sql }}
```

## Query examples

### {{ query_1_title }}

```sql
{{ query_1_sql }}
```

### {{ query_2_title | default('List with pagination') }}

```sql
{{ query_2_sql | default('SELECT * FROM table LIMIT 20 OFFSET 0;') }}
```
""",
            variables={
                "title": "Data Model Reference",
                "description": "Database schema and entity reference",
                "er_diagram_content": "USER ||--o{ ORDER : places",
                "entity_1_name": "User",
                "entity_2_name": "Order",
            },
            tags=["data-model", "database", "schema"],
            style_guide="technical",
        )

        # Deployment Guide Template
        self.templates["deployment"] = BuiltInTemplate(
            id="deployment",
            name="Deployment Guide",
            category=TemplateCategory.DEPLOYMENT,
            description="Production deployment instructions",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: how-to
product: {{ product | default('both') }}
tags:
  - deployment
  - {{ primary_tag | default('operations') }}
---

# {{ title }}

{{ intro_paragraph }}

## Architecture overview

```mermaid
graph TB
    {{ architecture_diagram }}
```

## System requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | {{ min_cpu | default('2 cores') }} | {{ rec_cpu | default('4 cores') }} |
| RAM | {{ min_ram | default('4 GB') }} | {{ rec_ram | default('8 GB') }} |
| Disk | {{ min_disk | default('20 GB') }} | {{ rec_disk | default('50 GB SSD') }} |
| OS | {{ supported_os | default('Ubuntu 22.04+, RHEL 8+') }} | {{ recommended_os | default('Ubuntu 22.04 LTS') }} |

## Prerequisites

- {{ prerequisite_1 }}
- {{ prerequisite_2 }}
- {{ prerequisite_3 | default('Network access to required services') }}

## Deploy with Docker

```bash
{{ docker_deploy_command }}
```

### Docker Compose

```yaml
{{ docker_compose_yaml }}
```

## Deploy to Kubernetes

```yaml
{{ k8s_manifest }}
```

Apply the manifest:

```bash
{{ k8s_apply_command | default('kubectl apply -f deployment.yaml') }}
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `{{ env_var_1 }}` | Yes | - | {{ env_var_1_desc }} |
| `{{ env_var_2 }}` | No | {{ env_var_2_default }} | {{ env_var_2_desc }} |
| `{{ env_var_3 | default('LOG_LEVEL') }}` | No | {{ env_var_3_default | default('info') }} | {{ env_var_3_desc | default('Application log level') }} |

## Health checks

```bash
{{ health_check_command }}
```

Expected response:

```json
{{ health_check_response | default('{"status": "healthy"}') }}
```

## Monitoring

### Key metrics

| Metric | Description | Alert threshold |
|--------|-------------|-----------------|
| {{ metric_1_name }} | {{ metric_1_desc }} | {{ metric_1_threshold }} |
| {{ metric_2_name }} | {{ metric_2_desc }} | {{ metric_2_threshold }} |

## Scaling

{{ scaling_description }}

```bash
{{ scaling_command | default('kubectl scale deployment app --replicas=3') }}
```

## Rollback

```bash
{{ rollback_command }}
```

## Troubleshooting

### {{ deploy_issue_1 }}

**Solution:** {{ deploy_solution_1 }}

### {{ deploy_issue_2 | default('Container fails to start') }}

**Solution:** {{ deploy_solution_2 | default('Check the container logs and verify environment variables.') }}
""",
            variables={
                "title": "Deployment Guide",
                "description": "Deploy to production step by step",
                "intro_paragraph": "Deploy the application to production",
                "docker_deploy_command": "docker run -d app:latest",
                "prerequisite_1": "Docker 20.10+",
            },
            tags=["deployment", "operations", "devops"],
            style_guide="technical",
        )

        # Performance Guide Template
        self.templates["performance"] = BuiltInTemplate(
            id="performance",
            name="Performance Optimization Guide",
            category=TemplateCategory.PERFORMANCE,
            description="Performance tuning and optimization",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: how-to
product: {{ product | default('both') }}
tags:
  - performance
  - {{ primary_tag | default('optimization') }}
---

# {{ title }}

{{ intro_paragraph }}

## Performance benchmarks

| Operation | Baseline | Optimized | Improvement |
|-----------|----------|-----------|-------------|
| {{ bench_op_1 }} | {{ bench_base_1 }} | {{ bench_opt_1 }} | {{ bench_gain_1 }} |
| {{ bench_op_2 }} | {{ bench_base_2 }} | {{ bench_opt_2 }} | {{ bench_gain_2 }} |

## Profiling

### Identify bottlenecks

```{{ profile_language | default('bash') }}
{{ profile_command }}
```

### Read profiling output

```
{{ profile_output }}
```

## Optimization strategies

### {{ strategy_1_title }}

{{ strategy_1_description }}

**Before:**

```{{ code_language | default('python') }}
{{ strategy_1_before }}
```

**After:**

```{{ code_language | default('python') }}
{{ strategy_1_after }}
```

**Impact:** {{ strategy_1_impact }}

### {{ strategy_2_title }}

{{ strategy_2_description }}

```{{ code_language | default('python') }}
{{ strategy_2_code }}
```

**Impact:** {{ strategy_2_impact }}

## Caching

### {{ cache_strategy_title | default('Cache frequently accessed data') }}

```{{ cache_language | default('python') }}
{{ cache_code }}
```

**Cache invalidation:** {{ cache_invalidation | default('TTL-based with 5-minute expiry') }}

## Database optimization

### Query optimization

```sql
{{ optimized_query }}
```

### Index recommendations

```sql
{{ index_recommendation | default('CREATE INDEX idx_name ON table (column);') }}
```

## Configuration tuning

| Setting | Default | Recommended | Description |
|---------|---------|-------------|-------------|
| {{ tuning_1_name }} | {{ tuning_1_default }} | {{ tuning_1_recommended }} | {{ tuning_1_desc }} |
| {{ tuning_2_name }} | {{ tuning_2_default }} | {{ tuning_2_recommended }} | {{ tuning_2_desc }} |

## Load testing

```bash
{{ load_test_command }}
```

### Results

{{ load_test_results }}

## Monitoring performance

{{ monitoring_description | default('Set up dashboards to track key performance indicators continuously.') }}
""",
            variables={
                "title": "Performance Optimization Guide",
                "description": "Improve application performance",
                "intro_paragraph": "Optimize for speed and efficiency",
                "bench_op_1": "API response time",
                "strategy_1_title": "Optimize hot path",
            },
            tags=["performance", "optimization", "tuning"],
            style_guide="technical",
        )

        # Testing Guide Template
        self.templates["testing"] = BuiltInTemplate(
            id="testing",
            name="Testing Guide",
            category=TemplateCategory.TESTING,
            description="Testing strategy, setup, and examples",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: how-to
product: {{ product | default('both') }}
tags:
  - testing
  - {{ primary_tag | default('quality') }}
---

# {{ title }}

{{ intro_paragraph }}

## Testing strategy

```mermaid
graph BT
    E2E[End-to-End Tests] --> Integration[Integration Tests]
    Integration --> Unit[Unit Tests]
```

| Level | Count | Execution time | Coverage target |
|-------|-------|----------------|-----------------|
| Unit | {{ unit_count | default('500+') }} | {{ unit_time | default('< 30s') }} | {{ unit_coverage | default('80%') }} |
| Integration | {{ integration_count | default('100+') }} | {{ integration_time | default('< 5m') }} | {{ integration_coverage | default('60%') }} |
| E2E | {{ e2e_count | default('20+') }} | {{ e2e_time | default('< 15m') }} | {{ e2e_coverage | default('Critical paths') }} |

## Setup

### Install test dependencies

```{{ install_language | default('bash') }}
{{ install_test_deps }}
```

### Configure test environment

```{{ config_language | default('yaml') }}
{{ test_config }}
```

## Run tests

### All tests

```bash
{{ run_all_command }}
```

### Unit tests only

```bash
{{ run_unit_command }}
```

### Integration tests only

```bash
{{ run_integration_command }}
```

### With coverage

```bash
{{ run_coverage_command }}
```

## Write unit tests

### Example: {{ unit_test_subject }}

```{{ test_language | default('python') }}
{{ unit_test_example }}
```

## Write integration tests

### Example: {{ integration_test_subject }}

```{{ test_language | default('python') }}
{{ integration_test_example }}
```

## Fixtures and helpers

```{{ test_language | default('python') }}
{{ fixture_example }}
```

## Mocking external services

```{{ test_language | default('python') }}
{{ mock_example }}
```

## Continuous integration

{{ ci_description }}

```yaml
{{ ci_config }}
```

## Coverage report

```bash
{{ coverage_report_command | default('coverage report --show-missing') }}
```

## Best practices

1. {{ best_practice_1 }}
1. {{ best_practice_2 }}
1. {{ best_practice_3 | default('Keep tests independent and repeatable') }}
1. {{ best_practice_4 | default('Use descriptive test names that explain the expected behavior') }}
""",
            variables={
                "title": "Testing Guide",
                "description": "How to test the application",
                "intro_paragraph": "Comprehensive testing ensures quality",
                "install_test_deps": "pip install -e '.[test]'",
                "run_all_command": "pytest",
            },
            tags=["testing", "quality", "ci"],
            style_guide="technical",
        )

        # Contributing Guide Template
        self.templates["contributing"] = BuiltInTemplate(
            id="contributing",
            name="Contributing Guide",
            category=TemplateCategory.CONTRIBUTING,
            description="How to contribute to the project",
            content="""---
title: "Contributing to {{ project_name }}"
description: "{{ description }}"
content_type: how-to
product: {{ product | default('both') }}
tags:
  - contributing
  - {{ primary_tag | default('community') }}
---

# Contributing to {{ project_name }}

{{ intro_paragraph }}

## Code of conduct

{{ code_of_conduct | default('This project follows the Contributor Covenant. Be respectful and constructive.') }}

## Getting started

### Fork and clone

```bash
git clone https://github.com/{{ github_org }}/{{ github_repo }}.git
cd {{ github_repo }}
```

### Set up development environment

```{{ setup_language | default('bash') }}
{{ setup_dev_command }}
```

### Run tests

```bash
{{ run_tests_command }}
```

## Development workflow

1. Create a branch from `{{ default_branch | default('main') }}`
1. Make your changes
1. Write or update tests
1. Run the linter: `{{ lint_command }}`
1. Commit with a descriptive message
1. Open a pull request

### Branch naming

- `feature/short-description` for new features
- `fix/short-description` for bug fixes
- `docs/short-description` for documentation

### Commit messages

{{ commit_convention | default('Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.') }}

## Pull request process

1. {{ pr_step_1 | default('Fill out the pull request template') }}
1. {{ pr_step_2 | default('Ensure all CI checks pass') }}
1. {{ pr_step_3 | default('Request review from a maintainer') }}
1. {{ pr_step_4 | default('Address review feedback') }}

## Code style

{{ code_style_description }}

```{{ style_language | default('bash') }}
{{ format_command }}
```

## Reporting issues

{{ issue_reporting | default('Use the GitHub issue tracker. Include steps to reproduce, expected behavior, and actual behavior.') }}

## License

{{ license_info | default('Contributions are licensed under the same terms as the project.') }}

## Questions?

{{ questions_contact | default('Open a discussion on GitHub or ask in the community channel.') }}
""",
            variables={
                "project_name": "Project Name",
                "description": "Guidelines for contributing to the project",
                "intro_paragraph": "Contributions are welcome",
                "github_org": "org",
                "github_repo": "repo",
            },
            tags=["contributing", "community", "development"],
            style_guide="technical",
        )

        # Glossary Template
        self.templates["glossary"] = BuiltInTemplate(
            id="glossary",
            name="Glossary",
            category=TemplateCategory.GLOSSARY,
            description="Terminology and definitions",
            content="""---
title: "{{ title | default('Glossary') }}"
description: "{{ description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - glossary
  - {{ primary_tag | default('reference') }}
---

# {{ title | default('Glossary') }}

{{ intro_paragraph }}

## A

### {{ term_a1 }}

{{ definition_a1 }}

### {{ term_a2 | default('API') }}

{{ definition_a2 | default('Application Programming Interface. A set of protocols for building software.') }}

## B

### {{ term_b1 | default('Backoff') }}

{{ definition_b1 | default('A strategy to progressively increase delay between retries.') }}

## C

### {{ term_c1 }}

{{ definition_c1 }}

## D-F

### {{ term_d1 | default('Deployment') }}

{{ definition_d1 | default('The process of releasing software to a production environment.') }}

## G-I

### {{ term_g1 | default('Gateway') }}

{{ definition_g1 | default('A server that acts as an intermediary for requests from clients.') }}

## J-L

### {{ term_j1 | default('JWT') }}

{{ definition_j1 | default('JSON Web Token. A compact token format for securely transmitting claims between parties.') }}

## M-O

### {{ term_m1 | default('Middleware') }}

{{ definition_m1 | default('Software that acts as a bridge between an operating system and applications.') }}

## P-R

### {{ term_p1 | default('Payload') }}

{{ definition_p1 | default('The data carried by a network packet or message body.') }}

## S-U

### {{ term_s1 | default('Schema') }}

{{ definition_s1 | default('A structured framework that defines the organization of data.') }}

## V-Z

### {{ term_v1 | default('Webhook') }}

{{ definition_v1 | default('A callback triggered by an event that sends data to a URL in real time.') }}
""",
            variables={
                "description": "Definitions of key terms used in the documentation",
                "intro_paragraph": "This glossary defines terms used throughout the docs",
                "term_a1": "Authentication",
                "definition_a1": "The process of verifying identity",
                "term_c1": "CORS",
            },
            tags=["glossary", "terminology", "reference"],
            style_guide="technical",
        )

        # Admin Guide Template
        self.templates["admin_guide"] = BuiltInTemplate(
            id="admin_guide",
            name="Administration Guide",
            category=TemplateCategory.ADMIN_GUIDE,
            description="System administration and management",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: how-to
product: {{ product | default('self-hosted') }}
tags:
  - admin
  - {{ primary_tag | default('operations') }}
---

# {{ title }}

{{ intro_paragraph }}

## User management

### Create a user

```{{ admin_language | default('bash') }}
{{ create_user_command }}
```

### Assign roles

```{{ admin_language | default('bash') }}
{{ assign_role_command }}
```

### Deactivate a user

```{{ admin_language | default('bash') }}
{{ deactivate_user_command }}
```

## Backup and restore

### Create a backup

```bash
{{ backup_command }}
```

!!! warning "Schedule regular backups"
    {{ backup_warning | default('Set up automated daily backups to avoid data loss.') }}

### Restore from backup

```bash
{{ restore_command }}
```

## Log management

### View logs

```bash
{{ view_logs_command }}
```

### Log rotation

```{{ log_config_language | default('yaml') }}
{{ log_rotation_config }}
```

## Database maintenance

### Run maintenance tasks

```bash
{{ db_maintenance_command }}
```

### Check database health

```bash
{{ db_health_command }}
```

## Security administration

### Rotate secrets

```bash
{{ rotate_secrets_command }}
```

### Audit log

```bash
{{ audit_log_command | default('cat /var/log/app/audit.log | tail -100') }}
```

## System updates

### Apply updates

```bash
{{ update_command }}
```

### Verify update

```bash
{{ verify_update_command }}
```

## Monitoring checklist

- [ ] {{ monitoring_check_1 | default('CPU and memory usage within limits') }}
- [ ] {{ monitoring_check_2 | default('Disk space above 20% free') }}
- [ ] {{ monitoring_check_3 | default('All services running') }}
- [ ] {{ monitoring_check_4 | default('No critical errors in logs') }}
- [ ] {{ monitoring_check_5 | default('Backups completing successfully') }}
""",
            variables={
                "title": "Administration Guide",
                "description": "System administration reference",
                "intro_paragraph": "Manage and maintain the system",
                "create_user_command": "# Create user command",
                "backup_command": "# Backup command",
            },
            tags=["admin", "operations", "management"],
            style_guide="technical",
        )

        # Configuration Reference Template
        self.templates["configuration"] = BuiltInTemplate(
            id="configuration",
            name="Configuration Reference",
            category=TemplateCategory.CONFIGURATION,
            description="Complete configuration options reference",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - configuration
  - {{ primary_tag | default('reference') }}
---

# {{ title }}

{{ intro_paragraph }}

## Configuration file

The primary configuration file is `{{ config_file_path | default('config.yml') }}`.

```{{ config_language | default('yaml') }}
{{ config_example }}
```

## Environment variables

All settings can also be set through environment variables with the `{{ env_prefix | default('APP_') }}` prefix.

| Variable | Config key | Type | Default | Description |
|----------|-----------|------|---------|-------------|
| `{{ env_prefix | default('APP_') }}{{ env_1_suffix }}` | `{{ config_1_key }}` | {{ config_1_type }} | `{{ config_1_default }}` | {{ config_1_desc }} |
| `{{ env_prefix | default('APP_') }}{{ env_2_suffix }}` | `{{ config_2_key }}` | {{ config_2_type }} | `{{ config_2_default }}` | {{ config_2_desc }} |
| `{{ env_prefix | default('APP_') }}{{ env_3_suffix | default('LOG_LEVEL') }}` | `{{ config_3_key | default('log_level') }}` | {{ config_3_type | default('string') }} | `{{ config_3_default | default('info') }}` | {{ config_3_desc | default('Application log level') }} |

## Sections

### {{ section_1_name }}

{{ section_1_description }}

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `{{ s1_opt_1 }}` | {{ s1_opt_1_type }} | `{{ s1_opt_1_default }}` | {{ s1_opt_1_desc }} |
| `{{ s1_opt_2 }}` | {{ s1_opt_2_type }} | `{{ s1_opt_2_default }}` | {{ s1_opt_2_desc }} |

### {{ section_2_name }}

{{ section_2_description }}

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `{{ s2_opt_1 }}` | {{ s2_opt_1_type }} | `{{ s2_opt_1_default }}` | {{ s2_opt_1_desc }} |

## Validation

{{ product_name | default('The application') }} validates configuration at startup. Invalid values cause the process to exit with a descriptive error message.

## Reload configuration

{{ reload_description | default('Some settings can be changed without a restart.') }}

```bash
{{ reload_command | default('kill -HUP $(pidof app)') }}
```

## Example configurations

### Development

```{{ config_language | default('yaml') }}
{{ dev_config_example }}
```

### Production

```{{ config_language | default('yaml') }}
{{ prod_config_example }}
```
""",
            variables={
                "title": "Configuration Reference",
                "description": "All configuration options explained",
                "intro_paragraph": "Configure every aspect of the application",
                "config_file_path": "config.yml",
                "config_example": "# Configuration example",
            },
            tags=["configuration", "reference", "settings"],
            style_guide="technical",
        )

        # CLI Reference Template
        self.templates["cli_reference"] = BuiltInTemplate(
            id="cli_reference",
            name="CLI Reference",
            category=TemplateCategory.CLI_REFERENCE,
            description="Command-line interface reference",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: reference
product: {{ product | default('both') }}
tags:
  - cli
  - {{ primary_tag | default('reference') }}
---

# {{ title }}

{{ intro_paragraph }}

## Installation

```bash
{{ install_command }}
```

## Global options

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--help` | `-h` | Show help message | - |
| `--version` | `-V` | Show version | - |
| `--verbose` | `-v` | Increase output verbosity | `false` |
| `{{ global_flag_1 }}` | `{{ global_flag_1_short | default('') }}` | {{ global_flag_1_desc }} | `{{ global_flag_1_default }}` |

## Commands

### `{{ cmd_1_name }}`

{{ cmd_1_description }}

```bash
{{ cli_name | default('app') }} {{ cmd_1_name }} {{ cmd_1_usage | default('[options]') }}
```

**Options**

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `{{ cmd_1_opt_1 }}` | `{{ cmd_1_opt_1_short | default('') }}` | {{ cmd_1_opt_1_desc }} | `{{ cmd_1_opt_1_default | default('-') }}` |
| `{{ cmd_1_opt_2 | default('--output') }}` | `{{ cmd_1_opt_2_short | default('-o') }}` | {{ cmd_1_opt_2_desc | default('Output format') }} | `{{ cmd_1_opt_2_default | default('text') }}` |

**Examples**

```bash
# {{ cmd_1_example_1_desc }}
{{ cmd_1_example_1 }}

# {{ cmd_1_example_2_desc | default('With options') }}
{{ cmd_1_example_2 | default('app command --flag value') }}
```

### `{{ cmd_2_name }}`

{{ cmd_2_description }}

```bash
{{ cli_name | default('app') }} {{ cmd_2_name }} {{ cmd_2_usage | default('[options]') }}
```

**Options**

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `{{ cmd_2_opt_1 }}` | `{{ cmd_2_opt_1_short | default('') }}` | {{ cmd_2_opt_1_desc }} | `{{ cmd_2_opt_1_default | default('-') }}` |

**Examples**

```bash
{{ cmd_2_example }}
```

### `{{ cmd_3_name | default('help') }}`

{{ cmd_3_description | default('Show help for a command.') }}

```bash
{{ cli_name | default('app') }} help [command]
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | {{ exit_0 | default('Success') }} |
| 1 | {{ exit_1 | default('General error') }} |
| 2 | {{ exit_2 | default('Invalid arguments') }} |
| {{ exit_code_custom | default('127') }} | {{ exit_custom_desc | default('Command not found') }} |

## Configuration file

The CLI reads configuration from `{{ config_file | default('~/.app/config.yml') }}`.

## Shell completion

### Bash

```bash
{{ bash_completion | default('source <(app completion bash)') }}
```

### Zsh

```bash
{{ zsh_completion | default('source <(app completion zsh)') }}
```

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `{{ cli_env_1 }}` | {{ cli_env_1_desc }} | {{ cli_env_1_default | default('-') }} |
| `{{ cli_env_2 | default('NO_COLOR') }}` | {{ cli_env_2_desc | default('Disable colored output') }} | {{ cli_env_2_default | default('-') }} |
""",
            variables={
                "title": "CLI Reference",
                "description": "Complete command-line reference",
                "intro_paragraph": "The CLI provides full control from the terminal",
                "cli_name": "app",
                "cmd_1_name": "init",
            },
            tags=["cli", "reference", "commands"],
            style_guide="technical",
        )

        # Onboarding Guide Template (using existing category)
        self.templates["onboarding"] = BuiltInTemplate(
            id="onboarding",
            name="Developer Onboarding Guide",
            category=TemplateCategory.ONBOARDING,
            description="New team member onboarding checklist",
            content="""---
title: "{{ title }}"
description: "{{ description }}"
content_type: tutorial
product: {{ product | default('both') }}
tags:
  - onboarding
  - {{ primary_tag | default('getting-started') }}
---

# {{ title }}

{{ intro_paragraph }}

## Day 1: Environment setup

### Access requests

- [ ] {{ access_1 | default('GitHub organization access') }}
- [ ] {{ access_2 | default('Internal tools access') }}
- [ ] {{ access_3 | default('Cloud provider console access') }}

### Install required tools

```bash
{{ install_tools_command }}
```

### Clone the repository

```bash
git clone {{ repo_url }}
cd {{ repo_name }}
```

### Set up local development

```{{ setup_language | default('bash') }}
{{ local_setup_command }}
```

### Verify the setup

```bash
{{ verify_setup_command }}
```

## Day 2: Learn the codebase

### Architecture overview

{{ architecture_overview }}

```mermaid
graph TB
    {{ architecture_diagram }}
```

### Key directories

| Directory | Purpose |
|-----------|---------|
| `{{ dir_1 }}` | {{ dir_1_purpose }} |
| `{{ dir_2 }}` | {{ dir_2_purpose }} |
| `{{ dir_3 | default('tests/') }}` | {{ dir_3_purpose | default('Test suite') }} |

### Run the application

```bash
{{ run_app_command }}
```

## Day 3-5: First contribution

### Find a starter task

{{ starter_task_description | default('Check the issue tracker for issues labeled "good first issue".') }}

### Development workflow

1. {{ workflow_step_1 | default('Create a feature branch') }}
1. {{ workflow_step_2 | default('Make changes and write tests') }}
1. {{ workflow_step_3 | default('Run the linter and test suite') }}
1. {{ workflow_step_4 | default('Open a pull request') }}

### Code review process

{{ code_review_description }}

## Resources

- [Contributing Guide]({{ contributing_link | default('#') }})
- [Architecture Docs]({{ architecture_link | default('#') }})
- [API Reference]({{ api_link | default('#') }})
- {{ resource_extra | default('Team wiki and documentation') }}

## Questions?

{{ questions_contact | default('Ask your mentor or post in the team channel.') }}
""",
            variables={
                "title": "Developer Onboarding Guide",
                "description": "Get new team members up to speed",
                "intro_paragraph": "Welcome to the team",
                "repo_url": "https://github.com/org/repo.git",
                "repo_name": "repo",
            },
            tags=["onboarding", "getting-started", "team"],
            style_guide="technical",
        )

    # -- Content-type mapping ------------------------------------------------

    CONTENT_TYPE_MAP: dict[str, str] = {
        "tutorial": "tutorial",
        "how-to": "how_to",
        "concept": "concept",
        "reference": "api_reference",
        "troubleshooting": "troubleshooting",
        "release-note": "release_notes",
        "quickstart": "quickstart",
        "changelog": "changelog",
        "faq": "faq",
        "webhook": "webhook",
        "sdk": "sdk",
        "data-model": "data_model",
        "deployment": "deployment",
        "performance": "performance",
        "testing": "testing",
        "contributing": "contributing",
        "glossary": "glossary",
        "admin-guide": "admin_guide",
        "configuration": "configuration",
        "cli-reference": "cli_reference",
        "onboarding": "onboarding",
        "security": "security",
        "integration": "integration_guide",
        "migration": "migration_guide",
        "adr": "adr",
        "runbook": "runbook",
        "auth-flow": "auth_flow",
    }

    def get_for_content_type(self, content_type: str) -> Optional[BuiltInTemplate]:
        """Get a template matching a content_type string.

        Args:
            content_type: Document content type (e.g. "tutorial", "how-to").

        Returns:
            Matching template or None.
        """
        template_id = self.CONTENT_TYPE_MAP.get(content_type)
        if template_id:
            return self.templates.get(template_id)
        return None

    def render(
        self,
        template_id: str,
        variables: Dict[str, Any],
        shared_vars: Optional[Any] = None,
    ) -> Optional[str]:
        """Render a template with variables and optional shared variables.

        Merges shared variables (lower priority) with explicit variables
        (higher priority), then renders the Jinja2 template.

        Args:
            template_id: Template identifier.
            variables: Variables to substitute into the template.
            shared_vars: Optional SharedVariablesManager instance. Its
                variables are merged with lower priority than *variables*.

        Returns:
            Rendered content string, or None if template not found.
        """
        template = self.get_template(template_id)
        if not template:
            return None

        merged: Dict[str, Any] = {}

        # Merge shared variables first (lower priority)
        if shared_vars is not None:
            try:
                for vd in shared_vars.list_all():
                    merged[vd.name] = vd.value
            except (AttributeError, TypeError):
                pass

        # Template defaults
        merged.update(template.variables)
        # Explicit variables override everything
        merged.update(variables)

        from jinja2 import Environment, BaseLoader, Undefined

        class _SilentUndefined(Undefined):
            """Return empty string for missing variables instead of raising."""
            def __str__(self) -> str:
                return ""

            def __iter__(self):
                return iter([])

            def __bool__(self) -> bool:
                return False

        env = Environment(loader=BaseLoader(), undefined=_SilentUndefined)
        jinja_tpl = env.from_string(template.content)
        return jinja_tpl.render(**merged)

    def get_template(self, template_id: str) -> Optional[BuiltInTemplate]:
        """Get a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template if found, None otherwise
        """
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: TemplateCategory) -> List[BuiltInTemplate]:
        """Get all templates in a category.

        Args:
            category: Template category

        Returns:
            List of templates in the category
        """
        return [t for t in self.templates.values() if t.category == category]

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates.

        Returns:
            List of template summaries
        """
        return [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category.value,
                "description": t.description,
                "tags": t.tags
            }
            for t in self.templates.values()
        ]

    def render_template(self, template_id: str, variables: Dict[str, Any]) -> Optional[str]:
        """Render a template with variables.

        Args:
            template_id: Template identifier
            variables: Variables to substitute

        Returns:
            Rendered content or None if template not found
        """
        template = self.get_template(template_id)
        if not template:
            return None

        from jinja2 import Template
        jinja_template = Template(template.content)

        # Merge default variables with provided ones
        merged_vars = {**template.variables, **variables}

        return jinja_template.render(**merged_vars)

    def export_template(self, template_id: str, output_path: Path) -> bool:
        """Export a template to a file.

        Args:
            template_id: Template identifier
            output_path: Path to save the template

        Returns:
            Success status
        """
        template = self.get_template(template_id)
        if not template:
            return False

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template.content)
            return True
        except Exception:
            return False

    def validate_variables(self, template_id: str, variables: Dict[str, Any]) -> List[str]:
        """Validate that required variables are provided.

        Args:
            template_id: Template identifier
            variables: Provided variables

        Returns:
            List of missing required variables
        """
        template = self.get_template(template_id)
        if not template:
            return ["Template not found"]

        missing = []
        for var_name in template.variables.keys():
            if var_name not in variables and '|' not in template.content:
                # Check if variable has a default in the template
                import re
                pattern = f"{{{{{var_name}\\s*\\|\\s*default"
                if not re.search(pattern, template.content):
                    missing.append(var_name)

        return missing