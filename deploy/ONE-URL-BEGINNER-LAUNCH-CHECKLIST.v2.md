# One-URL Beginner Launch Checklist v2 (Pre-Filled)

Этот файл уже частично заполнен вашими данными.
Секреты в репозиторий не записываем: храните их только в серверном `.env`.

## Уже подставлено

- Domain: `veri-doc.app`
- Server IP: `204.168.146.27`
- SSH key найден локально: `~/.ssh/id_ed25519_hetzner`
- SSH вход подтвержден: `root@204.168.146.27` (Ubuntu shell открылся)
- Starter checkout URL: `https://liora-tech.lemonsqueezy.com/checkout/buy/d86a8f7b-7ff6-4bf2-8f96-7b5118d67605`
- Pro checkout URL: `https://liora-tech.lemonsqueezy.com/checkout/buy/40e1e233-c9e5-41cf-8204-8184e7a35862`
- Business/Enterprise invoice URL: `https://calendly.com/veridoc/discovery`

## 0) Что осталось получить от вас

1. SSH вход:
- `SSH_HOST`: `204.168.146.27`
- `SSH_PORT`: `22` (подтвердить в firewall, если не меняли)
- `SSH_USER`: `root`

1. DNS access:
- подтверждение, что вы можете менять DNS записи домена `veri-doc.app`

1. LemonSqueezy:
- `LEMONSQUEEZY_STORE_ID`
- `LEMONSQUEEZY_WEBHOOK_SECRET` (после создания webhook)

1. LLM:
- хотя бы один ключ (`OPENAI_API_KEY` или другой)

1. Smoke:
- `VERIDOC_SMOKE_EMAIL` (заполнен ниже)
- `VERIDOC_SMOKE_PASSWORD` (заполнен ниже; хранить только на сервере)

---

## 1) Готовый `.env` (предзаполненный)

```env
# ---- Database ----
POSTGRES_USER=veridoc
POSTGRES_PASSWORD=
POSTGRES_DB=veridoc
POSTGRES_PORT=5432

# ---- Redis ----
REDIS_PORT=6379

# ---- API ----
API_PORT=8000
VERIDOC_SECRET_KEY=
VERIDOC_CORS_ORIGINS=https://veri-doc.app
VERIDOC_ENVIRONMENT=production
VERIDOC_BASE_URL=https://veri-doc.app/api

# ---- LLM (минимум 1 ключ обязателен) ----
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=
DEEPSEEK_API_KEY=

# ---- LemonSqueezy ----
LEMONSQUEEZY_API_KEY=
LEMONSQUEEZY_STORE_ID=
LEMONSQUEEZY_WEBHOOK_SECRET=

# ---- Smoke account ----
VERIDOC_SMOKE_EMAIL=eugenia@veridoc-app
VERIDOC_SMOKE_PASSWORD=

# ---- Licensing ----
VERIOPS_LICENSE_KEY=
```

---

## 2) Команды (копировать-вставить)

```bash
sudo apt update
sudo apt install -y git curl ca-certificates
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

sudo mkdir -p /opt/veridoc
sudo chown -R $USER:$USER /opt/veridoc
cd /opt/veridoc
git clone https://github.com/YevheniiaDolska/automated-docs-pipeline.git .
git checkout main

cp deploy/.env.example .env
chmod 600 .env
```

Секреты (сгенерировать на сервере):

```bash
openssl rand -hex 32   # VERIDOC_SECRET_KEY
openssl rand -hex 32   # VERIOPS_LICENSE_KEY
```

Запуск:

```bash
docker compose -f docker-compose.production.yml --env-file .env up -d --build
docker compose -f docker-compose.production.yml ps
```

Проверка:

```bash
curl -fsS https://veri-doc.app/api/health
curl -fsS https://veri-doc.app/api/health/ready
```

Smoke:

```bash
VERIDOC_BASE_URL=https://veri-doc.app/api \
VERIDOC_SMOKE_EMAIL=eugenia@veridoc-app \
VERIDOC_SMOKE_PASSWORD='PASTE_REAL_PASSWORD' \
python3 scripts/production_smoke.py

## 3) LemonSqueezy webhook events (что включить)

В вашем текущем backend обрабатываются события:

- `subscription_created`
- `subscription_updated` (включая смену плана)
- `subscription_cancelled`
- `subscription_resumed`
- `subscription_payment_success`
- `subscription_payment_failed`
- `subscription_payment_refunded`
- `subscription_trial_ending`

`subscription_plan_changed` отдельно не нужен, это часть `subscription_updated`.
`affiliate_activated` не обязателен для текущей серверной логики выплат в этом репо.
```
