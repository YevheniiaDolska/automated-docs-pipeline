# Generate Documentation from Gap Analysis

# Documentation Generation Tasks

Generate the following documentation files based on the gap analysis.
Follow these rules:

1. Use the templates in `./templates/` directory
2. Follow frontmatter schema from `docs-schema.yml`
3. Keep descriptions 50-160 characters for SEO
4. First paragraph must be <60 words with a clear definition
5. Use concrete examples and code samples
6. Don't use words like 'simple', 'easy', 'just'

## Tasks

## Execution

For each task:
1. Read the template file
2. Create the document with proper frontmatter
3. Fill in content based on context and keywords
4. Save to the specified output path

After generating all documents, run: `npm run lint` to validate.

Prompt gate reason:
- feature_blocked:community

## After Generation

1. Run pre-commit hooks: `git add . && git commit -m "docs: add generated documentation"`
2. If hooks fail, fix issues and retry
3. Create PR for human review
