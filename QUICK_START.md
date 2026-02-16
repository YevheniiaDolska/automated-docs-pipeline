# Quick Start - Creating Documentation

## For Users: Super Simple Path

### Option 1: Ask Claude (Recommended)

```bash
# Just tell Claude what you need
"Create a quickstart guide for webhook authentication"

# Claude will
# 1. Use the right template
# 2. Follow ALL formatting rules
# 3. Place it in correct folder
# 4. Update navigation
# 5. Pass ALL checks first time

```

### Option 2: Use Helper Script

```bash
# Create a how-to guide
python scripts/create-doc.py --type how-to --title "Configure webhook auth"

# Create a tutorial
python scripts/create-doc.py --type tutorial --title "Build your first workflow"

```

### Option 3: Manual (if needed)

1. Copy a template from `templates/`
1. Edit content
1. Run checks: `npm run lint`

## Validation Happens Automatically

### Local (Pre-commit)

When you commit, these run automatically:

- ✅ Markdownlint
- ✅ Spell check
- ✅ Frontmatter validation
- ✅ SEO/GEO optimization

### Remote (CI/CD)

Same checks run on GitHub when you push:

- ✅ All linting checks
- ✅ Build validation
- ✅ Orphaned page detection

## Common Commands

```bash
# Check everything before commit
npm run lint

# Check specific file
markdownlint docs/your-file.md
python scripts/seo_geo_optimizer.py docs/your-file.md

# Fix common issues automatically
markdownlint --fix docs/your-file.md

```

## Why This Works

1. **Claude knows the rules** - CLAUDE.md has explicit formatting
1. **Templates are pre-validated** - Already follow all rules
1. **Double validation** - Local + CI/CD
1. **Same rules everywhere** - No surprises

## No More 20 Iterations

✅ Documents are right the first time
✅ Claude follows strict rules
✅ Templates ensure consistency
✅ Validation catches any issues
