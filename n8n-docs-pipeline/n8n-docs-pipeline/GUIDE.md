# Documentation Pipeline Prototype — Полная инструкция

## Что ты получишь

GitHub-репо с работающим docs-сайтом, который демонстрирует:
- MkDocs Material с Diátaxis-структурой
- Algolia DocSearch (бесплатный для open-source)
- GEO-линтер + валидация frontmatter в CI
- Vale + markdownlint + cspell на каждый PR
- Auto-deploy на GitHub Pages
- Мониторинг n8n GitHub commits + community topics (GitHub Actions)
- Шаблоны для типовых страниц

Тема: n8n (3-4 примера страниц). Система универсальна.

**Время: ~2 дня.**

---

## Фаза 0: Создание репо (15 мин)

```bash
# 1. Создай репо на GitHub (Public, с README)
# 2. Склонируй
git clone git@github.com:YOUR_USERNAME/n8n-docs-pipeline.git
cd n8n-docs-pipeline

# 3. Скопируй ВСЕ файлы из этого пакета в корень репо
#    (сохраняя структуру папок)

# 4. Установи зависимости
pip install mkdocs-material pymdown-extensions mkdocs-meta-descriptions-plugin
npm install -g cspell markdownlint-cli

# Vale:
# macOS: brew install vale
# Windows: choco install vale
# Linux: snap install vale

# 5. Синхронизируй Vale
vale sync

# 6. Проверь что работает
mkdocs serve
# Открой http://127.0.0.1:8000
```

---

## Фаза 1: Что делает каждый файл

### Конфиги (корень репо)

| Файл | Что делает |
|------|-----------|
| `mkdocs.yml` | Конфиг сайта: тема, навигация, плагины, поиск |
| `.vale.ini` | Конфиг Vale: какие стили применять |
| `docs-schema.yml` | Схема frontmatter: какие поля обязательны |
| `glossary.yml` | Глоссарий n8n-терминов для GEO-линтера |
| `cspell.json` | Словарь для проверки орфографии |
| `.markdownlint.yml` | Правила форматирования Markdown |
| `.gitignore` | Что не коммитить |

### Скрипты (scripts/)

| Файл | Что делает |
|------|-----------|
| `validate_frontmatter.py` | Проверяет frontmatter по схеме |
| `geo_lint.py` | GEO-линтер (9 правил из нашего пайплайна) |
| `new_doc.py` | Генерация новой страницы из шаблона |

### CI/CD (.github/workflows/)

| Файл | Что делает |
|------|-----------|
| `docs-check.yml` | При PR: Vale + markdownlint + cspell + frontmatter + GEO |
| `deploy.yml` | При merge в main: build + deploy на GitHub Pages |
| `monitor-n8n.yml` | Еженедельно: проверяет n8n releases + community |

### Контент (docs/)

| Файл | Тип (Diátaxis) | Пример чего |
|------|----------------|-------------|
| `getting-started/quickstart.md` | Tutorial | Первый workflow за 5 мин |
| `how-to/configure-webhook-trigger.md` | How-to | Настройка конкретной штуки |
| `concepts/workflow-execution-model.md` | Concept | Как устроен движок |
| `reference/nodes/webhook.md` | Reference | Параметры ноды |
| `troubleshooting/webhook-not-firing.md` | Troubleshooting | Решение проблемы |

### Algolia (overrides/)

| Файл | Что делает |
|------|-----------|
| `overrides/main.html` | Вставляет meta-теги из frontmatter в HTML |
| `overrides/partials/algolia-search.html` | UI Algolia DocSearch |

---

## Фаза 2: Настройка Algolia DocSearch (30 мин)

Algolia DocSearch бесплатен для open-source/технических docs.

### Шаг 2.1: Подай заявку

1. Иди на https://docsearch.algolia.com/apply/
2. Заполни: URL твоего docs-сайта (после deploy на GitHub Pages)
3. Одобрение обычно 1-3 дня
4. Получишь: `appId`, `apiKey`, `indexName`

### Шаг 2.2: Пока ждёшь — используй встроенный поиск MkDocs

Встроенный поиск (lunr.js) работает из коробки. Algolia — апгрейд, который добавляет фасеты.

MkDocs Material поддерживает tags plugin — это простейшая форма фасетов
(фильтрация по тегам). Она работает без Algolia и уже настроена в mkdocs.yml.

### Шаг 2.3: Когда получишь ключи — подключи Algolia

В `mkdocs.yml` раскомментируй блок `extra` с Algolia-конфигом и впиши свои ключи.

Фасетный поиск через Algolia работает так:
- Frontmatter рендерится в `<meta>` теги (через `overrides/main.html`)
- Algolia-краулер индексирует эти meta-теги как фасеты
- В поиске можно фильтровать по `product`, `content_type`, `n8n_component`

### Шаг 2.4: Расширенная настройка (после одобрения)

Когда Algolia одобрит — ты получишь доступ к Crawler Editor.
Там настраиваешь `attributesForFaceting`:

```json
{
  "attributesForFaceting": [
    "searchable(tags)",
    "filterOnly(content_type)",
    "filterOnly(product)",
    "filterOnly(n8n_component)"
  ]
}
```

---

## Фаза 3: Мониторинг n8n для doc gaps (20 мин)

### Источник 1: GitHub releases/commits

Файл `.github/workflows/monitor-n8n.yml` автоматически:
- Раз в неделю проверяет n8n GitHub releases
- Парсит CHANGELOG.md на новые фичи
- Создаёт GitHub Issue в твоём репо: "New n8n feature: [название]"

Как использовать:
1. Утром видишь issue "n8n 2.5: Chat node now supports approval buttons"
2. Решаешь: нужна ли новая страница / обновление существующей?
3. Если да — используешь шаблон: `python scripts/new_doc.py --type how-to`

### Источник 2: Community forum

n8n community на Discourse (community.n8n.io). RSS-фид доступен:
- `https://community.n8n.io/c/getting-started-with-n8n/docs-and-tutorials/6.rss`
- `https://community.n8n.io/c/questions/7.rss`

Monitor workflow (в `monitor-n8n.yml`):
- Раз в неделю проверяет RSS
- Ищет повторяющиеся вопросы (= doc gaps)
- Создаёт issue: "Community doc gap: [тема]"

### Как это работает на практике

Каждый понедельник ты открываешь GitHub Issues:
```
🏷 n8n-release: Chat node v2 - approval buttons (auto-created)
🏷 community-gap: 5 questions about webhook HMAC verification (auto-created)
🏷 stale-doc: webhook.md not updated in 45 days (auto-created)
```

Это твой бэклог. Приоритизируешь, берёшь в работу.

---

## Фаза 4: CI/CD настройка (15 мин)

### GitHub Pages

1. GitHub → Settings → Pages → Source: "GitHub Actions"
2. Push в main → `deploy.yml` автоматически:
   - Билдит сайт (`mkdocs build`)
   - Деплоит на GitHub Pages
   - Сайт доступен на `https://YOUR_USERNAME.github.io/n8n-docs-pipeline/`

### Проверки на PR

1. Создай ветку: `git checkout -b test/first-pr`
2. Измени любой .md файл
3. Push + создай PR
4. `docs-check.yml` автоматически запустит:
   - Vale (стиль: Google + GEO rules)
   - markdownlint (форматирование)
   - cspell (орфография + n8n-термины)
   - validate_frontmatter.py (схема метаданных)
   - geo_lint.py (GEO-оптимизация)
5. Результаты — прямо в PR

---

## Фаза 5: Повседневное использование

### Новая страница из шаблона

```bash
python scripts/new_doc.py --type how-to --title "Set up error handling in n8n workflows"
# Создаст docs/how-to/set-up-error-handling-in-n8n-workflows.md
# с заполненным frontmatter и скелетом по шаблону
```

### Проверка перед коммитом

```bash
# Всё сразу
vale docs/ && markdownlint docs/ && python scripts/validate_frontmatter.py && python scripts/geo_lint.py docs/

# Или по одному файлу
vale docs/how-to/configure-webhook-trigger.md
python scripts/geo_lint.py docs/how-to/configure-webhook-trigger.md
```

### Деплой

```bash
git add .
git commit -m "docs: add webhook trigger how-to guide"
git push origin main
# → auto-deploy за 2 минуты
```

---

## Чеклист: всё работает

```
[ ] mkdocs serve показывает сайт локально
[ ] Навигация: 5 табов (Getting Started, How-To, Concepts, Reference, Troubleshooting)
[ ] Теги кликабельны (встроенные фасеты)
[ ] Content tabs работают (Cloud | Self-hosted)
[ ] Mermaid-диаграммы рендерятся
[ ] vale docs/ находит стилистические проблемы
[ ] python scripts/validate_frontmatter.py проходит
[ ] python scripts/geo_lint.py находит GEO-проблемы (в тестовом файле)
[ ] PR запускает CI проверки
[ ] Merge в main деплоит на GitHub Pages
[ ] Algolia подключён (или встроенный поиск работает)
[ ] monitor-n8n.yml создаёт issues из n8n releases
```

---

## Что показывать на собеседовании

1. **Сайт** — ссылка на GitHub Pages. Выглядит профессионально.
2. **CI/CD** — открой любой PR, покажи автоматические проверки.
3. **GEO-линтер** — запусти на примере с ошибками, покажи вывод.
4. **Мониторинг** — покажи автоматически созданные issues из n8n releases.
5. **Шаблоны** — запусти `new_doc.py`, покажи как за 30 секунд создаётся скелет.
6. **Код** — GitHub репо целиком. Рекрутер/HM может посмотреть структуру.

Фраза для интервью:
"I built a documentation pipeline prototype that automates quality gates — GEO optimization for LLM discoverability, style linting, frontmatter validation — and monitors the product's GitHub releases and community forum for documentation gaps. Here's the live site, and here's what the CI pipeline looks like on a real PR."
