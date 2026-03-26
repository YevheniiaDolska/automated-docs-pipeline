# One-URL Beginner Launch Checklist (VeriDoc)

Этот файл — полный, простой, пошаговый план запуска с одним доменом (`https://yourdomain.com`) и маршрутом API через `/api`.

## 0) Что нужно от вас (без этого запуск невозможен)

Соберите и пришлите мне:

1. SSH-доступ к серверу:
- IP сервера
- порт (обычно 22)
- user (например ubuntu/root)
- способ входа: пароль или SSH key
- есть ли sudo права

2. Домен:
- ваш один URL (например `https://yourdomain.com`)
- доступ к DNS (где управляются записи домена)

3. LemonSqueezy:
- `LEMONSQUEEZY_API_KEY`
- `LEMONSQUEEZY_STORE_ID`
- `LEMONSQUEEZY_WEBHOOK_SECRET`
- checkout-ссылки:
  - Starter (общая ссылка, где выбор month/year внутри checkout)
  - Pro (общая ссылка, где выбор month/year внутри checkout)
  - Business/Enterprise: manual invoice (ссылка на ваш contact, сейчас Calendly)

4. LLM ключ(и):
- хотя бы один: `OPENAI_API_KEY` (или `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY`)

5. Секреты (создадим командой):
- `VERIDOC_SECRET_KEY`
- `VERIOPS_LICENSE_KEY` (для encrypted capability pack)

---

## 1) Архитектура с одним URL (как у вас)

Будет так:
- `https://yourdomain.com/` -> landing
- `https://yourdomain.com/api/*` -> VeriDoc API
- webhook LemonSqueezy:
  `https://yourdomain.com/api/billing/webhooks/lemonsqueezy`

Это поддерживается в `deploy/nginx.conf` (Option B, path-based).

---

## 2) День 1 — сервер и запуск

На сервере:

```bash
# 1) базовая подготовка
sudo apt update
sudo apt install -y git curl ca-certificates

# 2) docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3) проект
sudo mkdir -p /opt/veridoc
sudo chown -R $USER:$USER /opt/veridoc
cd /opt/veridoc
git clone https://github.com/YevheniiaDolska/automated-docs-pipeline.git .
git checkout main
```

Создать `.env`:

```bash
cp deploy/.env.example .env
chmod 600 .env
```

Сгенерировать секреты:

```bash
openssl rand -hex 32   # VERIDOC_SECRET_KEY
openssl rand -hex 32   # VERIOPS_LICENSE_KEY
```

Вписать в `.env` минимум:
- `POSTGRES_PASSWORD`
- `VERIDOC_SECRET_KEY`
- `VERIDOC_CORS_ORIGINS=https://yourdomain.com`
- `LEMONSQUEEZY_API_KEY`
- `LEMONSQUEEZY_STORE_ID`
- `LEMONSQUEEZY_WEBHOOK_SECRET`
- хотя бы один LLM key
- `VERIDOC_BASE_URL=https://yourdomain.com/api`
- `VERIDOC_SMOKE_EMAIL`
- `VERIDOC_SMOKE_PASSWORD`

---

## 3) Nginx под один URL

В `deploy/nginx.conf`:
- оставить/включить Option B: Path-based routing
- маршрут `/api/` должен идти в `api:8000`

Потом запуск:

```bash
docker compose -f docker-compose.production.yml --env-file .env up -d --build
docker compose -f docker-compose.production.yml ps
```

---

## 4) Проверки (обязательно)

```bash
curl -fsS https://yourdomain.com/api/health
curl -fsS https://yourdomain.com/api/health/ready
```

Smoke:

```bash
VERIDOC_BASE_URL=https://yourdomain.com/api \
VERIDOC_SMOKE_EMAIL=smoke@yourdomain.com \
VERIDOC_SMOKE_PASSWORD='StrongPassword123!' \
python3 scripts/production_smoke.py
```

---

## 5) Landing (что настроить)

Файл лендинга:
`C:\Users\Kroha\Documents\development\git_wrapper\veridoc-landing.html`

Проверить, что:
- Starter/Pro кнопки ведут на правильные Lemon checkout URL (с выбором month/year внутри)
- Business/Enterprise кнопки ведут на `Contact for Invoice`
- ссылка на условия рефералки есть рядом с отключением бейджа на старших тарифах
- monthly/yearly toggle работает

---

## 6) Что уже закрыто

- `npm run lint` проходит без `--no-verify`
- markdown/frontmatter долг закрыт

---

## 7) Что осталось до полного GO (ручное)

- DNS/TLS на вашем домене
- реальный webhook тест из LemonSqueezy (test mode)
- backup/restore на сервере
- мониторинг/алерты

---

## Готовый `.env` шаблон с пустыми полями “вставь сюда”

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
VERIDOC_CORS_ORIGINS=https://yourdomain.com
VERIDOC_ENVIRONMENT=production
VERIDOC_BASE_URL=https://yourdomain.com/api

# ---- LLM (минимум 1 ключ обязателен) ----
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=
DEEPSEEK_API_KEY=

# ---- LemonSqueezy ----
LEMONSQUEEZY_API_KEY=
LEMONSQUEEZY_STORE_ID=
LEMONSQUEEZY_WEBHOOK_SECRET=

# Опционально (если используете variant IDs)
LS_VARIANT_STARTER_MONTHLY=
LS_VARIANT_STARTER_ANNUAL=
LS_VARIANT_PRO_MONTHLY=
LS_VARIANT_PRO_ANNUAL=
LS_VARIANT_BUSINESS_MONTHLY=
LS_VARIANT_BUSINESS_ANNUAL=
LS_VARIANT_ENTERPRISE_MONTHLY=
LS_VARIANT_ENTERPRISE_ANNUAL=

# ---- Smoke account ----
VERIDOC_SMOKE_EMAIL=
VERIDOC_SMOKE_PASSWORD=

# ---- Licensing ----
VERIOPS_LICENSE_KEY=
```

---

## Точный чеклист “галочки по шагам” на 2 дня

### День 1

- [ ] Есть SSH-доступ на сервер
- [ ] Установлены Docker и Git
- [ ] Репозиторий склонирован в `/opt/veridoc`
- [ ] `.env` создан и заполнен обязательными значениями
- [ ] Включен Option B в `deploy/nginx.conf`
- [ ] Стек поднят через `docker compose`
- [ ] `https://yourdomain.com/api/health` отвечает
- [ ] `https://yourdomain.com/api/health/ready` отвечает

### День 2

- [ ] Вебхук LemonSqueezy указывает на `/api/billing/webhooks/lemonsqueezy`
- [ ] Тестовые события биллинга успешно дошли
- [ ] `production_smoke.py` прошел
- [ ] Проверен backup
- [ ] Проверен restore (на отдельной БД/слоте)
- [ ] Заполнен `production-gate.md` по факту

---

## Список “что прислать мне, чтобы я сделал всё за вас удаленно”

- [ ] SSH: host, port, username, пароль/ключ
- [ ] Подтверждение sudo-доступа
- [ ] Домен и доступ к DNS
- [ ] `LEMONSQUEEZY_API_KEY`
- [ ] `LEMONSQUEEZY_STORE_ID`
- [ ] `LEMONSQUEEZY_WEBHOOK_SECRET`
- [ ] хотя бы один LLM API key
- [ ] Starter checkout URL
- [ ] Pro checkout URL
- [ ] Contact URL для Business/Enterprise invoices
- [ ] ссылка на страницу условий рефералки
- [ ] разрешение сгенерировать `VERIDOC_SECRET_KEY`
- [ ] разрешение сгенерировать `VERIOPS_LICENSE_KEY`
