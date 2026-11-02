# Состояние разработки

Обновлено: 15.10.2026. **T00 DONE, T01 DONE.** Следующая задача — T02 (TODO), миграционный baseline по отдельному поручению. Docker Desktop работает, lgg-test healthy; неизвестная БД не затронута. Результаты — [карточка T01](tasks/T01.md), контракт — [ENVIRONMENT](ENVIRONMENT.md).

Ветка `dev`, HEAD `71fdcfaa2b14f00ca515d2d98529c9657eb36951`. Документы локально изменены/новые, не закоммичены. Commit: none. PR: none. Deploy: none. Проверять status заново, не считать этот snapshot вечным.

## Уже выполнено в планировании

- [x] Прочитаны требования и правила; сохранены согласованные требования в PRODUCT, GPT стал коротким входом.
- [x] Удалённые main/dev сверены с локальными, код ключевых сценариев прочитан, AST всех Python-файлов проверен.
- [x] Подготовлены исследование платформ, правовой обзор с ограничениями источников, архитектура, backlog и карточки T00–T04.
- [x] Подготовлены workflow, промпты, каталог навыков с pinned SHA и разделением available/proposed; ничего не установлено.
- [x] Исследованы локальные признаки БД: env/dumps/media не найдены; внешняя БД остаётся UNKNOWN.

## Реализация: единый реестр статусов

`TODO` не начато; `IN_PROGRESS` выполняется; `VERIFY` написано, нужно проверять; `BLOCKED` причина и следующий шаг обязательны; `DONE` критерии выполнены. Обозначение READY — вычисляемое: TODO с выполненными зависимостями, не отдельный статус.

| ID | Статус | Доказательство / остаток |
|---|---|---|
| T00 | DONE | Инвентаризация и изоляция описаны в ENVIRONMENT; origin DNS/port sandbox ограничения записаны |
| T01 | DONE | 14 guard/unit passed, 141 collected, compose dev/test config PASS, lgg-test healthy, role smoke PASS; полный baseline — T02 |
| T02 | TODO | Миграция содержит autcrement; PostgreSQL baseline не выполнен |
| T03 | TODO | Public DTO/active/JWT defects остаются |
| T04 | TODO | Replay/concurrency/revocation не исправлены |
| T05 | TODO | Admin/teacher_students/bootstrap отсутствуют |
| T05b | TODO | D01 и invite/reset |
| T06 | TODO | Object permission matrix не реализована |
| T07 | TODO | D02; архив Lesson/read-only/purge |
| T08 | TODO | Персональный урок, cancellation, links |
| T08b | TODO, optional | N weekly copies; допускается перенос после пилота |
| T09 | TODO | Submission lifecycle/append/version |
| T10 | TODO | Review queue и concurrent checking |
| T11 | TODO | D04, deadlines/debts |
| T12 | TODO | D06, storage/limits/compression |
| T13 | TODO | Notifications/audit |
| T14 | TODO | Frontend/auth bridge/design |
| T15a | TODO | Ученический кабинет |
| T15b | TODO | Кабинет teacher |
| T15c | TODO | Admin |
| T16 | TODO | E2E/CI/regression |
| T17 | TODO | Production bundle/runbook |
| T18 | TODO | Backup/restore/monitoring |
| P01 | TODO | Оператор/правовые процедуры до реальных ПД |
| P02 | TODO | Timeweb release, только отдельное поручение |
| P03 | TODO | Пилот |
| F01–F06 | DEFERRED | После MVP, см. TASKS |

## Выполненные и невыполненные проверки

15.10: git remote SHA — совпали; AST main/dev — без syntax errors, 60/184 Python-файла, 5/127 определений тестов. Это статический анализ, не functional validation. Подробности — CODE_REVIEW.

Полный pytest, Docker build, PostgreSQL migration, UI/browser, нагрузка, restore/deploy — **NOT RUN**. Guard T01 реализован; unit/collect-only/Compose/role smoke выполнены, результаты ниже. Навыки проверены чтением SKILL.md, не исполнением всех scripts. Официальный портал РКН/публикация поправки не открылись, fallback и повторная проверка описаны PRIVACY.

## Последняя передача

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

Git handoff 15.10.2026: diff T00/T01 проверен; ветка `codex/t00-t01-environment`, origin/dev подтверждён 71fdcfa. Повторно 14 unit passed, 141 collected, diff check PASS. Исправлен multi-statement вызов в test drop_schema (две отдельные execute). Владелец разрешил commit/push/draft PR в dev; merge/deploy запрещены. Посторонние planning/design/instruction документы исключены из коммита.

Git result 15.10.2026: ветка `codex/t00-t01-environment`; implementation commit `8be580f` отправлен в origin. Draft PR в dev: https://github.com/KutuevTimur/API_online_school/pull/1 . Локальные секреты проверены сравнением с содержимым commit, не включены. Merge/deploy не выполнялись. Ручная проверка владельцем сейчас не требуется: пользовательский сценарий ещё не готов. Следующая задача T02 по отдельному поручению; этот PR остаётся draft.
