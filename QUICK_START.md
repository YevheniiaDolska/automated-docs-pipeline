# Quick start (first 30 minutes)

This guide is for a person who has never installed this pipeline before.

## 1. Clone and enter project

```bash
git clone <repo-url>
cd "Auto-Doc Pipeline"
```

## 2. Install dependencies

```bash
python3 -m pip install -r requirements.txt
npm install
```

## 3. Validate minimal mode

```bash
make validate-minimal
```

If this command passes, your core setup works.

## 4. Run full validation (optional)

```bash
make validate-full
```

## 5. Start docs preview

```bash
make docs-serve
```

Open `http://127.0.0.1:8000`.

## 6. Run with Docker (optional)

```bash
docker compose -f docker-compose.docs-ops.yml up --build
```

## What to read next

1. `README_SETUP.md` for full beginner setup.
1. `SETUP_FOR_PROJECTS.md` to install into another repository.
1. `MINIMAL_MODE.md` for restricted company environments.
1. `SECURITY_OPERATIONS.md` for secrets and access policy.
