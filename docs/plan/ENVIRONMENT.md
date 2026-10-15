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

## T02 — 15.10.2026

Миграционный baseline выполнен только на lgg-test. Ветка
codex/t00-t01-environment, исходный HEAD 662a992; новых commit/push/merge/deploy нет.
Контейнер и порт подтверждены Compose. Alembic использует явный guarded test config;
миграции не создают media в проекте. Чистая цепочка d98c55d6402c → 56c4070bf9cd,
no-op и round-trip проверяются отдельными tests/migrations через Alembic.
Synthetic snapshot покрывает все 12 таблиц; текущие ORM совпадают с инспекцией БД,
включая enum labels. Main baseline явно отклоняется.
Внешняя БД остаётся UNKNOWN и не затронута. Mapping/downgrade и команды —
README и TEST_BASELINE.md. Полный исходный pytest: 141 passed, 0 failed, 0 skipped.


## Приёмка перед T08 — 15.10.2026

Впервые собран/запущен lgg-dev: новые postgres_data/media volumes, PostgreSQL
healthy на 127.0.0.1:55431, backend 127.0.0.1:8018. До миграций public tables=0;
lgg_dev_app без SUPERUSER/CREATEDB/CREATEROLE. Head 811d7911d0b4, schema diff пустой.
Synthetic HTTP и restart persistence PASS; оба контейнера оставлены работающими.
Файлы persistent в lgg-dev_media; локальный client media-audit-client не является
хранилищем backend. Полный [отчёт](T00_T07_ACCEPTANCE.md), команды и остановка — README.
Неизвестная БД не затронута. Dev MODE=LOCAL в исходном ignored env; runner MODE=DEV.


## T08 — 15.10.2026

Существующий synthetic lgg-dev обновлён migration 29e67248e0f3 без reset/удаления
volumes; schema diff пустой. Backend пересобран и перезапущен, сохранность
status/time/URL и прежнего PDF SHA256 проверена по HTTP. Dev остаётся на
127.0.0.1:8018, PostgreSQL healthy 55431; guarded test 55432 отдельно.
[Карточка T08](tasks/T08.md) содержит итоговые проверки. Учётные данные/ID только
в ignored .env.audit-access (0600), не в документации/Git/чате.

## T09 — 15.10.2026

Synthetic lgg-dev обновлён migration `8a575436b7db` без reset/удаления volumes.
Backend build/start и HTTP smoke: 28 запросов + независимая concurrent create
пара (201/409) PASS. После restart login/checked answer/version/PDF bytes/OpenAPI
PASS. Dev alembic check: schema diff пустой. Старые DB/media сохранены.
Dev остаётся 127.0.0.1:8018, файлы — прежний persistent `lgg-dev_media`;
удалённые attachments ожидают existing admin cleanup retry в durable queue.
Учётные данные и synthetic IDs только ignored `.env.audit-access` (0600).
Test остаётся отдельной guarded lgg-test на loopback 55432. Неизвестная БД
не затронута. Итог тестов и ограничения — [карточка T09](tasks/T09.md).


## T10 — 15.10.2026

Synthetic dev backend пересобран и запущен с T10 без reset/удаления volumes.
29 HTTP checks PASS, restart persistence 8 PASS (повтор на окончательном build
также PASS); dev alembic check PASS. Новый DDL отсутствует.
Guarded lgg-test: полный pytest 395 passed, migration suite 20 passed;
после тестов upgrade head/check PASS, чистая schema на 8a575436b7db.
Dev 127.0.0.1:8018/docs остаётся работающим, прежний persistent media volume
сохранён. Неизвестная БД не затронута. Подробнее — tasks/T10.md.


## T11 — 15.10.2026

Synthetic dev обновлён migration `689ceabc2b0c` без reset/удаления volumes.
Последний build/up/healthy и 29 T11 HTTP PASS; restart retained 7 T11 + 8 T10
HTTP PASS, прежний PDF сохранён; dev schema diff пустой. Legacy закрытые сроки
дополнительно проверены: 0 расхождений. Dev 127.0.0.1:8018/docs, persistent
lgg-dev_media сохранён, credentials/IDs только ignored .env.audit-access (0600).
Guarded lgg-test отдельно на 55432: полный pytest 421, финальные scoped 95,
migrations 23, guard 14 PASS; после migration suite upgrade/check PASS,
пустые 21 domain tables на head 689ceabc2b0c. Неизвестная БД не затронута.
Подробности и ограничения — tasks/T11.md.

## T12 — 15.10.2026

Оба isolated targets сохранены; текущий head `36a8711f7799`. Три добавочные
миграции T12 прошли clean/prior-state/round-trip/unsafe downgrade checks.
Полный pytest 478, финальные scoped 82, migrations 27, unit 38 PASS; подробности T12.
Dev backend build/up/HTTP 33/restart 24 PASS, schema diff пустой. Порт 8018,
volume lgg-dev_media (/app/media), DB 55431. Явный MODE=DEV добавлен в backend Compose
(прежний env давал LOCAL и maintenance правильно отказывал). Test guard 55432 не
ослаблен; maintenance сравнивает также реальный engine/session.

D06 synthetic визуальная приёмка принята: dev PHOTO_ORIGINALS_APPROVED=1.
Новые originals удаляются через durable queue после успешного ready/link commit;
не массовая обработка старой истории. Legacy 5/5 copied/hash verified, 0 failed,
reader LEGACY_FILE_READS=0. Старые copies/0600 manifests сохранены на 7 дней;
повреждение новой копии блокирует expiry deletion. Worker 60s, orphan grace 24h,
DB/shared/manifest refs защищены. Runtime assets=32, pending cleanup=0 после smoke.

Секреты/IDs по-прежнему только ignored env/`.env.audit-access`; значения не выводились.
Внешняя БД, реальные ПД, production и backup restore не затрагивались/не проверялись.

Финальный preflight: guarded lgg-test head 36a8711f7799, users/courses/assets = 0/0/0;
both Compose config --quiet и git diff --check PASS. Dev сохранён работающим.
