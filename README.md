# TeenTöö: настройка на GitHub

Что внутри:
- `index.html` — сайт (читает вакансии из `listings.json`, скрывает закрытые по дате).
- `listings.json` — список вакансий.
- `update_listings.py` — скрипт обновления.
- `.github/workflows/update.yml` — расписание: запуск примерно раз в 3 дня.

## 1. Аккаунт и репозиторий
1. Зарегистрируйся на github.com (бесплатно).
2. Нажми **+** → **New repository**. Имя, например, `teentoo`. Тип **Public**. Нажми **Create repository**.

## 2. Загрузка файлов
1. В репозитории нажми **Add file → Upload files** и перетащи `index.html`, `listings.json`, `update_listings.py`. Нажми **Commit changes**.
2. Папку `.github` перетаскиванием часто не загрузить (она скрытая). Сделай так: **Add file → Create new file**, в поле имени введи `.github/workflows/update.yml` (слэши сами создадут папки), вставь туда содержимое файла `update.yml` и нажми **Commit changes**.

## 3. Включить сайт (GitHub Pages)
**Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main`, папка `/ (root)` → Save.**
Через 1–2 минуты сайт откроется по адресу `https://ТВОЙ-ЛОГИН.github.io/teentoo/`.

## 4. Разрешить автообновление
**Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**

## 5. Проверить запуск
Вкладка **Actions** → слева **Update job listings** → **Run workflow**. Зелёная галочка значит, что всё работает. После этого расписание запускается само.

## 6. Источник новых вакансий (по желанию)
Без источника скрипт только убирает закрытые вакансии. Новые ты добавляешь вручную: открой `listings.json` на GitHub (карандаш **Edit**), скопируй блок любой вакансии и поменяй поля. Чтобы вакансии добавлялись сами, нужен источник данных. Один из вариантов — парсер на apify.com (я его не проверял, он может быть платным, проверь правила сайтов-источников):
1. **Settings → Secrets and variables → Actions → Secrets → New repository secret**: имя `APIFY_TOKEN`, значение — твой токен Apify.
2. Вкладка **Variables → New repository variable**: `APIFY_ACTOR` (например `studio-amba~tootukassa-scraper`) и при необходимости `APIFY_INPUT` (настройки парсера в JSON).
3. Запусти workflow вручную и посмотри `listings.json`. Названия полей у парсера могут отличаться, тогда поправь функцию `convert` в `update_listings.py`.

Вакансии из парсера не содержат переводов и точного возраста. Для пользователей младше 18 лет они скрыты, пока возраст не указан.

## 7. Свой домен
**Settings → Pages → Custom domain**, затем добавь DNS-записи у регистратора по подсказкам GitHub.

## Важно
- Расписание GitHub иногда запускается с задержкой.
- Поле `updated` в `listings.json` меняется только когда скрипт получил новые вакансии.
