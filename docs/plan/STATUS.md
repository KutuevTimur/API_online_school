# Состояние разработки

Обновлено: 15.10.2026. **T00–T12 DONE локально (включая T05b и T12a/b/c); T08b optional отложена.**
T00–T07 повторно проверены в отдельном dev по HTTP; исправлены два дефекта PATCH курса.
[Отчёт приёмки](T00_T07_ACCEPTANCE.md). T12 DONE локально, D06 и synthetic читаемость приняты; далее T13 по отдельному поручению. D01–D06 приняты 15.10.2026. Миграции проверены локально
на lgg-test, неизвестная БД не затронута. [TEST_BASELINE](TEST_BASELINE.md).

Ветка `codex/t00-t01-environment`; T02–T09 сохранены в `2dfd49c`.
По поручению владельца T10–T12 сохраняются одним локальным коммитом вместе с этой записью;
его SHA: `git log -1 --oneline`. Push/merge/deploy не выполняются и не разрешены.
Существующий draft PR #1 не обновлялся. Исходные посторонние документы сохранены.

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
| T02 | DONE | Clean/prior-state/round-trip/main refusal: 3 migration tests; полный набор 144 passed; schema diff пустой |
| T03 | DONE | Public UserResponse/active/JWT regressions; полный набор 181 passed |
| T04 | DONE | Digest/family/atomic rotation/auth_version; полный набор 197 passed |
| T05 | DONE | ADMIN/teacher_students/atomic creation/bootstrap; полный набор 216 passed |
| T05b | DONE | Invite/reset/nullable email/username login; 240 passed, 8 migrations passed; schema diff пустой |
| [T06](tasks/T06.md) | DONE | Централизованные SQL policies, D01 profiles/avatar/files; 263 passed, 8 migrations passed, schema diff пустой |
| [T07](tasks/T07.md) | DONE | D02 archive/cutoff/restore/admin purge + durable cleanup; 290 passed, 11 migrations passed, schema diff пустой |
| [T08](tasks/T08.md) | DONE | Атомарный урок+ученик, UTC/default55/status/call links/warnings; 333 passed, 18 migrations passed, 39 T08 HTTP PASS |
| T08b | TODO, optional | N weekly copies; допускается перенос после пилота |
| [T09](tasks/T09.md) | DONE | Один working answer, submit/version, append/delete/swap, immutable history; полный 361 passed + финальные T09 27 passed, 20 migrations, 28 HTTP + concurrent pair PASS |
| [T10](tasks/T10.md) | DONE | D05, version/grade review и SQL queue; 395 passed, 20 migrations, 14 guard, 29 HTTP + 8 restart PASS |
| T11 | DONE | D04 принят; placements/deadline/debt/freeze; полный 421 + финальные scoped 95, migrations 23 |
| [T12](tasks/T12.md) | DONE | Storage/assets/limits/quota/WebP/legacy migration/GC; full 478 + финальные scoped 82, migrations 27, unit 38; HTTP 33, dev legacy остаток 0 |
| T12a | DONE | Immutable local/legacy adapters, explicit FK, guarded streaming/Range, byte/count/quota, failure/unknown COMMIT safe |
| T12b | DONE локально | D06 + synthetic чтение приняты; WebP ≤2560/q85, новые originals post-commit cleanup; реальные фото/устройства/UI не заявляются |
| T12c | DONE локально | Manifest/hash copy 5/5; legacy reads off; 7-day copies, 24h orphan grace, 60s worker, shared refs/purge/restart |
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

Исторический snapshot до T02: полный pytest и миграции ещё не выполнялись. Актуальный результат T02 ниже. Docker build, UI/browser, нагрузка, restore/deploy — **NOT RUN**. Guard T01 реализован; unit/collect-only/Compose/role smoke выполнены, результаты ниже. Навыки проверены чтением SKILL.md, не исполнением всех scripts. Официальный портал РКН/публикация поправки не открылись, fallback и повторная проверка описаны PRIVACY.

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


## Выполнение T02 — 15.10.2026

Исправлена только исполнимость initial DDL; следующая revision 56c4070bf9cd
согласует soft-delete двух таблиц с ORM. Synthetic backfill проверяет все строки;
deleted_at NULL. Main baseline отвергается до migration DDL без stamp/drop.
Clean/no-op/round-trip и snapshot всех 12 таблиц проходят, metadata diff пустой,
enum labels совпадают. Полный старый набор: 141 passed; финальный совместный:
**144 passed, 0 failed, 0 skipped**, 37.86s. Expectations не подгонялись.
Все команды, ограничения и дальнейшие auth дефекты: TEST_BASELINE.md.

Ручная проверка владельцем сейчас не нужна: пользовательского сценария пока нет.
Следующее T03 — публичные DTO/active/JWT. Новых Git операций и deploy нет.


Финальное состояние lgg-test: после общего pytest повторно выполнены migration tests
(3 passed, 5.34s), затем MODE=TEST .venv/bin/alembic upgrade head и alembic check:
PASS, «No new upgrade operations detected». Оставлена пустая synthetic схема
из 12 доменных таблиц на head 56c4070bf9cd, контейнер работает.
git diff --check: PASS. Новых commit/push/merge/deploy нет.


## Выполнение T03 — 15.10.2026

T03 DONE локально на `codex/t00-t01-environment`, HEAD `662a992`.
Registration (включая master route/alias) и четыре password routes используют
существующий `UserResponse`; внутренний `UserDTO` с hash сохранён.
Login/access/refresh проверяют активность единым helper; missing/inactive account
и invalid refresh/JWT возвращают 401 `Invalid credentials` без раскрытия аккаунта.
JWT проверяет подпись с algorithm только из trusted config, обязательные exp/sub,
числовой конечный exp с будущим сроком и строковый положительный sub в диапазоне
PostgreSQL INTEGER. TypeError/ValueError/JWTError/OverflowError нормализуются.

Проверки на guarded lgg-test (healthy, loopback 55432):
- `MODE=TEST .venv/bin/python -m pytest tests/modules/auth tests/modules/users -q --tb=short`: 71 passed, 15.30s (до двух дополнительных regressions).
- `MODE=TEST .venv/bin/python -m pytest -q --tb=short`: **181 passed**, 43.70s, 0 failed/0 skipped; 37 новых regressions T03.
- JSON всех registration/password aliases и вложенных public profiles без hash;
  публичные response schemas OpenAPI проверены рекурсивно. Active login/access/refresh
  сохранены; отключение сразу запрещает старый access и новые токены.
- Первый sandbox запуск: 71 setup errors из-за запрета loopback socket, до тестов;
  повтор с разрешённым локальным доступом прошёл. Это не функциональные failures.
- Финальные migration tests: 3 passed, 5.84s; `MODE=TEST .venv/bin/alembic upgrade head`
  и `MODE=TEST .venv/bin/alembic check`: PASS, schema diff пустой.

`git diff --check`: PASS.
Оставлена пустая synthetic схема lgg-test на head 56c4070bf9cd; контейнер работает.
Новых commit/push/merge/deploy нет; исходные документы и изменения T02 сохранены.
P0 целиком НЕ закрыт: replay/concurrency/revocation — T04; роли и object permissions — T05–T06.
UI/E2E/dev backend запуск не проверялись. Ручная проверка владельцем сейчас не нужна:
новый пользовательский интерфейс не добавлен, API smoke покрыт автоматическими тестами.
Следующее — T04 по отдельному поручению.


## Выполнение T04 — 15.10.2026

T04 DONE локально на `codex/t00-t01-environment`, HEAD `662a992`.
Refresh хранится только как digest с family_id; ротация атомарна, User → Token
row locks, один commit и rollback при ошибке. Replay отзывает семейство.
Logout проверяет владельца, повторный/unknown/foreign возвращают одинаковый 200.
Password change/reset отзывает все refresh целевого пользователя и повышает
JWT auth_version. Legacy JWT без ver отклонены. TTL настраиваются env,
default 15 минут / 30 дней. Migration c3882e989a1e отзывает legacy refresh,
удаляет raw column; downgrade оставляет неработающие placeholders.
README описывает принудительный re-login и риск гонок вкладок; cookie bridge T14.

Проверки:
- Auth/users после upgrade: 73 passed, 15.90s.
- T04/migrations первоначально: 17 passed, 11.06s.
- Итоговый полный `MODE=TEST .venv/bin/python -m pytest -q --tb=short`:
  **197 passed, 49.82s**, 0 failed/0 skipped; +16 T04 regressions.
- Независимые AsyncSession одновременно: ровно один успех, потомок отозван
  при replay; injection между revoke/insert сохраняет старый token.
- Password rollback/reset, чужой logout/пользователь B и legacy ver проверены.
- Первый auth прогон до upgrade упал на missing auth_version; после upgrade
  исправлено. Sandbox loopback denial обходился разрешённым локальным доступом.

UI/E2E/dev backend не запускались, внешняя БД не затронута.
Ручная проверка владельцем сейчас не требуется, API покрыт автоматическими тестами.
Новых commit/push/merge/deploy нет; изменения T02/T03 и исходные документы сохранены.
Следующее T05: admin/teacher_students/bootstrap по отдельному поручению.

Финально: migration suite 3 passed, 5.08s; `MODE=TEST .venv/bin/alembic upgrade head`
и `MODE=TEST .venv/bin/alembic check` PASS, «No new upgrade operations detected».
Оставлена пустая synthetic lgg-test схема на head c3882e989a1e. `git diff --check` PASS.


## Выполнение T05 — 15.10.2026

T05 DONE локально на `codex/t00-t01-environment`, HEAD `662a992`.
ADMIN и teacher_students с unique pair/started_at/ended_at; teacher создаёт только
student+связь атомарно, admin создаёт teacher/student и назначает существующего
student преподавателю. Оба legacy master endpoints требуют bearer ADMIN;
HTTP admin creation запрещено. is_active — admin only, аккаунт admin закрыт
от teacher mutations. Первый admin — интерактивный CLI, idempotent отказ
повтора, advisory lock защищает параллельный bootstrap. Дубликат аккаунта — 409.

Migration d897e9b55d47: транзакционное обновление PostgreSQL role enum,
backfill только из действующих курсов/зачислений; архивные-only пары в отчёт,
связь не выводится из наличия пользователей. Downgrade при наличии admin
отклоняется до DDL без удаления/понижения аккаунта. Детали: tasks/T05.md.

Проверки guarded lgg-test (healthy, loopback 55432):
- Полный `MODE=TEST .venv/bin/python -m pytest -q --tb=short`: **216 passed**, 60.34s,
  0 failed/0 skipped; +17 T05 role/CLI/rollback/concurrency tests, +2 migration tests.
- Clean/prior-state/round-trip/enum/schema, archived-only backfill и отказ
  downgrade с admin проходят в полном наборе. Второй teacher для общего student,
  concurrent unique assignment, восстановление связи, missing profile,
  teacher→admin/teacher запреты и оба master aliases проверены.
- CLI интерактивный путь, hash/active и concurrent/repeated bootstrap проверены
  на PostgreSQL; failure injection связи откатывает весь новый аккаунт.
- Первые прогоны выявили устаревшие expectations, отсутствующий 409 handler и
  ошибку synthetic SQL подготовки; исправлены до зелёного финального прогона.

Ручная проверка владельцем сейчас не требуется: UI не добавлен, API/CLI покрыты
автоматически. Полная матрица объектов/списки/файлы — T06, invite/reset — T05b.
Dev backend/UI/E2E/deploy не запускались; внешняя БД не затронута.
Новых commit/push/merge/deploy нет; исходные изменения T02–T04 сохранены.
Следующее T05b: сначала D01, затем one-time invite/reset по отдельному поручению.

Финальная сверка: `MODE=TEST .venv/bin/python -m pytest tests/migrations -q --tb=short`:
**5 passed**, 7.37s. `MODE=TEST .venv/bin/alembic upgrade head` и
`MODE=TEST .venv/bin/alembic check`: PASS, «No new upgrade operations detected».
Оставлена пустая synthetic схема lgg-test на head `d897e9b55d47`, контейнер работает.
`git diff --check`: PASS.

## 15.10.2026 — согласование D01

Владелец принял D01 для MVP; более удобная выдача доступа отложена. Контракт
зафиксирован в DECISIONS/PRODUCT, подготовлена tasks/T05b.md, обновлены TASKS,
STATUS/GPT. T05b TODO, реализация не поручена. Код/БД не менялись, тесты не
запускались. Проверка документации: git diff --check. Ручная проверка сейчас
не требуется: нового исполнимого сценария нет. Ветка codex/t00-t01-environment,
HEAD 662a992; новых commit/push/merge/deploy нет.
Следующее — локальная реализация T05b по отдельному поручению.

## Результат — 15.10.2026

T05b DONE локально по поручению владельца. Ветка `codex/t00-t01-environment`,
HEAD `662a992`; новые commit/push/merge/deploy не выполнялись, draft PR #1
не обновлялся. Исходные изменения T02–T05 и посторонние документы сохранены.

Реализованы приглашения 72 часа/reset 1 час, username-only login, nullable email
(включая удаление email из своего профиля), отдельный is_activated. Все registration
aliases создают ожидающий активации аккаунт и возвращают ссылку, а не задают
переданный teacher пароль. Старый password input вне схемы и игнорируется.
Teacher перевыдаёт только invite своему pending student; reset активированного
аккаунта — admin. Все password aliases self-only с current_password; self-change
отменяет ожидающий reset. Активация/reset не снимают is_active=false.

Новый модуль account_invitations: модели/DTO/repository/service/DI/router,
DB rate limits и audit actor/target/action/result/time/correlation без секретов.
Digest at rest; User → token locks, одна транзакция и rollback. Выдача ссылки,
создание user/profile/teacher link и audit атомарны. Consume не принимает target ID:
аккаунт определяется сохранённым токеном, назначение проверяется отдельно.

Миграция `711e94443ef3` сгенерирована Alembic autogenerate на lgg-test и дополнена
проверкой legacy username/email cross-collisions (только число в warning),
сохранением email/старых активированных аккаунтов и отказом downgrade до DDL
при nullable email/pending users. Никаких фиктивных email/автоактивации для отката.

Проверки:
- `MODE=TEST .venv/bin/python -m pytest tests/modules/auth tests/modules/users -q --tb=short`:
  **123 passed**, 38.82s (до последних четырёх дополнительных regressions).
- Финальный `MODE=TEST .venv/bin/python -m pytest -q --tb=short`:
  **240 passed**, 74.79s, 0 failed/0 skipped; +24 проверки к baseline T05.
- Финальный `MODE=TEST .venv/bin/python -m pytest tests/migrations -q --tb=short`:
  **8 passed**, 11.94s. Clean/prior-state/round-trip, schema/enum checks,
  сохранение email, collision warning, отказ небезопасного downgrade проходят.
- `MODE=TEST .venv/bin/alembic upgrade head` и `MODE=TEST .venv/bin/alembic check`:
  PASS, «No new upgrade operations detected».
- AST: 216 Python files PASS; `git diff --check` PASS.
- Конкурентное потребление в двух независимых AsyncSession: один успех;
  failure injection оставляет ссылку пригодной. Проверены expiry/replay/reissue,
  wrong purpose, disabled account, teacher boundaries, admin reset/сессии другого
  пользователя, current password, SQL rate counters и IP с разными token IDs.

Первые прогоны: 19 failed/197 passed из-за старых expectations и обязательного
current_password, затем 1 failed/235 passed — старое ожидание номера revision
после транзакционного отказа downgrade. Исправлено; финальный полный прогон зелёный.
Sandbox запрещал loopback/Docker socket; проверки выполнены с разрешённым локальным
доступом к guarded lgg-test, внешняя БД не затронута.

Оставлена пустая synthetic схема из 16 доменных таблиц на head `711e94443ef3`;
lgg-test-postgres-1 healthy, 127.0.0.1:55432. Dev backend build/start, UI/browser/E2E,
SMTP и deploy не выполнялись. Ссылки относительные с fragment; frontend-страницы
активации/reset ещё отсутствуют (T14). Rate limit — fixed window 15 минут,
10/identifier и 100/direct IP; возможен burst на границе окна, forwarded headers
не доверяются; proxy-настройка перед T17. Полная матрица профилей/списков/файлов — T06.

Ручная проверка владельцем сейчас не требуется: API сценарии покрыты автоматикой,
пользовательская форма ещё отсутствует. Следующее — T06 по отдельному поручению;
начать с endpoint → policy таблицы и принятого D01, без повторного согласования.


## Выполнение T06 — 15.10.2026

T06 DONE локально на `codex/t00-t01-environment`, HEAD `662a992`.
Таблица endpoint → policy составлена до правок: [карточка T06](tasks/T06.md).
Общие permission repository/service и SQL scopes закрывают чужие курсы, занятия,
персональные материалы/ответы/файлы. Admin читает учебные данные без teacher workflow.
Списки и total ограничены до pagination; missing profile не превращается в all rows.
D01: минимальная карточка связанного student, без контактов/отчества; общий профиль
и avatar меняют self/admin. role/is_active запрещены в обычной DTO; отдельный admin
account-status отзывает refresh/auth_version, пишет audit. Nested enrollment student
минимален; student_user_id вместо student_id. Avatar JSON содержит auth URL;
GET/download и legacy avatar alias проверяют права. Teacher hard delete закрыт до T07.

Проверки guarded lgg-test (healthy, 127.0.0.1:55432):
- `MODE=TEST .venv/bin/python -m pytest -q --tb=short`: **263 passed**, 102.33s,
  0 failed/0 skipped; +23 T06 regressions к 240 T05b.
- `MODE=TEST .venv/bin/python -m pytest tests/migrations -q --tb=short`:
  **8 passed**, 12.47s.
- `MODE=TEST .venv/bin/alembic upgrade head` и `MODE=TEST .venv/bin/alembic check`:
  PASS, «No new upgrade operations detected». Нового DDL нет.
- AST: 219 Python files PASS; `git diff --check`: PASS.
- Два teacher/общий student/другой student/admin, прямые/подменённые IDs,
  pagination/filter/count, missing teacher/student profile, same-lesson recipient,
  profile privacy, avatar/download/upload/write boundaries, audit и active revocation.
Промежуточные failures и исправление SQL auto-correlation описаны в карточке;
финальный полный прогон зелёный. Sandbox Docker socket требовал локальной эскалации;
доступ к подтверждённой guarded lgg-test разрешён. Внешняя БД не затронута.

Оставлена пустая synthetic схема на head `711e94443ef3`; контейнер работает.
Dev backend startup/UI/browser/E2E не выполнялись. Ручная проверка владельцем сейчас
не требуется: API покрыт автоматикой, frontend отсутствует. Archive/read-only/cutoff,
expiry history и безопасный admin purge — T07 после D02; submission lifecycle — T09/T10,
storage rollback/retry — T12/T07. Эти этапы не объявлены готовыми.
Новых commit/push/merge/deploy нет, draft PR #1 не обновлялся; исходные изменения
T02–T05b и посторонние документы сохранены. Следующее — T07 по отдельному поручению,
начать с D02 без повторного согласования D01.


## Выполнение T07 — 15.10.2026

T07 DONE локально по явному поручению, D02 принят. [Карточка и проверки](tasks/T07.md).
Lesson archive/DTO, Course idempotent archive со стабильным slug, read-only по
предкам/участию; unlink LessonStudent сохраняет историю. Cutoff включителен по
created_at grant/material/submission/file; SQL scopes до count/pagination,
my-materials/nested files/direct IDs, gaps после re-enroll/teacher relink.
Admin restore не оживляет отдельные архивы/зачисления; явный history-access + audit.
Admin purge подтверждает ID+имя, атомарно удаляет цепочку и сохраняет durable queue;
после commit безопасный unlink, shared refs/PathsConfig/retry/restart, без rmtree.

Миграция 811d7911d0b4: autogenerate + legacy cutoff backfill, pre-DDL refusal
для duplicates/dangling grants, protection от потери новых архивов/истории при downgrade.
Полный `MODE=TEST .venv/bin/python -m pytest -q --tb=short`: **290 passed**,
128.63s, 0 failed/0 skipped. Финальные migrations: **11 passed**, 17.11s;
upgrade head/check PASS, schema diff пустой. AST 230 файлов, OpenAPI и diff check PASS.
Промежуточные failures и исправления записаны в карточке T07.

Оставлена пустая synthetic lgg-test: 19 доменных таблиц, 0 строк, head 811d7911d0b4.
Внешняя БД и рабочее media не затронуты. Worker запускается после purge и через
admin retry; scheduler не подключён. Активный submission lifecycle/file swap —
T09/T12, восстановление backup с deletion ledger — T18.
Dev build/start, UI/browser/E2E не запускались; ручная проверка владельцем сейчас
не требуется: API покрыт автоматически, frontend отсутствует.
Ветка codex/t00-t01-environment, HEAD 662a992; commit/push/merge/deploy не выполнялись,
draft PR #1 не обновлялся; предыдущие изменения и посторонние документы сохранены.
Следующее — T08 по отдельному поручению, сначала согласовать D03.


## 15.10.2026 — согласование D03

D03 принят ответом «D03 принимаю», контракт зафиксирован в DECISIONS/PRODUCT/A05
и карточке T08. Подготовка завершена, T08 TODO; далее локальная реализация по
отдельному поручению. Код/БД не менялись, тесты не запускались; diff check PASS.
Ветка codex/t00-t01-environment, HEAD 662a992; новых commit/push/merge/deploy нет.


## 15.10.2026 — повторная приёмка T00–T07 перед T08

[Полный отчёт, команды, неуспешные промежуточные проверки и ограничения](T00_T07_ACCEPTANCE.md).
Новый отдельный lgg-dev (DB 55431, HTTP 8018) поднят из Docker build на synthetic
данных; миграции от пустой схемы PASS. Исправлены 500 при стандартной обложке
через PATCH и отсутствие deleted_at при PATCH-архивировании; добавлены 2 regressions.
Финальный pytest: **292 passed, 142.58s**, guard unit **14 passed**, T07 targeted
**26 passed**. Итоговый HTTP **68 запросов PASS**, restart persistence **3 PASS**
(login, курс, идентичный PDF); Swagger/OpenAPI 200. Dev alembic check PASS.
Файлы dev — persistent lgg-dev_media, неизвестная БД не затронута. Purge только
своей новой synthetic цепочки; failed cleanup=0, второй курс/файл сохранены.
Тестовый lgg-test остаётся отдельным; финальное migration состояние — в отчёте.

Dev оставлен работающим: http://127.0.0.1:8018/docs. Учётные данные только
локально в ignored .env.audit-access (0600), не в отчёте/чате/Git. Необязательные
ручные шаги приведены в отчёте; обязательной ручной приёмки для этого этапа нет.
UI отсутствует; production, нагрузка и backup restore не проверялись.
Ветка codex/t00-t01-environment, HEAD 662a992; commit/push/merge/deploy нет.
Следующее: T08, D03 уже принят; реализация не начата.

Финальный повтор migrations: **11 passed, 16.82s**; guarded lgg-test upgrade/check
PASS, head 811d7911d0b4, users=0/courses=0. Dev synthetic данные сохранены.


## Выполнение T08 — 15.10.2026

T08 DONE локально по поручению владельца, D03 принят. [Карточка/контракт/проверки](tasks/T08.md).
POST /lessons атомарно создаёт Lesson+LessonStudent; 0/1/multiple, действующее
участие/связь/active, public user_id, rollback и независимые concurrent sessions
проверены. Default 55, aware UTC, scheduled/completed/cancelled, перенос одного,
status filter до count/pagination. Cancellation сохраняет историю, архив read-only
и admin restore не подменяются status. Course URL/lesson override/effective URL,
очистка, динамический fallback и HTTP(S) allowlist; backend внешнюю ссылку не скачивает.
Пересечения teacher — предупреждение с сохранением, границы/self/archive/cancelled
исключены, completed учитывается; conflict IDs не выдаются ученику в detail/list.

Migration 29e67248e0f3 — autogenerate + NULL duration→55, invalid legacy guard,
enum/check, запрет потери non-default statuses/links при downgrade. Полный pytest:
**333 passed**, 183.66s, 0 failed/0 skipped; migrations **18 passed**, 32.50s;
guard unit **14 passed**, 0.41s; AST 235 Python files, diff check PASS.
Первый полный прогон 7 failed/326 passed: исправлены новые synthetic migration
fixtures, контракт/проверяемые требования не ослаблялись. Два rollback injection
и concurrent create с независимыми sessions зелёные.

Dev Docker build/upgrade/перезапуск PASS; 68 T00–T07 HTTP + **39 T08 HTTP PASS**,
restart persistence 3 прежних + 4 T08 HTTP PASS; Swagger/OpenAPI 200/default55.
Dev alembic check PASS, старые synthetic DB/media сохранены. Оба DB targets
остаются изолированными; неизвестная БД не затронута.
Dev http://127.0.0.1:8018/docs оставлен работающим. Учётные данные/ID synthetic
сценария только в ignored .env.audit-access (0600). Ручное знакомство — в карточке;
обязательной ручной приёмки backend нет. Frontend/browser UI не реализованы.

Ветка codex/t00-t01-environment, HEAD 662a992; commit/push/merge/deploy нет,
draft PR #1 не обновлялся. T08b optional не делался, T09/T11 не подменялись.
Следующее T09 — lifecycle ответа по отдельному поручению; D03 не повторять.

Финально после pytest: migration suite **18 passed, 33.47s**, upgrade/check PASS.
Lgg-test head 29e67248e0f3, users/courses=0; dev данные сохранены на том же head.
Новых Git операций нет; HEAD 662a992, git diff --check PASS.


## Выполнение T09 — 15.10.2026

T09 DONE локально по поручению владельца. [Карточка/контракт/все проверки](tasks/T09.md).
Один рабочий ответ с DB partial unique, latest legacy attempt и историей без потери
данных. Draft submitted_at=null, явный непустой/idempotent submit, поздняя отправка,
version; append сохраняет ID/байты, point delete/swap атомарны с durable cleanup.
Checked/history immutable, teacher обход закрыт. Parent→Homework→submission locks
сериализуют concurrent create/edit/submit; rollback не удаляет прежние файлы.
Re-enroll/file scopes сохранены и в mutation responses, скрытая история не удаляется.

Полный pytest **361 passed**, 223.32s. После финальной узкой правки scopes:
T09 **27 passed**, 28.81s (включая новый regression; полный после неё не повторялся).
Migrations **20 passed**, guard unit **14 passed**, AST 239, OpenAPI/diff check PASS.
Migration `8a575436b7db`: autogenerate/backfill/unique/check/unsafe downgrade refusal.
Dev build/upgrade/start и **28 HTTP + concurrent create pair PASS**, повтор на
окончательном build PASS; restart persistence login/answer/version/PDF/OpenAPI PASS.
Dev schema diff пустой; synthetic DB/media сохранены. Неизвестная БД не затронута.

Dev http://127.0.0.1:8018/docs работает; локальные synthetic credentials/ID только
ignored .env.audit-access (0600). Обязательной ручной приёмки backend нет;
необязательное знакомство в карточке. UI/E2E/production/backup не проверялись.
Cleanup scheduler/orphan reconciliation — T12; очередь проверки/mandatory expected
version для teacher/оценка D05 — T10. Новых commit/push/merge/deploy нет,
ветка codex/t00-t01-environment, HEAD 662a992; PR #1 не обновлялся.
Следующее T10: сначала D05, затем локальная реализация по отдельному поручению.

Финально T09: migrations **20 passed**, 39.57s, upgrade/check PASS; оставлена
чистая lgg-test на `8a575436b7db`, dev synthetic данные сохранены. AST 239,
OpenAPI/diff check PASS. Обязательных действий владельца сейчас нет.


## Сохранение T02–T09 в Git — 15.10.2026

По явному поручению владельца код, миграции, тесты, инструкции запуска и отчёты
T02–T09 сохранены одним локальным коммитом на codex/t00-t01-environment.
Эта запись входит в тот же коммит (SHA — `git log -1`). Push/merge/deploy не
выполнялись, draft PR #1 не обновлялся. Посторонние документы и прежние правки
rules_project.md оставлены вне коммита. Проверки кода не повторялись: изменений
реализации после результатов T09 нет; staged diff/состав/проверка секретов выполнены.
Следующее: T10, сначала D05 по отдельному поручению. От владельца сейчас ничего.


## Выполнение T10 — 15.10.2026

T10 DONE локально по поручению владельца, D05 принят ответом «подтверждаю».
[Контракт, результаты, ограничения и необязательные Swagger шаги](tasks/T10.md).
Teacher review требует strict integer grade 0–5 и expected_version; stale version
409, draft 409, checked/history 403. Общие parent→homework→submission locks
защищают от concurrent edit/check и check/check, проверено в независимых sessions.
checked_at UTC, внутренний checked_by teacher FK, публичный checked_by user_id.
Queue только своих submitted working answers активных курсов/уроков/участий,
course/student filters, SQL count/page в одном snapshot, стабильный порядок,
текущие version/text/files/context. Итог student доступен в прежних list/detail.
Numeric history сохранена без округления; нового DDL нет, новые review — integer.

Финальный полный pytest **395 passed**, 254.54s, 0 failed/0 skipped;
33 T10 tests включены. Migrations **20 passed**, 36.99s; guard **14 passed**,
0.37s; AST 242/OpenAPI/diff check PASS. Guarded test upgrade head/check PASS,
оставлена чистая test schema на 8a575436b7db. Промежуточные failures/исправления
записаны в карточке; контракт не ослаблялся.
Dev build/start, **29 HTTP PASS**, restart persistence **8 HTTP PASS**;
повтор 8 retained checks на окончательном image PASS. Dev schema diff пустой,
synthetic данные и persistent lgg-dev_media сохранены. Dev 127.0.0.1:8018/docs
работает; credentials/IDs только ignored .env.audit-access (0600).
Неизвестная БД не затронута. Ручная приёмка backend не обязательна; frontend/UI/E2E,
production/load/backup не проверялись. Notifications/deadline/debt не входят в T10.
Ветка codex/t00-t01-environment, HEAD 2dfd49c; новых commit/push/merge/deploy нет,
PR #1 не обновлялся. Посторонние документы и rules_project.md сохранены.
Следующее — T11 по отдельному поручению; сначала согласовать D04 на примере долга.


## Выполнение T11 — 15.10.2026

T11 DONE локально по поручению владельца, D04 принят ответом «подтверждаю».
[Контракт, миграция, промежуточные исправления, проверки и Swagger шаги](tasks/T11.md).
Placements original/debt с unique, один ответ/очередь без копирования; следующий
допустимый урок того же курса/ученика, стабильный scheduled_at/id, nullable срок.
Расписание/архив/restore и восстановление участия/teacher link пересчитывают срок
в бизнес-транзакции. Append-only deadline journal, SQL cutoff/gaps, последняя
видимая placement в /my, placement данного урока в detail/list, прямой file access
через долг с обеими проверками. Checked замораживает историю; parent delete bypass
закрыт. Course lock сериализует move-vs-check и concurrent identical debt.

Migration 689ceabc2b0c: autogenerate/backfill, старые ручные сроки в legacy_import;
checked/read-only импорт сохраняется, active unchecked рассчитывается; безопасный
round-trip pristine backfill, отказ потери новых placements/events. Полный pytest
**421 passed**, 300.41s; после callbacks возврата доступа — финальные scoped
**95 passed**, 87.84s, включая все 25 T11 tests (полный после этих callbacks не повторён).
Migrations **23 passed**, guard **14 passed**; AST 253/diff check PASS.
Test upgrade/check PASS; чистая lgg-test на head 689ceabc2b0c.

Окончательный dev build/up/healthy, **29 T11 HTTP PASS**, после restart **7 T11 +
8 T10 HTTP PASS**, прежний PDF и данные сохранены; dev schema diff пустой.
Проверка импортированной закрытой истории dev: 0 расхождений со старым сроком.
Dev 127.0.0.1:8018/docs работает, credentials/IDs только ignored .env.audit-access.
Неизвестная БД и реальные ПД не затронуты. UI/E2E/production/load/backup не проверялись.
Обязательной ручной приёмки backend нет; необязательный Swagger сценарий — в карточке.

Ветка codex/t00-t01-environment, HEAD 2dfd49c; новых commit/push/merge/deploy нет,
PR #1 не обновлялся. Прежние T10 правки и посторонние документы сохранены.
Следующее — T12a (storage adapter/защита), локально по отдельному поручению;
D06 перед нормализацией/удалением оригиналов фото. От владельца сейчас ничего.


## Выполнение T12 — 15.10.2026

T12a/b/c DONE локально по поручению владельца; [карточка, контракт, все проверки](tasks/T12.md).
D06 принят вариантом 1, затем владелец подтвердил читаемость synthetic сравнений.
WebP ≤2560/q85 без EXIF/GPS, white alpha/orientation/sRGB; PDF без растеризации и
дубликата. Исходник нового фото удаляется через durable queue после ready/link commit;
старые фото массово не нормализуются. Никакие реальные ПД не использовались.

Storage protocol/local/read-only legacy, UUID immutable keys, descriptor-safe paths,
FileAsset с explicit FK; pending/failed закрыты. Private/nosniff/Range auth сохраняет
T06/T07/T11 scopes. Stream 20MiB, answer 10/100MiB, 50MP/single frame и 30s bounded
worker; multipart guard 102MiB до полного FastAPI spool. Общая student quota 1GiB,
admin override/audit/report/warnings, cross-course concurrency. Rollback/commit-ack
ambiguity защищают committed refs, а orphan/retry покрывает crash window.

Миграции 4ffe7beb42f4 / 5c844cca1bd6 / 36a8711f7799: autogenerate, legacy unchanged,
source usage и safe downgrade guards. Полный pytest **478 passed**; после последних
long-name/unknown-COMMIT fixes финальные scoped **82 passed** (полный не повторён).
Migrations **27 passed**, tests_unit **38 passed**, AST **285**, diff check PASS.
Test upgrade/check PASS, оставляется пустая schema на 36a8711f7799.

Финальный dev build/up/healthy PASS, **33 HTTP PASS** (включая HEIC, 48.77MP,
20MiB boundary, quota и Range). Restart T12 6 + T10 8 + T11 7 + старый PDF SHA256 3 PASS;
T12 6 повторён на окончательном image. Dev schema diff пустой. Legacy 5/5 copied/hash
verified, 0 failed/remaining, legacy reads отключены; 7-day source copies/manifests
сохранены. Runtime post-commit cleanup 4 объектов PASS, 32 assets, pending cleanup=0.
Dev volume lgg-dev_media и DB сохранены; MODE=DEV теперь явный в Compose.
Dev http://127.0.0.1:8018/docs работает; credentials/IDs только ignored .env.audit-access.

Обязательных ручных действий сейчас нет. Synthetic D06 чтение принято; конкретные
устройства и реальные фото не заявляются проверенными. UI/E2E/production/load/
malware scan/backup restore не проверены, идут дальнейшими этапами.
Ветка codex/t00-t01-environment, HEAD 2dfd49c; новых commit/push/merge/deploy нет,
PR #1 не обновлён, посторонние документы и прежние правки rules_project.md сохранены.
Следующее — T13 по отдельному поручению. Перед ним разумно отдельно сохранить T10–T12
локальным коммитом; D06 повторно не спрашивать.

Финальный preflight: guarded lgg-test head 36a8711f7799, users/courses/assets = 0/0/0;
both Compose config --quiet и git diff --check PASS. Dev сохранён работающим.
