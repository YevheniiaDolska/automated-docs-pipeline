# Private Repository Setup Guide

## Quick Answer: Yes, It Works in Private Repos

The pipeline works exactly the same in private repositories, but:

- **GitHub Actions**: Costs money (free tier: 2,000 minutes/month)
- **External APIs**: Still free (Discourse, Stack Overflow)
- **All features**: Work identically

## Cost Breakdown for Private Repos

### GitHub Actions Minutes

| Plan | Minutes/Month | Cost | Good For |
| --- | --- | --- | --- |
| Free | 2,000 | $0 | Small team (1-3 writers) |
| Team | 3,000 | $4/user/month | Medium team (4-10 writers) |
| Enterprise | 50,000 | Custom | Large organizations |

**Your usage estimate:**

- Each commit triggers ~3 minutes of checks
- 20 commits/day = 60 minutes/day
- Monthly: ~1,200 minutes (fits in free tier)

### Adding to an Existing Private Repository

## Method 1: Direct Copy (Simplest)

```bash
# 1. Clone your private repo
git clone https://github.com/your-company/your-docs-repo.git
cd your-docs-repo

# 2. Download this pipeline (if you haven't already)
git clone https://github.com/[pipeline-source]/auto-doc-pipeline.git ../pipeline-temp

# 3. Copy pipeline files to your repo
cp -r ../pipeline-temp/scripts ./
cp -r ../pipeline-temp/.github ./
cp ../pipeline-temp/.vale.ini ./
cp ../pipeline-temp/.markdownlint.yml ./
cp ../pipeline-temp/.pre-commit-config.yaml ./
cp ../pipeline-temp/mkdocs.yml ./
cp ../pipeline-temp/requirements.txt ./
cp ../pipeline-temp/package.json ./
cp ../pipeline-temp/cliff.toml ./

# 4. Install dependencies
pip install -r requirements.txt
npm install
pre-commit install

# 5. Commit everything
git add .
git commit -m "Add documentation automation pipeline"
git push
```

## Method 2: As a Git Submodule (Advanced)

Keeps pipeline separate for easy updates:

```bash
# Add as submodule
git submodule add https://github.com/[pipeline-source]/auto-doc-pipeline.git .pipeline

# Link configuration files
ln -s .pipeline/.vale.ini .vale.ini
ln -s .pipeline/.markdownlint.yml .markdownlint.yml
ln -s .pipeline/.pre-commit-config.yaml .pre-commit-config.yaml

# Copy scripts (so they're accessible)
cp -r .pipeline/scripts ./

git add .
git commit -m "Add documentation pipeline as submodule"
git push
```

## Method 3: Fork and Customize

Best for heavy customization:

```bash
# 1. Fork the pipeline to your organization
# (Do this in GitHub UI - fork to your company's account)

# 2. Clone YOUR fork
git clone https://github.com/your-company/forked-pipeline.git

# 3. Add as remote to docs repo
cd your-docs-repo
git remote add pipeline https://github.com/your-company/forked-pipeline.git
git fetch pipeline

# 4. Merge pipeline files
git merge pipeline/main --allow-unrelated-histories

# 5. Resolve conflicts and commit
git add .
git commit -m "Integrate custom pipeline"
git push
```

## Setting Up Secrets for Private Repos

### Required GitHub Secrets

Go to: Settings → Secrets and variables → Actions

Add these secrets:

```yaml
# For Algolia search (optional)
ALGOLIA_APP_ID: your_app_id
ALGOLIA_API_KEY: your_admin_key
ALGOLIA_INDEX_NAME: your_index

# For community gap detection (optional)
DISCOURSE_API_KEY: your_discourse_key
DISCOURSE_URL: https://forum.yourcompany.com
STACK_OVERFLOW_KEY: your_so_key
```

### Local Configuration

Create `.env` file (do not commit this):

```bash
# .env
GITHUB_TOKEN=ghp_yourPersonalAccessToken
DISCOURSE_API_KEY=your_key
STACK_OVERFLOW_KEY=your_key
```

Add to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

## Team Setup Instructions

### For Each Team Member

Send this to your team:

```markdown
## Setup Documentation Pipeline

1. **Install tools** (one time):
   - Python 3.8+: https://python.org
   - Git: https://git-scm.com
   - VS Code: https://code.visualstudio.com

2. **Clone and setup** (one time):
   ```bash
   git clone https://github.com/company/docs-repo.git
   cd docs-repo
   pip install -r requirements.txt
   pre-commit install
   ```text

1. **Daily workflow**:

   ```bash
   # Create new doc
   python scripts/new_doc.py how-to "Your Title"

   # Write your content
   code docs/your-file.md

   # Commit (auto-checks run)
   git add .
   git commit -m "Add how-to guide for X"
   git push
   ```text

1. **If checks fail**: Read the error and fix, or run:

   ```bash
   python scripts/seo_geo_optimizer.py docs/ --fix
   ```text

```

## Permissions Required

### For Repository Admins

Your repo needs these permissions:

1. **Settings → Actions → General**:
   - Actions permissions: Allow all actions
   - Workflow permissions: Read and write

1. **Settings → Branches** (optional but recommended):
   - Add rule for `main` branch
   - Require status checks to pass
   - Include: vale, markdownlint, seo-check

### For Team Members

Each person needs:

- **Write** access to the repository
- **Read** access to organization secrets
- Ability to create pull requests

## Migrating from Public to Private

If moving from public to private repo:

```bash
# 1. Create private repo in GitHub UI

# 2. Change remote URL
git remote set-url origin https://github.com/company/private-docs.git

# 3. Push to private repo
git push -u origin main

# 4. Update GitHub Actions workflows
# Change any public URLs to private ones in .github/workflows/

# 5. Set up billing for Actions
# Go to Settings → Billing → Set up payment method
```

## Common Private Repo Issues

### "Resource not accessible by integration"

**Fix**: Go to Settings → Actions → General → Workflow permissions → Read and write

### "GitHub Actions is disabled"

**Fix**: Settings → Actions → General → Allow all actions

### "Billing limit exceeded"

**Fix**:

1. Settings → Billing → Spending limits → Increase limit
1. Or optimize workflows to use fewer minutes

### "Can't access secrets"

**Fix**: Secrets are not inherited from org by default

1. Organization settings → Secrets → Make available to repository
1. Or add secrets directly to the repository

## Cost Optimization Tips

### Reduce Action Minutes Usage

1. **Run only on main branch**:

   ```yaml
   # .github/workflows/docs-check.yml
   on:
     push:
       branches: [main]  # Not on feature branches
   ```

1. **Cache dependencies**:

   ```yaml
   - uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
   ```

1. **Run heavy checks weekly**:

   ```yaml
   on:
     schedule:
       - cron: '0 0 * * 1'  # Mondays only
   ```

## Security Best Practices

### For Documentation Repos

1. **Never commit**:
   - API keys
   - Passwords
   - Internal URLs
   - Customer data

1. **Use secrets for**:
   - External API keys
   - Deployment credentials
   - Webhook URLs

1. **Review before merge**:
   - Require PR reviews
   - Run security scanning
   - Check for accidental secrets

### Example Security Workflow

```yaml
# .github/workflows/security.yml
name: Security Check
on: [pull_request]

jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
```

## Quick Setup Script

Save this as `setup-private-repo.sh`:

```bash
#!/bin/bash

echo "Setting up Documentation Pipeline for Private Repo"
echo "================================================"

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required but not installed. Aborting." >&2; exit 1; }
command -v git >/dev/null 2>&1 || { echo "Git required but not installed. Aborting." >&2; exit 1; }

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Create .env template
echo "Creating .env template..."
cat > .env.example << EOL
# Copy to .env and fill in your values
GITHUB_TOKEN=
DISCOURSE_API_KEY=
STACK_OVERFLOW_KEY=
EOL

# Setup git hooks
echo "Configuring git..."
git config core.hooksPath .git/hooks

# Create first document
echo "Creating example document..."
python scripts/new_doc.py tutorial "Getting Started"

echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your API keys"
echo "2. Run 'python scripts/pilot_analysis.py' to check current state"
echo "3. Start writing docs."
```

Make it executable:

```bash
chmod +x setup-private-repo.sh
./setup-private-repo.sh
```

## FAQ

**Q: Do all features work in private repos?**
A: Yes, 100% identical functionality.

**Q: What's the main difference?**
A: GitHub Actions costs money for private repos.

**Q: Can I use it without GitHub Actions?**
A: Yes. Pre-commit hooks work locally without Actions.

**Q: How do I add team members?**
A: Settings → Manage access → Invite collaborators

**Q: Can I use this with GitLab/Bitbucket?**
A: Yes, but you'll need to convert GitHub Actions to GitLab CI or Bitbucket Pipelines.

## Support

If you encounter issues with private repo setup:

1. Check GitHub Status: <https://www.githubstatus.com/>
1. Verify billing is active: Settings → Billing
1. Check Actions tab for error details
1. Review repository permissions: Settings → Manage access
