# Краткий журнал сессий

Новые записи сверху; подробные тесты в карточке/TEST_BASELINE, не копировать сюда всё. Журнал не заменяет STATUS.

## 2026-10-15 — ручная приёмка и своевременные решения владельца

AGENTS/GPT/WORKFLOW/PROMPTS обновлены: агент сам зовёт на полезный ручной тест, даёт проверенный запуск/шаги/результат, отдельно отмечает ожидающую приёмку; настройки сервера/хранилища спрашивает только перед зависимым шагом, предлагает подходящий вариант и объясняет компромиссы. Фактическое локальное хранение объясняется по конфигурации. Изменены только инструкции; статусы реализации и существующие изменения другой сессии сохранены. Проверка: git diff --check и целостность локальных Markdown-ссылок.

## 2026-10-15 — T01 выполнена после установки Docker

- Docker Desktop запущен, Engine 29.8.2 / Compose 5.6.0. Только lgg-test PostgreSQL на loopback 55432 создана и оставлена healthy; роль ограничена, public tables=0.
- Guard/env/media/engine lifecycle/fixtures/tools/compose/examples/README реализованы. Секреты в ignored локальных env, не опубликованы.
- 14 unit passed, 141 collected; compose dev/test config PASS, read-only role/connection smoke PASS, diff check PASS. Полный DB pytest/Alembic/dev build NOT RUN.
- Init shell mount получил Permission denied; заменён на SQL. Пересоздан только новый пустой test volume этой сессии.
- T01 DONE; следующая T02 по отдельному поручению. Внешняя БД UNKNOWN, не тронута. dev 71fdcfa; commit/push/PR/deploy отсутствуют.

## 2026-10-15 — T00, локальный старт

- Владелец разрешил T00 и T01 при доступном окружении; без commit/push/deploy.
- T00 DONE как инвентаризация, создан ENVIRONMENT.md с отдельными dev/test DB/roles/volumes/media. Внешняя БД UNKNOWN.
- dev 71fdcfa; Python 3.14.0, зависимости найдены; Docker/psql/pg_isready отсутствуют. Origin DNS недоступен, bind порта запрещён sandbox.
- T01 BLOCKED (ENV_BLOCKED), код не менялся; DB fixtures, pytest, миграции и Docker не запускались. Следующее: Docker Desktop + Compose v2, затем T01.
- Исходные рабочие файлы сохранены. Commit/PR/deploy отсутствуют.

## 2026-10-15 — исследование и планирование

- Основа dev 71fdcfa; удалённые main/dev совпали. Код не менялся; commit/PR/deploy отсутствуют.
- Получены уточнения: 6 преподавателей/50–60 учеников, PDF 2–3 МБ, фото телефона; разрешение автора кода подтверждено. Внешняя БД неизвестна.
- Подготовлен docs/plan: требования, исследования/ПД, архитектура/решения, задачи T00–P03 и F01–F06, карточки T00–T04, files/release, workflow/prompts/skills/status.
- Проверки: AST всех Python main/dev без ошибок; функциональные тесты/миграции/Docker не запускались. Сеть GitHub проверена; РКН/publication недоступны инструменту, ограничения записаны.
- Контекст оптимизирован фактически: подробные требования перенесены из GPT в PRODUCT без отмены согласованного; GPT короткий, старый ASTRA_PROMPT перенаправляет к новым промптам, текущая задача отделена от backlog.
- Следующее: новый чат GPT-6.1 Sol, T00; затем T01 по готовности. D-вопросы не блокируют независимые начальные задачи.

Проверка пакета: локальные ссылки/ID и согласованность входов проверены, git diff --check без ошибок; tracked функциональные файлы совпадают с HEAD. Только Markdown-изменения, включая внешний AGENTS-указатель.

## 2026-10-15 — подсказки владельцу

По запросу владельца AGENTS/GPT/WORKFLOW/PROMPTS дополнены обязанностью агента самому сообщать необходимые ручные действия, подходящий момент GitHub/смены модели/нового чата и давать готовые промпты. Функциональный код и статусы T00/T01 не изменялись. Проверка: Markdown diff и git diff --check; runtime-тесты для этой правки документации не нужны.

Git handoff 15.10.2026: diff T00/T01 проверен; ветка `codex/t00-t01-environment`, origin/dev подтверждён 71fdcfa. Повторно 14 unit passed, 141 collected, diff check PASS. Исправлен multi-statement вызов в test drop_schema (две отдельные execute). Владелец разрешил commit/push/draft PR в dev; merge/deploy запрещены. Посторонние planning/design/instruction документы исключены из коммита.

Git result 15.10.2026: ветка `codex/t00-t01-environment`; implementation commit `8be580f` отправлен в origin. Draft PR в dev: https://github.com/KutuevTimur/API_online_school/pull/1 . Локальные секреты проверены сравнением с содержимым commit, не включены. Merge/deploy не выполнялись. Ручная проверка владельцем сейчас не требуется: пользовательский сценарий ещё не готов. Следующая задача T02 по отдельному поручению; этот PR остаётся draft.

## 2026-10-15 — T02, локальный миграционный baseline

Ветка codex/t00-t01-environment, исходный HEAD 662a992. Initial revision:
только исправление autcrement. Добавлена 56c4070bf9cd, guarded Alembic config,
main preflight refusal, 3 migration tests со snapshot всех 12 таблиц.
Metadata/enum schema matches ORM; clean/no-op/round-trip/prior-state PASS.
Существующий baseline 141 passed, финальный общий набор 144 passed (37.86s),
0 failed/skipped. Подробности TEST_BASELINE.md. T02 DONE, следующее T03.
Внешняя БД UNKNOWN и не затронута; новых commit/push/merge/deploy нет.
Ручная проверка владельцем пока не нужна, пользовательский сценарий не добавлен.


Финальное состояние lgg-test: после общего pytest повторно выполнены migration tests
(3 passed, 5.34s), затем MODE=TEST .venv/bin/alembic upgrade head и alembic check:
PASS, «No new upgrade operations detected». Оставлена пустая synthetic схема
из 12 доменных таблиц на head 56c4070bf9cd, контейнер работает.
git diff --check: PASS. Новых commit/push/merge/deploy нет.


## 2026-10-15 — T03, локальные public DTO/active/JWT

Ветка codex/t00-t01-environment, HEAD 662a992. Переиспользован UserResponse
на регистрации/смене пароля и aliases; внутренний UserDTO сохранён.
Единая active проверка login/access/refresh, generic 401 для auth failures,
строгие exp/sub и trusted algorithm. Добавлены 37 regressions, JSON/OpenAPI без hash.
Целевой набор 71 passed; финальный полный 181 passed (43.70s), 0 failed/skipped.
Sandbox socket отказ при первом запуске снят разрешённым локальным запуском.
После полного набора migration tests 3 passed (5.84s), upgrade head/check PASS.
Оставлена пустая lgg-test схема на 56c4070bf9cd, контейнер работает.
git diff --check PASS. Исходные изменения сохранены, Git/deploy не выполнялись.
T03 DONE; следующее T04 (rotation/revocation), P0 целиком ещё открыт.
Ручная проверка сейчас не требуется; детали/команды — STATUS и карточка T03.


### 15.10.2026 — T04 локально

На `codex/t00-t01-environment` (HEAD 662a992) реализованы digest/family refresh,
атомарная ротация с User → Token locks, строгий family replay, owned/idempotent
logout, password revoke + auth_version, конфигурация TTL и migration c3882e989a1e.
Полный итоговый pytest: 197 passed, 49.82s. Две AsyncSession/rollback/reset/изоляция
покрыты. Forced re-login и T14 single-flight/cookie граница описаны в README/T04.
Первый запуск без upgrade дал missing column; исправлено применением миграции.
Новых commit/push/merge/deploy нет; исходные T02/T03 изменения сохранены.
Ручная приёмка сейчас не нужна. Следующее T05 по отдельному поручению.
Финальные migration tests 3 passed; upgrade head/check PASS, schema diff пустой;
lgg-test оставлена пустой на c3882e989a1e. Diff check PASS.

## 15.10.2026 — T05 локальная реализация

Поручение владельца: T05 на codex/t00-t01-environment, lgg-test, без Git
публикации/deploy. Прочитаны AGENTS/GPT/STATUS/rules/PRODUCT/ARCHITECTURE и T05
backlog; создана отдельная карточка tasks/T05.md. Реализованы ADMIN,
teacher_students, атомарный teacher→student+link, admin assignment, bearer-only
legacy registration, первый admin CLI с advisory lock. Existing T02–T04 и
посторонние документы сохранены. Добавлены role/rollback/concurrency/CLI и
migration regressions. Итоговые команды и результаты будут зафиксированы в
карточке и STATUS после последней сверки. Приёмка UI не требуется.

Финал T05: **216 passed**, 60.34s, 0 failed/0 skipped. T05 DONE; details и
ошибки промежуточных прогонов записаны в tasks/T05.md и STATUS. Следующее T05b,
сначала D01. Git HEAD 662a992, ветка прежняя; commit/push/merge/deploy не выполнялись.

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

## 15.10.2026 — T05b локальная реализация по принятому D01

T05b DONE: одноразовые invite/reset, отдельный is_activated, username-only login,
nullable email, self-change с текущим паролем, отзыв сессий, SQL rate limits/audit.
Миграция 711e94443ef3 с сохранением email/legacy activation, collision warning и
отказом небезопасного downgrade. Полный pytest 240 passed (74.79s), финальные
migration tests 8 passed (11.94s), upgrade/check PASS, schema diff пустой,
AST 216 файлов и diff check PASS. Подробности/промежуточные failures — tasks/T05b.md.
Пустая synthetic lgg-test на head 711e94443ef3, контейнер healthy/55432.
UI/E2E/dev build не проверены; формы активации/reset остаются T14, object matrix T06.
Ручная проверка сейчас не нужна; внешняя БД не затронута. Ветка прежняя,
HEAD 662a992; новых commit/push/merge/deploy нет. Следующее T06 по отдельному
поручению, начать с endpoint → policy таблицы; D01 повторно не спрашивать.


## 15.10.2026 — T06 локально

По явному поручению владельца, с принятым D01. T06 DONE: endpoint→policy таблица,
общие SQL scopes + permission repository/service, изоляция list/detail/write/file,
minimal profiles, self/admin profile mutations, отдельный admin account-status +
audit/revocation, auth avatar GET и URL вместо disk path, student_user_id в enrollment,
проверка active teacher_students/StudentCourse при назначении. Teacher hard delete закрыт.
Полный pytest: 263 passed/102.33s; migrations: 8 passed/12.47s; upgrade head и alembic
check PASS (schema diff пустой), AST 219 Python files и git diff --check PASS.
Промежуточные failures (старые expectations, SQL correlation) исправлены, детали T06.md.
Непроверено: dev startup/UI/E2E. D02/archive/cutoff/purge остаются T07; lifecycle — T09/T10.
Ручная проверка владельцем сейчас не требуется, frontend отсутствует.
Ветка codex/t00-t01-environment, HEAD 662a992; commit/push/merge/deploy не выполнялись,
PR #1 не обновлялся, исходные изменения сохранены. Пустая synthetic lgg-test на
711e94443ef3, контейнер работает; внешняя БД не тронута. Дальше T07, сначала D02.


## 15.10.2026 — подготовка T07 и D02

По поручению владельца прочитаны входные инструкции и relevant требования,
проверены branch/status/diff. Создана tasks/T07.md: предложение D02, порядок
реализации и критерии приёмки. D02 не принят; T07 BLOCKED до ответа владельца.
Код/БД не менялись, тесты не запускались; ручного сценария пока нет.
Ветка codex/t00-t01-environment, HEAD 662a992; существующие изменения сохранены.
Commit/push/merge/deploy не выполнялись. Далее — решение D02, затем его фиксация.


## 15.10.2026 — D02 принят, подготовка T07 завершена

Владелец ответил «D02 принимаю». Контракт записан в DECISIONS/PRODUCT/A04,
обновлены карточка T07, STATUS и GPT. T07 TODO, зависимость D02 снята;
реализация по отдельному поручению. Код/БД не менялись, тесты не запускались.
Проверка документации: git diff --check PASS. Ручного сценария пока нет.
Ветка codex/t00-t01-environment, HEAD 662a992; существующие изменения сохранены.
Commit/push/merge/deploy не выполнялись. Далее — локальная реализация T07.


## 15.10.2026 — T07 локально DONE

По явному поручению после принятого D02 реализованы archive/read-only/cutoff,
gaps/re-enroll/teacher relink, admin restore/history-access/audit, безопасный
admin purge с транзакционной durable queue и retry после commit. Миграция
811d7911d0b4 autogenerate + backfill/refusal/downgrade guards. README/API runbook
и endpoint→policy/проверки в tasks/T07.md; STATUS/GPT обновлены.
Полный pytest **290 passed**, 128.63s; финальные migrations **11 passed**, 17.11s;
upgrade head/check PASS, schema diff пустой; AST 230 файлов/OpenAPI/diff check PASS.
Промежуточные failures (старые expectations, fixtures, synthetic timestamps)
исправлены и записаны в карточке. Пустая lgg-test: 19 domain tables, 0 rows,
head 811d7911d0b4. Внешняя БД/рабочее media не затронуты; тестовые файлы временные.
Dev start/build/UI/E2E не запускались, ручная проверка сейчас не требуется.
Scheduler для cleanup пока не подключён, admin retry доступен.
Ветка codex/t00-t01-environment, HEAD 662a992; новых commit/push/merge/deploy нет,
PR #1 не обновлялся, исходные изменения сохранены. Далее T08, сначала D03.


## 15.10.2026 — подготовка T08

Подготовлена tasks/T08.md: предложение D03, границы T08/T08b, план и приёмка.
D03 ожидает ответа владельца. Проверены инструкции, требования и branch/status/diff.
Код/БД не менялись, тесты не запускались, ручного сценария пока нет.
Ветка codex/t00-t01-environment, HEAD 662a992; прежние изменения сохранены.
Commit/push/merge/deploy не выполнялись. Следующее: согласовать D03.


## 15.10.2026 — D03 принят

Ответ владельца «D03 принимаю» зафиксирован в DECISIONS/PRODUCT/A05/T08/STATUS.
T08 подготовлен, реализация не начата; следующий шаг — отдельное локальное поручение.
Код/БД не менялись, тесты не запускались, diff check PASS; ручного сценария нет.
Ветка codex/t00-t01-environment, HEAD 662a992; commit/push/merge/deploy нет.


## 15.10.2026 — автоматическая и HTTP-приёмка T00–T07

Поднят отдельный Docker lgg-dev с новой пустой БД, миграции от clean PASS.
На synthetic данных пройдены 68 HTTP запросов account/auth/course/enrollment/
permissions/archive/restore/purge/files, ещё 3 после restart с SHA256 PDF.
Исправлены два воспроизведённых дефекта PATCH курса (standard avatar 500,
archive без deleted_at), добавлены regressions. Полный повтор pytest: 292 passed,
142.58s; guard unit 14 passed; targeted T07 26 passed. Dev schema diff пустой.
[Полный отчёт](T00_T07_ACCEPTANCE.md) фиксирует промежуточные failures/ограничения,
команды повторения и ручное знакомство со Swagger. Dev оставлен работающим,
учётные данные в ignored локальном файле; внешняя БД не затронута.
Ветка codex/t00-t01-environment, HEAD 662a992; commit/push/merge/deploy нет.
Следующее T08 по отдельному поручению, D03 принят; UI ещё отсутствует.

Финальный migration повтор после pytest: 11 passed, 16.82s; upgrade/check PASS,
lgg-test head 811d7911d0b4, users/courses=0. git diff --check PASS.


## 15.10.2026 — T08 DONE локально

Атомарный Lesson+LessonStudent с active participation/public user_id, default55/UTC,
manual status/move/cancel/complete, course call_url/lesson override и overlap warnings
реализованы по D03. Migration 29e67248e0f3 создана autogenerate на lgg-test,
дополнена backfill/guards и проверками enum/check/round-trip.
Полный pytest 333 passed, 183.66s; 18 migrations passed, 32.50s; guard14 passed;
68 прежних + 39 T08 реальных HTTP PASS; после restart 3+4 HTTP PASS, PDF SHA256
сохранён. Dev migration/check/build PASS, backend оставлен работающим.
Первый полный прогон: 7 failed/326 passed из-за новых migration seed fixtures,
исправлено. AST235/diff check PASS. [Полный handoff/ручные шаги](tasks/T08.md).
Неизвестная БД не затронута, dev/test synthetic targets раздельны; UI и T08b нет.
Ветка codex/t00-t01-environment, HEAD 662a992; commit/push/merge/deploy нет.
Следующее T09 по отдельному поручению, можно новый чат: «Реализуй T09 локально
по инструкциям и актуальным требованиям, без commit/push/deploy».

Финально после pytest: migration suite **18 passed, 33.47s**, upgrade/check PASS.
Lgg-test head 29e67248e0f3, users/courses=0; dev данные сохранены на том же head.
Новых Git операций нет; HEAD 662a992, git diff --check PASS.

## 15.10.2026 — T09 локально

Поручение: реализовать T09; отдельно подтверждены критерии append, immutable
checked, сохранение истории и concurrent create. Карточка tasks/T09.md создана
после первых структурных правок, до основной реализации service; критерии
и матрица проверок записаны до продолжения. Ветка codex/t00-t01-environment,
HEAD 662a992, новых commit/push/merge/deploy нет; PR #1 не обновлялся.

Выполнено: один is_working ответ на ДЗ, partial unique, version, draft timestamp,
непустой/idempotent submit, submitted edit, append без потери старых ID/байтов,
point file delete/swap, immutable checked/history. Parent/domain locks и rollback,
UUID storage names, durable FileDeletion при commit. Миграция 8a575436b7db:
autogenerate, latest legacy backfill с сохранением истории, unsafe downgrade guard.
Re-enroll file scopes сохранены в mutation responses; hidden history deletion 403.
T10 review version/queue/D05 и T12 storage contract не объявлены выполненными.

Проверено: полный pytest **361 passed**, 223.32s; после финальной узкой правки
scope/delete-history **27 T09 passed**, 28.81s (с новым regression, полный после
этой правки не повторялся). Migrations финально **20 passed**, 39.57s;
guard **14 passed**, 0.40s; AST 239/OpenAPI/diff check PASS; guarded lgg-test
upgrade/check PASS, schema diff пустой. Ошибки промежуточной подготовки fixtures
и их исправления перечислены в карточке, требования не ослаблялись.

Synthetic dev build/upgrade/start PASS без reset/удаления volumes. HTTP
**28 запросов + concurrent create pair 201/409 PASS**, повтор на окончательном
build PASS. Restart login/checked text+version/PDF bytes/OpenAPI PASS, dev
alembic check PASS. Старые synthetic DB/media сохранены, файлы lgg-dev_media;
credentials/IDs только ignored .env.audit-access (0600). Dev 127.0.0.1:8018/docs
работает. Чистая test schema на 8a575436b7db; неизвестная БД не затронута.
Sandbox socket/loopback требовали разрешённой локальной эскалации, auto-review
не отклонял действия. Посторонние документы и изменения T02–T08 сохранены.

Ручная приёмка backend не обязательна; необязательные Swagger шаги в карточке.
Frontend/UI/E2E, production/load/backup не проверялись. Orphan reconciliation
и scheduler — T12. Следующее: T10, сначала D05, по отдельному поручению.
От владельца сейчас ничего не требуется. Пора сохранить связный локальный
результат в Git по отдельному поручению; затем новый чат для T10.


## 15.10.2026 — локальный коммит T02–T09

Владелец поручил один коммит T02–T09 без push. Включены backend, миграции,
регрессионные и миграционные тесты, smoke tools, README и отчёты T02–T09.
Посторонние документы и исходные правки rules_project.md сохранены вне индекса.
Эта запись включена в создаваемый коммит; SHA доступен через git log -1.
Ветка codex/t00-t01-environment. Push/merge/deploy и изменение PR не выполнялись.
Проверки: staged diff --check, инвентаризация staged paths и скан на типовые
секреты/закрытые ключи; env/media/дампы не включены. Повтор pytest не нужен:
реализация после проверок T09 не менялась. Следующее T10, сначала D05;
рекомендуется новый чат. Обязательных действий владельца сейчас нет.


## 15.10.2026 — T10 локально

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


## 15.10.2026 — T11 локально, D04 принят

По поручению «Реализуй T11 локально; сначала согласуй D04» решение принято
ответом «подтверждаю». Реализованы original/debt placements, автоматический
следующий срок того же курса/ученика, журнал и freeze checked; один Homework/
ответ/очередь, прямой file access и history scopes для debts. Атомарный пересчёт
расписания/restore/возврата участия, исправлен MissingGreenlet updated_at при
restore внутри архивного курса. Migration 689ceabc2b0c сохраняет legacy manual
history и защищает downgrade. [Полный отчёт](tasks/T11.md).

Проверено: полный 421 passed; после callbacks re-enroll/relink scoped 95 passed
(25 T11 tests), migrations 23/guard 14/AST 253/diff check PASS; test upgrade/check
и чистая схема на head. Dev final build/up, 29 HTTP, restart retained 7 T11 + 8 T10
PASS, прежний PDF/данные/volume сохранены, schema diff пустой. UI/E2E/production/
load/backup не проверены, ручная приёмка backend не обязательна. Ветка
codex/t00-t01-environment, HEAD 2dfd49c, новых commit/push/merge/deploy нет, PR #1
не обновлялся; T10 и посторонние документы сохранены. Далее T12a по отдельному
поручению, D06 до нормализации фото. От владельца сейчас ничего.

## 15.10.2026 — T12a/b/c локально

Поручение: реализовать T12, начать T12a, D06 до нормализации. D06 принят вариантом 1;
после первоначального ожидания владелец подтвердил читаемость synthetic сравнений.
Согласование сохранено в DECISIONS; отдельные устройства/реальные фото не заявляются.

Выполнено: Storage/local/read-only legacy, descriptor-safe paths, UUID immutable
objects, FileAsset+explicit domain FK, private/Range/nosniff downloads, stream/count/
source byte/pixel/frame/timeout limits, pre-spool multipart cap. Student quota 1GiB,
owner/admin report и admin override/audit, cross-course lock. WebP ≤2560/q85,
orientation/alpha/sRGB и metadata stripping, source deletion post-ready/link commit.
Rollback защищён и при неизвестном исходе COMMIT: referenced committed bytes не
удаляются, при недоступной БД файлы остаются для reconciliation.
Legacy exact copy/hash + private 7-day manifest; expired duplicate cleanup сверяет
новые hash-копии, admin purge учитывает shared retained sources. 24h orphan grace,
durable queue, 60s DEV worker/restart. Фото старой истории не нормализовались.

Проверено: полный pytest 478 passed (343.65s); после последних long-name/COMMIT-ack
fixes профильный 181, финальный Files/T09/T07 82 passed (93.99s); полный после них
не повторялся. Migration suite 27 passed (62.73s), unit/guards 38 passed (0.96s),
AST 285 и diff check PASS. Три autogen revisions, final head 36a8711f7799;
test upgrade/check и dev schema diff пустые. Все промежуточные failures/исправления
и точный контракт — tasks/T12.md, без сокрытия ограничений.

Dev build/up/healthy, HTTP T12 33 PASS (включая bounded Linux 48.77MP, 20MiB boundary,
HEIC→WebP, Range/foreign file ID/quota). Restart T12 6/T10 8/T11 7/T00–T07 SHA256 3 PASS;
T12 6 повторён на окончательном image. Legacy 5/5 migrated, 0 failed/remaining,
reader off, manifests/старые bytes сохранены; dummy historical PDF импортированы
явным synthetic-only opaque режимом без изменения bytes. Runtime flags/cleanup PASS:
32 assets, 4 source/swap objects removed post-commit, pending cleanup 0.
MODE=DEV теперь явный в Compose; guard сопоставляет env и настоящий engine/session.

Не проверено: production/load/malware scan/backup restore, frontend/UI/E2E и реальные
фото/конкретные устройства. Обязательной ручной backend-приёмки нет; D06 synthetic
чтение принято. Dev DB/media и ignored credentials сохранены; test возвращается
на чистый head. Внешняя/неизвестная БД и реальные ПД не затронуты.

Git: codex/t00-t01-environment, HEAD 2dfd49c; новых commit/push/merge/deploy нет,
PR #1 не обновлён. Прежние T10/T11 и посторонние файлы/rules_project.md сохранены.
Следующее: отдельный локальный commit T10–T12 по поручению, затем T13 в новом чате.
Готовый промпт: «Реализуй T13 локально; T12 завершена, D06 принят. Начни с AGENTS,
GPT, STATUS и карточки задачи; commit/push/deploy не выполняй».

Финальный preflight: guarded lgg-test head 36a8711f7799, users/courses/assets = 0/0/0;
both Compose config --quiet и git diff --check PASS. Dev сохранён работающим.


## 15.10.2026 — локальное сохранение T10–T12

По явному поручению владельца T10–T12 сохраняются одним локальным коммитом
в codex/t00-t01-environment; SHA коммита с этой записью: `git log -1 --oneline`.
Включены код, миграции, проверки, README, окружение, STATUS и карточки T10–T12.
Прежние общие untracked документы планирования и правки rules_project.md
сохранены вне коммита, как при T02–T09; секреты и media не включены.
Проверки реализации приведены выше и в T12; при сохранении кода не меняли.
Push/merge/deploy не выполнялись. Далее T13 по отдельному локальному поручению.
