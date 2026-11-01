# LGG — локальная разработка

Онлайн-школа: FastAPI/SQLAlchemy/PostgreSQL в `src/`, React/TypeScript/Vite в
`frontend/`. Код развивается от dev во внутреннем репозитории `API_online_school`.

Начать с [GPT](GPT.md) и [STATUS](docs/plan/STATUS.md).
**Единый план до MVP — [TASKS](docs/plan/TASKS.md).**
[Карта документов](docs/plan/README.md) объясняет назначение остальных источников.
Доказательства последней сверки — [аудит 21.10](docs/plan/CHECKUP_2026_10_21.md).

## Окружения и данные

| Окружение | Адрес / назначение |
|---|---|
| Текущий локальный preview | `127.0.0.1:5173` → backend `8019` → guarded test PostgreSQL `55432` |
| Dev | backend `8018`, PostgreSQL `55431`, отдельные `lgg-dev_postgres_data` / `lgg-dev_media` |
| Production / внешняя БД | Не настроены/не подтверждены этим preview; подготовка T17/T18/P01/P02 |

Preview сейчас содержит сохраняемые аккаунты, занятия и материалы. Имя test БД
**не разрешает их сброс**. Приватные входы: `frontend/.artifacts/t15b1-login.txt`
(0600, ignored); файл не печатать в чат/логи. Media preview находятся во временном
OS каталоге из `files.media_root` приватного JSON; это не долговременное хранилище.
Не перезапускать `scripts/t14e_preview.py` для обычного продолжения: он создаёт
новый namespace/media и меняет файл входов. Восстановление текущего запуска —
[ENVIRONMENT](docs/plan/ENVIRONMENT.md#сохранение-текущего-preview).

## Безопасные локальные проверки без БД

Зависимости уже установлены; для аудита не выполнять pip/npm install, npm ci или npx.
Из корня репозитория:

```sh
./scripts/ast-index update
MODE=TEST .venv/bin/python -m pytest tests_unit -q
export PATH="$PWD/.local-runtime/bin:$PATH"
npm --prefix frontend run test:unit
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend run api:types:check
npm --prefix frontend run check:tokens
npm --prefix frontend run build
```

`api:types:check` сравнивает схему из исходной фабрики без подключения к БД.
[Frontend README](frontend/README.md) — runtime, файлы и команды UI;
[AST_INDEX](docs/plan/AST_INDEX.md) — symbol/outline/refs и ограничения индекса.

## Перед DB-тестами и миграциями

Сначала прочитать [T01](docs/plan/tasks/T01.md), фактические fixtures и
`src/core/config/test_guard.py`. `MODE=TEST` недостаточно: нужны точные target,
engine, session bind, SQL identity и изолированные media. Read-only preflight:

```sh
MODE=TEST PYTHONPATH=. .venv/bin/python scripts/test_preflight.py
```

`tests/conftest.py` очищает таблицы; migration tests сбрасывают public schema.
Не запускать их на действующем preview. Перед такими тестами остановить preview,
обеспечить проверенную копию и точное восстановление текущих данных/sequence/media
либо отдельный совместимый guarded disposable target. Не ослаблять guard ради
нового порта. После проверок восстановить прежний preview и проверить входы/файлы.
Никогда не использовать reset/fresh seed, `down -v`, drop или stamp для исправления
текущих аккаунтов. Исторические smoke-скрипты сначала читать: некоторые пишут в dev.

## Контракты и запуск

Актуальные API — `src/modules/*/views.py`, DTO и source-generated
`frontend/src/shared/api/schema.d.ts`; правила — PRODUCT/DECISIONS/ARCHITECTURE.
Миграции — `src/migrations/versions/`; данные обновляются Alembic, не create_all
при обычном запуске. Регистрация routers/models проверяется в `api/app.py` и
`db_models/__init__.py`. Учительская проверка поддерживает JSON `/teacher` и
multipart `/review`; результат и файлы проверки доступны ученику.

Dev Compose/Dockerfile не являются production bundle. `.dockerignore` исключает
секреты, приватные артефакты и локальные зависимости; build/image inspection в
последнем аудите не выполнялись. Доставка и приёмка production — только по TASKS.
Commit/push/deploy требуют отдельного запроса владельца.

[Прежний подробный README](docs/plan/history/README_before_2026-10-21.md) — история
этапов T00–T14, не актуальный справочник API или безопасная команда запуска.
