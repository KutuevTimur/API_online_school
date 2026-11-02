# Локальное окружение — T00

Проверено 15.10.2026. T00/T01 DONE. Docker Desktop работает; ниже инвентаризация T00 и актуальное дополнение T01.

## Факты

- Корень Git: `API_online_school`, ветка `dev`, HEAD `71fdcfaa2b14f00ca515d2d98529c9657eb36951`.
- Исходные изменения `rules_project.md` и untracked документы сохранены; stage/commit/push/deploy не выполнялись.
- `git ls-remote origin refs/heads/dev` не выполнен успешно: DNS `github.com` недоступен. Совпадение с origin в этой сессии не подтверждено; последний успешный snapshot — в CODE_REVIEW.
- `.venv/bin/python --version`: Python 3.14.0. Модули pytest, sqlalchemy, fastapi, dotenv, asyncpg найдены через `find_spec`; это не проверка их работы.
- `command -v docker`, `psql`, `pg_isready`: отсутствуют в PATH. PostgreSQL runtime и контейнеры не подтверждены.
- `.env*` в дереве проекта не найдены, значения окружения не выводились. Поиски личных файлов/серверов не повторялись.
- Попытка bind `127.0.0.1:55432` запрещена sandbox (`PermissionError`); свободность порта не установлена.
- Внешняя БД: **UNKNOWN**. Отсутствие env не доказывает отсутствие production.

## Контракт T01 (реализован)

| Параметр | Dev | Test |
|---|---|---|
| Compose project | `lgg-dev` | `lgg-test` |
| База | `lgg_dev` | `lgg_test` |
| Прикладная роль | `lgg_dev_app` | `lgg_test_app` |
| PostgreSQL host с хоста | `127.0.0.1` | `127.0.0.1` |
| Host port | `55431` | `55432` |
| Volume (project scoped) | `lgg-dev_postgres_data` | `lgg-test_postgres_data` |
| Media | отдельный backend volume `lgg-dev_media` | только `tmp_path_factory` pytest |
| Env source | `.env` | `.env.test`, без fallback на `.env` |

Отдельные экземпляры PostgreSQL создаёт Compose после явного локального запуска владельцем. Роли создаёт init script T01; test role без доступа к dev/prod, без SUPERUSER/CREATEDB/CREATEROLE. Секреты генерируются вне Git при подготовке runtime; сейчас не созданы. Старый compose с `online_school` не является выбранной целью.

Guard T01 до подключения/очистки должен требовать MODE=TEST, lgg_test, lgg_test_app, точный loopback host/55432 и ALLOW_TEST_DB_RESET=1, проверять фактический URL. Внутри сети Compose нужен отдельно определённый и проверяемый контракт, а не ослабление host guard. Происхождение контейнера подтверждать проектом lgg-test; localhost сам по себе недостаточен. Файлы удалять только из выделенного pytest tmp path. Не выполнять down -v для чужих проектов.

## Исходный блокер T00 (снят в T01)

Для выполнения T01 нужен Docker Desktop с запущенным daemon и Compose v2, доступными через `docker version` и `docker compose version`; затем проверить оба порта, подготовить отдельные env и compose по T01. Системный runtime в этой сессии не устанавливался. После этого реализовать T01 и выполнить guard unit tests, synthetic lifecycle, compose config и collect-only. До guard не запускать старые DB fixtures/tools. Миграционный baseline относится к T02.

T00: read-only inventory выполнен, порт и origin не подтверждены по причинам выше. Pytest, создание/сброс БД, миграции, Docker build/config — NOT RUN.

## Выполнение T01 — 15.10.2026

DONE по критериям T01. Docker Desktop запущен: Engine 29.8.2; современный Compose 5.6.0 (`docker compose`, преемник v2). Создан только проект lgg-test; контейнер lgg-test-postgres-1 healthy, loopback 55432. Тестовая БД lgg_test, роль lgg_test_app без SUPERUSER/CREATEDB/CREATEROLE; read-only SQL подтвердил контракт, public tables=0. Dev port 55431 свободен; dev контейнеры не создавались.

Реализованы явные .env/.env.test без test fallback; guard до создания engine и DB операций, проверка фактического engine URL/session bind; защищены fixtures, standalone tools и дополнительный legacy creator. Файлы тестов только tmp_path_factory, rmtree из fixtures удалён. Приложение использует один config/engine и dispose в lifespan; tests передают конфиг/DI overrides. Dev/test compose разделены по роли/имени/порту/volume; dev media persistent. Redis optional. Добавлены dummy env examples, dockerignore/gitignore и точные команды README. Локальные секреты созданы в ignored env с mode 0600, значения не выводились.

Проверки:
- `MODE=TEST .venv/bin/python -m pytest tests_unit -q`: **14 passed**, включая 6 отрицательных конфигураций, подменённый DSN/query, отказ до connection/remover, разрешённый target, media outside allocation, отсутствие fallback, lifecycle/dispose, session bind.
- `MODE=TEST .venv/bin/python -m pytest --collect-only -q`: **141 tests collected**; это не полный запуск.
- `docker compose --env-file .env.test -f compose.test.yaml config --quiet`: PASS.
- `docker compose --env-file .env -f docker-compose.yaml config --quiet`: PASS.
- `docker compose --env-file .env.test -f compose.test.yaml up -d --wait postgres`: PASS после исправления init (shell bind mount получил bad interpreter/Permission denied; заменён на psql init-app.sql). Пересоздан только новый пустой volume lgg-test этой сессии.
- Read-only connection smoke: PASS; роль/БД/ограничения подтверждены. `git diff --check`: PASS.

Не проверено: полный функциональный pytest, Alembic clean/prior-state, dev backend build/start, UI/E2E. Это не утверждение готовности приложения. Внешняя БД UNKNOWN и не тронута. Следующее — T02, миграционный baseline по отдельному поручению. Ветка dev, HEAD 71fdcfa; commit/push/PR/deploy отсутствуют. Тестовый контейнер оставлен работающим; остановка без удаления данных — в README.
