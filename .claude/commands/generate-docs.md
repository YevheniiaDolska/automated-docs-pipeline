# Generate Documentation from Gap Analysis

## Documentation Generation Tasks

Generate the following documentation files based on the gap analysis.
Follow these rules:

1. Use the templates in `./templates/` directory
1. Follow frontmatter schema from `docs-schema.yml`
1. Keep descriptions 50-160 characters for SEO
1. First paragraph must be <60 words with a clear definition
1. Use concrete examples and code samples
1. Don't use words like 'simple', 'easy', 'just'

## Tasks

### DOC-001: Authentication: authentication: Auth

- **Type**: how-to
- **Priority**: high
- **Output**: `docs/how-to/authentication-auth.md`
- **Template**: `templates/how-to.md`
- **Category**: authentication

**Context**: Update authentication documentation for changes in FULL_IMPLEMENTATION_START_HERE.md. Include security considerations.

**Keywords**:

**Sample questions from users**:

---

### DOC-002: Database Schema: database_schema: migration

- **Type**: how-to
- **Priority**: high
- **Output**: `docs/how-to/database-schema-database-schema-migration.md`
- **Template**: `templates/how-to.md`
- **Category**: database_schema

**Context**: Document database schema change in PILOT_VS_FULL_IMPLEMENTATION.md. Update data model documentation.

**Keywords**:

**Sample questions from users**:

---

### DOC-003: Removed Function: Function removed: if

- **Type**: how-to
- **Priority**: high
- **Output**: `docs/how-to/removed-function-function-removed-if.md`
- **Template**: `templates/how-to.md`
- **Category**: removed_function

**Context**: BREAKING: Function if was removed. Update documentation and add migration guide.

**Keywords**:

**Sample questions from users**:

---

### DOC-004: Signature Change: Function signature changed: print

- **Type**: how-to
- **Priority**: high
- **Output**: `docs/how-to/signature-change-function-signature-changed-print.md`
- **Template**: `templates/how-to.md`
- **Category**: signature_change

**Context**: UPDATE REQUIRED: Function print signature changed. Old: (f"Found {result['nbHits']} results for 'webhook'") → New: (f"Found {nb_hits} results for 'webhook'"). Update documentation and examples.

**Keywords**:

**Sample questions from users**:

---

### DOC-005: New Function: New function: print

- **Type**: how-to
- **Priority**: medium
- **Output**: `docs/how-to/new-function-new-function-print.md`
- **Template**: `templates/how-to.md`
- **Category**: new_function

**Context**: Document new function: print. Include parameters, return value, and usage example.

**Keywords**:

**Sample questions from users**:

---

### DOC-006: Webhook: webhook: webhook

- **Type**: how-to
- **Priority**: medium
- **Output**: `docs/how-to/webhook-webhook.md`
- **Template**: `templates/how-to.md`
- **Category**: webhook

**Context**: Update webhook documentation for changes in FULL_IMPLEMENTATION_START_HERE.md. Include payload examples and event types.

**Keywords**:

**Sample questions from users**:

---

### DOC-007: Public Function: public_function: seo_validate_file

- **Type**: reference
- **Priority**: medium
- **Output**: `docs/reference/public-function-public-function-seo-validate-file.md`
- **Template**: `templates/reference.md`
- **Category**: public_function

**Context**: Consider documenting public API: seo_validate_file. Include parameters, return value, and example usage.

**Keywords**:

**Sample questions from users**:

---

### DOC-008: Config Option: config_option: local

- **Type**: reference
- **Priority**: medium
- **Output**: `docs/reference/config-option-config-option-local.md`
- **Template**: `templates/reference.md`
- **Category**: config_option

**Context**: Document configuration option: local. Include allowed values and when to use.

**Keywords**:

**Sample questions from users**:

---

### DOC-009: Env Var: env_var: ALGOLIA_INDEX_NAME

- **Type**: reference
- **Priority**: medium
- **Output**: `docs/reference/env-var-env-var-algolia-index-name.md`
- **Template**: `templates/reference.md`
- **Category**: env_var

**Context**: Add environment variable ALGOLIA_INDEX_NAME to configuration reference. Include default value, description, and examples.

**Keywords**:

**Sample questions from users**:

---

### DOC-010: Error Handling: error_handling: FileNotFoundError

- **Type**: how-to
- **Priority**: medium
- **Output**: `docs/how-to/error-handling-error-handling-filenotfounderror.md`
- **Template**: `templates/how-to.md`
- **Category**: error_handling

**Context**: Document new error type: FileNotFoundError. Include cause, solution, and error code.

**Keywords**:

**Sample questions from users**:

---

## Execution

For each task:

1. Read the template file
1. Create the document with proper frontmatter
1. Fill in content based on context and keywords
1. Save to the specified output path

After generating all documents, run: `npm run lint` to validate.

## After Generation

1. Run pre-commit hooks: `git add . && git commit -m "docs: add generated documentation"`
1. If hooks fail, fix issues and retry
1. Create PR for human review
