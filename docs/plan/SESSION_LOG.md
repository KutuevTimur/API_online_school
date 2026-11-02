# Краткий журнал сессий

26.10.2026 · по отдельному owner-запросу добавлено через API ДЗ58 для самостоятельной
отправки Артёмом31, последний completed урок29. Guard/прежние ДЗ/GET no-answer/
browser empty form+submit PASS; ответ не создавался. Без seed/reset/изменений кода.
Подробности — [S3](tasks/T15d.md#s3--урок-и-состояния-ответа-26102026).


26.10.2026 · T15d S3: локально student урок/условие/статусы/CTA/result focus,
без backend/API/UploadQueue/версий; S1/S2 сохранены. VERIFY, ручная приёмка ожидает.
PASS173unit/34files/types/lint/format/API/tokens/build/Impeccable0, Chrome1/36.4s
read-only + явные HTTP fixtures1340/768/360/Back/dirty/axe0/writes0; Premium2 old false positives.
Preview с прежним media восстановлен, SQL guard PASS; teacher browser отклонён auto-review,
real write/disposable/physical NOT RUN. [Доказательства и остаток S3](tasks/T15d.md#s3--урок-и-состояния-ответа-26102026). Commit/push/deploy/установок нет.

Новые записи сверху; подробные тесты в карточке/TEST_BASELINE, не копировать сюда всё. Журнал не заменяет STATUS.

## 2026-10-15 — независимая проверка после T13

- Проверены план/решения/карточки, критичные слои кода, все 305 Python AST, 54 OpenAPI paths/71 operation и локальные ссылки.
- Текущий полный guarded pytest: **508 passed, 369.76s** (440 functional/30 migrations/38 unit). Dev OpenAPI HTTP200, T13 routes есть. После временных probes disposable test DB возвращена clean Alembic head, check без diff.
- Дополнительные API probes подтвердили Q01 avatar filename traversal (удаление чужого synthetic avatar), Q03 DELETE ДЗ+draft → FK error и Q04 PATCH course name=null → NOT NULL error. Q02 потеря прежнего avatar при неуспешной замене подтверждена двумя unit-пробами. Эти failures не маскировались и код пока не исправлен.
- Отчёт CHECKUP_T13.md, следующая задача T13R, затем D07/T14. Исторические DONE не стерты; новые находки явно открыты. Полный исторический STATUS ещё требует сокращения без потери доказательств.
- Изменены только документы/инструкции. Dev данные/media и внешняя БД не тронуты, commit/push/deploy не выполнялись. Первичный sandbox-запуск без DB доступа остановлен; он не считается результатом продукта.

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


## Выполнение T13 — 15.10.2026

T13 DONE локально по поручению владельца; [контракт/проверки/Swagger шаги](tasks/T13.md).
Notification recipient scope без admin bypass; SQL page/count в одном snapshot,
unread и идемпотентный read_at. Assigned/submitted/checked/rescheduled/cancelled
в транзакции доменного действия, unique dedupe, submitted edit/retry без спама.
Parent locks + независимые sessions защищают повтор PATCH; event key использует
сохранённую версию изменения урока. Target повторно проверяет object/submission
scope; purge/закрытая история дают available=false с сообщением, запись читается.
Audit admin-only объединяет новые AuditEvent с прежними AccountAudit/LifecycleAudit,
filters/count/page/source+id. Account creation/teacher-student linking аудируются;
прежние reset/profile/status/quota/restore/history/purge records не переписаны.
Секретов/контактов/решений в payload нет; rollback проверен для учебных и admin действий.

Полный pytest **504 passed**, 388.50s; после финальных уточнений **42 scoped passed**,
30.39s, включая все 25 T13 tests. Полный после этих уточнений не повторялся.
Отдельные migrations: **30 passed in 66.10s (0:01:06)**; unit **38 passed**, AST **305**, diff check PASS.
Autogenerate migration `2048d2eeeaa8`: clean/prior-state/round-trip и refusal потери
новых records. Test upgrade/check PASS; чистая guarded lgg-test на этом head.
Промежуточные test fixture/collection исправления записаны в карточке.

Dev окончательный build/up/healthy; **27 HTTP PASS**, повтор на final image PASS;
restart **9 T13 + 8 T10 + 7 T11 + 6 T12 HTTP PASS**, T13 9 повторён после последнего
restart. Dev alembic check PASS; прежние synthetic DB/media/PDF сохранены.
Dev http://127.0.0.1:8018/docs работает. Credentials/IDs только ignored .env.audit-access.
Ни неизвестная БД, ни реальные ПД не затронуты. Frontend/polling/UI/E2E/production/
load/backup restore не проверялись. Обязательной ручной backend-приёмки нет.

Ветка codex/t00-t01-environment, HEAD f6d41fd; новых commit/push/merge/deploy нет,
PR #1 не обновлялся. Посторонние документы и прежние правки rules_project.md сохранены.
Следующее T14 по отдельному поручению, сначала D07. От владельца сейчас ничего.


## 15.10.2026 — T13R, Q01–Q04 локально исправлены

По явному поручению владельца, без commit/push/deploy и без перехода к T14.
Прочитаны AGENTS/GPT/STATUS/T13R/CHECKUP/rules и relevant PRODUCT/ARCHITECTURE.
Q01: имя клиента не участвует в ключах; private scratch, T12 no-follow storage и
bounded decoder, static WebP ≤512, bytes 10MiB/pixels50MP/frame1/timeout30s.
Upload JSON URL вместо raw bytes, GET private/no-store/nosniff.
Q02: immutable новый объект, row lock, pointer/audit/retire queue в одной транзакции;
commit/write/decode/cancellation rollback, uncertain COMMIT и cleanup retry защищены.
Q03: любая попытка/история → 409; concurrency test выявил stale parent после ожидания
course lock — повторная проверка lock_homework теперь даёт 404 вместо FK 500.
Q04: mandatory explicit null → 422, name/slug1–500; nullable clearing/duplicate slug сохранены.

Постоянные новые regressions: 36; прежние converter/users/courses/T11 tests обновлены.
До исправлений 15 failed/4 passed (20.89s); первый sandbox запуск упёрся в loopback,
повтор выполнен только на guarded lgg-test. Intermediate scoped выявили lazy profile,
symlink error code, checked DELETE expectation и concurrency stale parent; исправлены.
Полный `MODE=TEST .venv/bin/python -m pytest -q --tb=short`: **544 passed in 406.68s (0:06:46)**.
Финальный scoped auth/test_t13r + converter: **48 passed in 38.29s** после усиления
AccountAudit/GET bytes/сохранности Homework+answer+file+placement+event+queue assertions.
Implementation после full не менялся. Migration tests входят в full; затем guarded
`src.tools.drop_schema` → upgrade head/check PASS, schema diff отсутствует.
AST **307** и diff check PASS; отдельное чтение файлового diff выполнено.
Lgg-test оставлена пустой на head 2048d2eeeaa8. Dev DB/media/image и неизвестная БД
не тронуты; реальные ПД не использовались. UI/E2E/load/production не проверены.

Обновлены README/T13R/CHECKUP/STATUS/GPT/TASKS. T13R DONE локально;
ветка codex/t00-t01-environment, HEAD f6d41fd, PR #1 не обновлён.
Прежние изменения T13 и посторонние документы сохранены.
От владельца сейчас ничего; далее отдельное поручение сохранить T13/T13R.
T14 не начат. Чат продолжить здесь для Git-сохранения; функциональную T14 — только
после нового явного запроса (и D07), её промпт сейчас не выдаётся как начатая работа.


## Локальное сохранение T13/T13R — 15.10.2026

Владелец явно разрешил локальный commit T13 и T13R; push/merge/deploy и T14
не разрешены. Код после проверок не менялся: full 544 passed, final scoped 48 passed,
migration head/check, AST 307 и diff PASS. Повтор pytest для одного сохранения не нужен.
В commit входят implementation/migration/tests/smoke, README, карточки T13/T13R,
CHECKUP_T13, STATUS и SESSION_LOG. Общие untracked planning/design/instruction
документы и прежние rules_project.md оставлены вне commit; secrets/media исключены.
Ветка codex/t00-t01-environment; SHA этого commit — `git log -1 --oneline`.
PR #1 не обновляется. Следующий шаг — ждать поручения владельца; T14 не начат.


## Архив STATUS перед полным frontend-планированием, 15.10.2026

Исторический снимок перенесён дословно при Q06. Не текущие инструкции/статусы;
актуальное состояние только в STATUS. Старые NOT RUN и SHA относятся к своим сессиям.

<details>
<summary>Полный прежний STATUS (624 строки), доказательства сохранены</summary>

# Состояние разработки

Обновлено: 15.10.2026. **[T13R](tasks/T13R.md) DONE локально.** Q01–Q04 из [CHECKUP_T13](CHECKUP_T13.md) исправлены; добавлены 36 постоянных regressions. Полный pytest **544 passed in 406.68s (0:06:46)**; финальный scoped **48 passed in 38.29s**. Migration head/check, AST 307 и diff check PASS. T14 не начат. Владелец разрешил локальный commit T13/T13R; push/deploy запрещены.

 **T00–T13 DONE локально (включая T05b и T12a/b/c); T08b optional отложена.**
T00–T07 повторно проверены в отдельном dev по HTTP; исправлены два дефекта PATCH курса.
[Отчёт приёмки](T00_T07_ACCEPTANCE.md). T13 DONE локально: notifications/admin audit; T13R DONE локально; T14 пока не начинать. D01–D06 приняты 15.10.2026. Миграции проверены локально
на lgg-test, неизвестная БД не затронута. [TEST_BASELINE](TEST_BASELINE.md).

Ветка `codex/t00-t01-environment`; T02–T09 сохранены в `2dfd49c`.
T10–T12 сохранены локально в `f6d41fd`. T13/T13R сохраняются одним разрешённым локальным commit (SHA: `git log -1`).
Push/merge/deploy запрещены; T14 не начат.
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
| [T13](tasks/T13.md) | DONE локально | Notifications/unread/read/target, admin audit; full 504 + final scoped 42, migrations 30, unit 38; dev HTTP 27 + restart 9 |
| [T13R](tasks/T13R.md) | DONE локально | Q01–Q04 исправлены; +36 regressions, full 544 PASS, final scoped 48 PASS; migration/AST/diff PASS |
| T14 | TODO | После T13R: frontend/auth bridge/design |
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


## Выполнение T13 — 15.10.2026

T13 DONE локально по поручению владельца; [контракт/проверки/Swagger шаги](tasks/T13.md).
Notification recipient scope без admin bypass; SQL page/count в одном snapshot,
unread и идемпотентный read_at. Assigned/submitted/checked/rescheduled/cancelled
в транзакции доменного действия, unique dedupe, submitted edit/retry без спама.
Parent locks + независимые sessions защищают повтор PATCH; event key использует
сохранённую версию изменения урока. Target повторно проверяет object/submission
scope; purge/закрытая история дают available=false с сообщением, запись читается.
Audit admin-only объединяет новые AuditEvent с прежними AccountAudit/LifecycleAudit,
filters/count/page/source+id. Account creation/teacher-student linking аудируются;
прежние reset/profile/status/quota/restore/history/purge records не переписаны.
Секретов/контактов/решений в payload нет; rollback проверен для учебных и admin действий.

Полный pytest **504 passed**, 388.50s; после финальных уточнений **42 scoped passed**,
30.39s, включая все 25 T13 tests. Полный после этих уточнений не повторялся.
Отдельные migrations: **30 passed in 66.10s (0:01:06)**; unit **38 passed**, AST **305**, diff check PASS.
Autogenerate migration `2048d2eeeaa8`: clean/prior-state/round-trip и refusal потери
новых records. Test upgrade/check PASS; чистая guarded lgg-test на этом head.
Промежуточные test fixture/collection исправления записаны в карточке.

Dev окончательный build/up/healthy; **27 HTTP PASS**, повтор на final image PASS;
restart **9 T13 + 8 T10 + 7 T11 + 6 T12 HTTP PASS**, T13 9 повторён после последнего
restart. Dev alembic check PASS; прежние synthetic DB/media/PDF сохранены.
Dev http://127.0.0.1:8018/docs работает. Credentials/IDs только ignored .env.audit-access.
Ни неизвестная БД, ни реальные ПД не затронуты. Frontend/polling/UI/E2E/production/
load/backup restore не проверялись. Обязательной ручной backend-приёмки нет.

Ветка codex/t00-t01-environment, HEAD f6d41fd; новых commit/push/merge/deploy нет,
PR #1 не обновлялся. Посторонние документы и прежние правки rules_project.md сохранены.
Следующее T14 по отдельному поручению, сначала D07. От владельца сейчас ничего.


## Выполнение T13R — 15.10.2026

Q01–Q04 исправлены; [карточка с доказательствами](tasks/T13R.md).
Аватары: opaque UUID + bounded T12 decoder/static WebP ≤512,
безопасный GET/JSON upload URL; транзакционная ссылка/audit/cleanup, rollback/retry,
unknown COMMIT/cancellation. ДЗ с любыми ответами/историей → 409;
create после concurrent DELETE → 404 после проверки parent lock.
Course PATCH обязательные null → 422, name/slug 1–500, nullable clearing сохранён.

Полный pytest **544 passed in 406.68s (0:06:46)**; финальный scoped **48 passed in 38.29s**.
36 новых постоянных regressions; baseline 508 → 544. Migration upgrade/check,
AST 307/diff PASS. Пустая guarded lgg-test на head 2048d2eeeaa8.
Dev image/DB/media не обновлялись; UI/E2E/load/production не проверялись.
Ветка codex/t00-t01-environment, HEAD f6d41fd; commit/push/merge/deploy нет.
Ручная проверка владельца не требуется. Следующий разрешённый шаг — ожидать поручения
на сохранение T13/T13R; T14 не начинать. Чат можно продолжить здесь для сохранения.


## Локальное сохранение T13/T13R — 15.10.2026

Владелец явно разрешил локальный commit T13 и T13R; push/merge/deploy и T14
не разрешены. Код после проверок не менялся: full 544 passed, final scoped 48 passed,
migration head/check, AST 307 и diff PASS. Повтор pytest для одного сохранения не нужен.
В commit входят implementation/migration/tests/smoke, README, карточки T13/T13R,
CHECKUP_T13, STATUS и SESSION_LOG. Общие untracked planning/design/instruction
документы и прежние rules_project.md оставлены вне commit; secrets/media исключены.
Ветка codex/t00-t01-environment; SHA этого commit — `git log -1 --oneline`.
PR #1 не обновляется. Следующий шаг — ждать поручения владельца; T14 не начат.

</details>


## 2026-10-15 — весь frontend и путь до запуска: планирование завершено

- Scope: только исследование/документы/визуальные примеры; без functional code, commit/push/deploy/установки навыков. Ветка codex/t00-t01-environment, HEAD95b3560; прежний rules_project diff сохранён, GitHub refs не обновлялись.
- Владелец принял доработанную «Учебную ленту», голубой/мятно-зелёный, разную плотность, desktop/phone teacher и split проверку; потребовал интуитивность. PRODUCT §8/D07/DESIGN обновлены; принятый HTML reference сохранён в docs/plan/assets/lgg-approved.html (идентичен просмотренному).
- В существующие RESEARCH/ARCHITECTURE/TASKS внесены сравнение4stack, peer-совместимые exact versions, карта3ролей/A09–A13, покрытие API и точечные gaps. Добавлены16карточек T14(parent/a–f), T15a/b/c, T16–T18, P01–P03. Ни MASTER/FRONTEND_PLAN, ни дубль PRODUCT/UX-контракта не создавался; ближайшая исполнимая T14a, реализация ждёт нового поручения.
- Q06: STATUS624→58строк, прежний HEAD текст дословно перенесён в раздел архива этого журнала; GPT31/AGENTS67строк. Обновлены README/navigation/WORKFLOW/PROMPTS/SKILLS/ENVIRONMENT; старые audit/baseline/acceptance документы помечены историческими. Доказательства и D08/D09/D10/UNKNOWN DB сохранены.
- Проверки: python3 /tmp/lgg-plan-check.py PASS (54Markdown/152локальных ссылок+якорей/0ошибок, сохранность истории, отсутствие src/tests/frontend изменений); source app factory/OpenAPI54paths/71operations PASS; live dev HTTP200/54paths, path/method inventories equal; docker ps dev/test DB healthy, DB/media не менялись. AST307PASS; node --check /tmp/lgg-refined-script.js и git diff --check PASS. Premium resolver MATCH; SKILL.md/официальные web docs/npm metadata проверены, optional security skills pinned49f948faa9258a0c61caceaf225e179651397431 не установлены.
- Ограничения: fullpytest544/scoped48 — предыдущая T13R, здесь не повторялись; frontend npm install/build/browser/E2E/production/load/restore NOT RUN. Browser file://preview запрещён policy, local bind sandbox запрещён, обход не выполнялся. Python TLS metadata fetch отказал; curl с системной проверкой TLS успешно прочитал registry без установки. Dev image после T13R не пересобран. Host Node26.0/npm11.12, выбранный Node24.22LTS/npm11.19.1 ещё не подключён. Ручная приёмка приложения сейчас не нужна (UI нет), дизайн принят; следующая сессия Sol по первому промпту PROMPTS, T14a только локально.


## 2026-10-15 — возвращение к согласованию дизайна

- Владелец уточнил, что хочет подробнее проработать внешний вид до реализации: сочетание приложенного скриншота «Фокус» и последней «Учебной ленты», сначала общий вид, затем несколько разделов. Новая версия не утверждена.
- STATUS/GPT/DESIGN/D07 получили короткую актуальную отметку; технические карточки и backend не перепроектировались. Прежний принятый reference сохранён как история, не перезаписан новой неподтверждённой версией.
- В чате подготовлен общий вид с верхней светлой навигацией, голубым занятием и заданиями рядом; телефон переключается локально. Проверены разметка/ID/JS syntax и основные контрастные пары, слабые пары исправлены. Browser QA не заявляется.
- Код приложения/БД/media/Git/установки не затронуты. Следующий шаг — отзыв владельца об общем виде, затем согласование нескольких содержательных экранов в том же направлении; реализация ждёт отдельного поручения.


## 2026-10-15 — окончание повторного визуального согласования

- После общего вида владелец попросил немного больше цвета; просмотрел список ДЗ, ответ ученика и проверку преподавателя, явно одобрил: «делаем так». Это направление и показанные экраны, не runtime приёмка всех разделов.
- В assets сохранены точные просмотренные lgg-hybrid-overview.html и lgg-learning-sections.html; прежний lgg-approved.html сохранён как исторический. DESIGN/D07/GPT/STATUS/T14d согласованы с верхней навигацией и более насыщенными голубыми/мятными акцентами.
- Проверены уникальные ID/прямые ссылки DOM и JS syntax нового примера. Browser/E2E QA не выполнялся; прежние ограничения сохраняются. Код приложения/БД/media не менялись, commit/push/deploy/установок нет.
- Следующий разрешаемый шаг — локальная T14a по PROMPTS, только новым явным запросом.


## 2026-10-15 — уточнение будущего F02

- Владелец конкретизировал банк: выдача ДЗ из задач банка и кабинет подготовки ОГЭ/ЕГЭ по предмету/номеру/теме с авторскими конспектами, файлами и задачами для повторения.
- Уточнены существующие PRODUCT/TASKS F02/ARCHITECTURE; отдельный план или карточка реализации не создавались. F02 остаётся после MVP, модель/API и открытые детали уточняются перед этапом.
- Функциональный код/БД/Git не менялись. Проверены ссылки документов и diff; реализация по-прежнему требует отдельного запроса.


## 2026-10-16 — T14a: серверные списки/Q05 DONE локально

- Владелец разрешил только локальную T14a; [карточка](tasks/T14a.md) содержит файлы, точные команды, результаты и ограничения. T14b не начата; commit/push/deploy/установок нет.
- Добавлены view/student filters courses/lessons, deterministic sort и student-only `/homeworks/my/page` с status/course/view/overdue; legacy array сохранён, scope/count до LIMIT одним SQL snapshot.
- Guarded lgg-test/engine/session, synthetic и pytest media: scoped234 PASS, окончательные31 PASS, full575 PASS (487.69s), AST15/diff/whitespace PASS. Первый full573/1 выявил expiry boundary; исправлен statement timestamp, добавлен independent-writer regression, full повторён успешно.
- README/T14a/STATUS обновлены; schema/migrations/dev DB/media/image не менялись, исходный rules_project diff сохранён. Ручной тест владельца не нужен: UI отсутствует. Можно отдельно сохранить в GitHub; следующий запрос — только T14b.


## 2026-10-16 — T14b: контекст/deep links/read-only API DONE локально

- Владелец разрешил только локальную T14b; [карточка](tasks/T14b.md) содержит изменения, точные команды, результаты и ограничения. T14c не начата; commit/push/deploy/установок нет.
- Scoped Homework/Lecture details, batch context/working attempt/flags/file descriptors, debt picker и lesson recipients; lecture course/view/date+id pagination. Optional course/lesson PATCH expected_updated_at атомарно даёт один save и второй409 в независимых sessions.
- Guarded lgg-test/actual engine/session/ограниченная роль, synthetic/temporary media: T14a31, scoped179, отдельные T14b24, **final full601 PASS (489.01s)**, включая 26 final T14b cases. SQL no-write/no-lock GET, query bound20/50, PDF/WebP bytes metadata, OpenAPI leak scan, AST217/diff PASS.
- SQL inspect исправил correlation can_create_lesson (нельзя заимствовать связь второго teacher); промежуточный full70 остановлен, окончательный full повторён. Карточка/STATUS обновлены; schema/migrations/dev DB/media/image/UI/DESIGN сохранены. Ручная приёмка до UI не требуется; следующий этап T14c только новым поручением.


## 2026-10-16 — T14c: административные контракты DONE локально

- Только локальная T14c по явному поручению; [карточка](tasks/T14c.md) содержит файлы, команды, результаты и промежуточные исправления тестов. T14d не начата; commit/push/deploy/установок нет.
- Admin `/admin/users` list/detail с safe state/profile DTO, SQL search/filters/count; `/users/students?q=` сохраняет active link scope. Admin links page/end с cutoff один раз, course→link/enrollment locks, atomic audit/recalc, без отключения общего аккаунта/удаления файлов.
- Guarded lgg-test/actual engine/session, SQL ограниченная роль и Compose loopback подтверждены: scoped378 PASS (302.56s), full614 PASS (488.83s), включая 13 T14c cases/OpenAPI scan; AST218/diff/whitespace PASS. Independent-session end/relink/submit/move в обоих порядках, rollback audit/deadline/events и hidden gaps проверены.
- Карточка/STATUS обновлены; schema/migrations/dev DB/media/image/UI/DESIGN сохранены, ручная приёмка не требуется до UI. Готово к отдельному сохранению в GitHub; следующий новый запрос — T14d.

## 16.10.2026 — T14d: локальный SPA-каркас

- Только [T14d](tasks/T14d.md): exact frontend/lock/OpenAPI/client, светлый shell/A13, dev gallery, signed-out login; backend/данные сохранены.
- Node24.22/npm11.19.1 локально; npm ci/ls/typecheck/lint/format/unit18/build/types-repeat/contrast/premium strict PASS.
- Real IAB360/1280: keyboard/Select/Date/dialog/errors/back/nav/CTA/overflow, screenshots; zoom200/runtime reduced-motion и E2E — NOT RUN (границы в карточке).
- Preview5173 оставлен, ручная приёмка **ожидает владельца**, T14e/f не начаты. Без commit/push/PR/deploy/установки skills.

## 16.10.2026 — T14d: доработка визуальной подачи

- По замечанию владельца [T14d](tasks/T14d.md): первым в dev-only gallery показан цельный ученический пример по принятому дизайну; controls свёрнуты ниже.
- Примеры занятия/задания/результата/курсов с честными границами, без реального входа/записи. Shared preview header и mobile focus улучшены.
- Unit22/typecheck/lint/format/build/tokens/types/premium0 PASS; real360/1280 и новые screenshots. Georgia exception узко ограничен математическими знаками из reference.
- Ручная приёмка ожидает; прежние NOT RUN сохранены. T14e/f/backend/DB не затронуты; без commit/push/deploy.


## 16.10.2026 — T14e локально VERIFY
- Только T14e; прежние local changes сохранены. Расписание обновлено в PRODUCT/ARCHITECTURE/T15a.1/T15b.2 только как требования; T14f/T15 не реализованы.
- Cookie bridge/CSRF, memory access, Web Locks/BC, boot/me/roles, reauth/cleanup, activate/reset реализованы; принятый дизайн сохранён. Подробности — [T14e](tasks/T14e.md).
- До backend тестов actual SQL/engine/session/media guard PASS: lgg-test55432, lgg_test/lgg_test_app restricted, temporary media; dev8018/55431 и UNKNOWN не затронуты.
- Final full633 PASS/494.30s, bridge13 PASS; frontend unit25/typecheck/lint/format/build/types/tokens/premium PASS. Standalone tests_unit circular-import collection failure сохранён в карточке; первый full632 — предыдущий прогон.
- Final Chromium10 PASS/13.5s (три роли, две вкладки/reload/401/logout, links, mobile/offline/axe/reauth, returnTo); contrast/toggle44px исправлены. WebKit и остальные NOT RUN перечислены в карточке, T14d limits не закрывались.
- Ручная приёмка ожидает; preview5173 → synthetic backend8019, fresh ignored0600 credentials/links. Без commit/push/PR/merge/deploy/skills install; следующий T14f только новым поручением.


### 16.10.2026 — T14f локально, VERIFY

- T14e: владелец принял вход «ну вроде нормально»; все технические NOT RUN сохранены отдельно.
- [T14f](tasks/T14f.md): UploadQueue/authorized photo+PDF6.4.299, drafts/reauth/dirty/409/422, DEV real-API gallery; прежний дизайн и локальные изменения сохранены.
- Новые проверки: guarded lgg-test backend121/100.04s + permission/context49/52.70s; frontend unit38, Chromium15/30.6s и quality/types/tokens/premium PASS. Preview/pytest строго по очереди.
- WebKit/физические устройства/real post-commit transport и остальные пределы NOT RUN в карточке; ручная приёмка файлов ожидает. Fresh private credentials и synthetic PDF/фото в preview5173→8019, OS temporary media; dev8018/UNKNOWN не тронуты.
- Без commit/push/PR/merge/deploy/установки skills. T15 не начата; после ручной приёмки отдельный запрос на GitHub либо новый чат T15a.1.

### 16.10.2026 — ручная приёмка T14f

- После сценария PDF/фото владелец ответил «д все кайф епта»; ручной gate [T14f](tasks/T14f.md) принят.
- Карточка и STATUS обновлены; технические NOT RUN сохранены, новых тестовых PASS не добавлено.
- T14f остаётся VERIFY по техническим пределам. T15 не начата, Git/публикация не выполнялись.


### 16.10.2026 · T15a.1 — read-кабинет ученика
- По явному local разрешению реализован только [T15a.1](tasks/T15a.md): Мой день,
  desktop week/mobile days, курсы/архив, recipient-scoped урок/PDF; T15a.2 не начата.
- Backend preflight actual engine/session/restricted lgg-test/temp media PASS; preview8019
  остановлен перед pytest81 PASS/85.72s, dev8018 не тронут. Frontend unit44/quality/strict PASS.
- Chromium regression19 PASS/43.1s + final student-read4 PASS/12.8s; отдельные synthetic
  accounts/private0600, mobile touch/PDF1 PASS/3.2s; ручная приёмка ожидает. Прежние NOT RUN сохранены.
- Дизайн и прежние локальные изменения сохранены; без commit/push/PR/merge/deploy/skills install.


### 16.10.2026 · уточнение расписания и замечания T15a.1
- [PRODUCT §5](PRODUCT.md) и A09: teacher — общая недельная часовая сетка своих
  учеников/занятий с прямыми переходами; student — только занятия по дням без часовых строк.
- [T15a.1](tasks/T15a.md) и [T15b.2](tasks/T15b.md) синхронизированы; визуальные
  замечания к «Мой день» сохранены. Приёмка T15a.1 — замечания, старые PASS исторические.
- Только фиксация требований/STATUS: код, БД и runtime не менялись; T15a.2 не начата.


### 16.10.2026 — T15a.1, исправления после замечаний владельца
- Восстановлены выразительные задания/курсы и компактное занятие; student неделя по дням без часовой сетки, mobile day switch. [Карточка/evidence](tasks/T15a.md#исправления-t15a1-по-повторному-поручению--16102026).
- Новый actual DB/engine/session/temp-media guard PASS; preview остановлен до pytest: backend81 PASS/87.07s. Затем новый synthetic seed8019, dev8018 не тронут.
- Unit44/quality/build/types/tokens/premium strict PASS; Chromium regression19 PASS+1 focus-test FAIL, исправлен; final student-read5 PASS/14.2s + усиленный schedule1 PASS/2.6s. Визуальное сравнение обоих references и desktop/360 выполнено.
- VERIFY, повторная ручная приёмка ожидает; WebKit/full backend/прежние NOT RUN сохранены. T15a.2 не начата, прежние изменения сохранены; Git/publication/install не выполнялись.

### 16.10.2026 — T15a.1: отметка прошедшего времени
- Ненавязчивая подпись «Уже прошло» после окончания занятия, отдельно от backend статуса; отменённые исключены.
- Typecheck/lint/format/build/diff PASS, Chromium desktop/3601 PASS/2.1s; screenshots просмотрены. Backend/8018 не тронут, T15a.2 не начата.

### 16.10.2026 · T15a.2 — решение ученика
- T15a.1 принята владельцем; локально реализована только T15a.2, приёмка ожидает.
- Real API черновик/фото/submit/edit/result; общий reauth/dirty/version recovery, отдельный synthetic answer world.
- Новый guard actual lgg-test/session/temp media PASS; scoped92 PASS/95.56s, pytest и preview отдельно; dev8018 сохранён.
- Node .local-runtime: unit49/quality/build/types/tokens/premium PASS; Chromium24 PASS+1 environmental429 → узкий повтор1 PASS/2.0s, desktop/360 и screenshots проверены.
- [Карточка T15a.2](tasks/T15a.md#t15a2--локальная-реализация-16102026): URL, ignored0600 вход, media persistence, evidence/NOT RUN; без Git/deploy/skills install и T15a.3.


### 16.10.2026 · маршрут полной ручной приёмки T14/T15
- По запросу владельца подготовлен [маршрут](MANUAL_ACCEPTANCE_T14_T15.md): роли, актуальные synthetic ID, desktop/360, ДЗ, persistence и пустые чек-листы.
- Frontend5173 HTTP200; synthetic8019 был недоступен. Pytest не обнаружен; новый read-only actual engine/session/SQL lgg-test/temp media preflight PASS, Docker healthy55432.
- Восстановлен только synthetic8019 штатным seed; локальный ignored0600 вход обновлён. Авторизованные GET подтвердили текущие данные/PDF; браузерные сценарии за владельца не отмечены.
- Pytest/E2E/build/миграции не запускались; dev8018, код и дизайн сохранены. T15a.3/исправления/Git/публикация не начинались.


### 16.10.2026 · частичный отзыв и отметки дней расписания
- Владелец сообщил, что в целом всё нормально, но полный подробный проход не делал; полный чек-лист не закрыт.
- В PRODUCT/T15a/STATUS записана будущая ненавязчивая отметка дней с занятиями на narrow/mobile; код не менялся.
- По исходнику подтверждён порядок ДЗ: создание DESC, для checked — проверка DESC; без новой сортировки и запусков тестов.
- Для объяснения изучены T15b, PRODUCT, DESIGN и TASKS/F01/F05; следующая реализация/Git/deploy не запускались.


### 16.10.2026 · расширенный MVP преподавательского расписания — план
- По идеям владельца PRODUCT/T15b/ARCHITECTURE/TASKS/STATUS обновлены: запись из общей сетки, поиск своих с нормой/счётчиком, недобор и быстрый подтверждаемый перенос.
- T08b включена в teacher MVP как ограниченное закрепление времени1–12 недель; бесконечное продление не обещано, DnD отложен как удобство.
- Добавлена T15b.4: недельная статистика/ставки; единица цены и правила расчёта требуют согласования перед реализацией, суммы не означают оплаты.
- Выделены новые backend gaps и критерии scope/недели/дублей/истории цен. Только документы; код, DB, preview, тесты и Git не менялись.


### 16.10.2026 · сверка согласованности документов teacher MVP
- Устранены актуальные противоречия D03/T08b, устаревшие входы GPT/README/TASKS/WORKFLOW, учтены teacher расширение в DESIGN/A09, T16/P03 и PRIVACY.
- Добавлена исполнимая плановая карточка T08b; D11/D12 отделяют требования владельца от предложений горизонта/нормы/денежных правил. Исторические результаты T08/SESSION_LOG сохранены.
- Обнаружен риск потери прошлых сумм при архивировании: ретроспективные деньги не наследуют автоматически фильтр активного календаря; решение до финансового кода.
- По дополнительному запросу запущен прежний frontend5173 Node .local-runtime; synthetic8019 уже работал, seed/DB не менялись. HTTP200 login/API proxy, не новый браузерный PASS.
- Только документы и запуск preview; source hashes/ссылки/whitespace сверены отдельно, без pytest/E2E/build/миграций/Git/deploy.

### 16.10.2026 · T15a.3 — конспекты, уведомления, профиль
- По явному local разрешению реализована только [T15a.3](tasks/T15a.md#t15a3--локальная-реализация-16102026): real list/detail/PDF/архив, notification unread/poll/read/target, собственный профиль/avatar/password. Общие primitives/дизайн сохранены.
- Actual lgg-test engine/session/SQL/temp-media guard PASS; preview остановлен до pytest, scoped61 PASS/57.68s. Dev8018 не затронут; production backend/schema не менялись.
- Local Node unit55/quality/types/tokens/build/premium strict PASS; общий Chromium31 PASS/1.9m; final avatar read-failure lock/common-page title — повтор6 PASS/21.1s; финальный filename wrap360 —2 PASS/6.6s. Screenshots desktop360 просмотрены. Ранние FAIL/rate limits не замаскированы, детали в карточке.
- T15a.1 принята; T15a.2 частичный положительный отзыв без полного чек-листа; T15a.3 ручная приёмка ожидает. Historical NOT RUN и отложенные отметки дней сохранены; teacher/T08b/статистика не начаты.
- Synthetic5173→8019 оставлен для приёмки; актуальные входы в ignored0600 JSON и `frontend/.artifacts/t15a3-login.txt`, временные media. Без commit/push/PR/merge/deploy/установок; следующий код только новым поручением.

### 16.10.2026 · отзыв о выборе недели — только фиксация
- По скриншоту владельца записаны «Прошлая/Текущая/Следующая неделя» и видимый выбор открытой недели; источник — PRODUCT§5, критерии в [T15a](tasks/T15a.md#дополнение-выбор-недели--16102026).
- Отметки дней с занятиями остаются отложенными; обе правки рекомендованы одним малым student-пакетом до teacher UI после отдельного разрешения.
- Согласованы документы PRODUCT/T15a/STATUS/A09/DESIGN/TASKS; код/DB/preview не менялись, тесты не запускались, git diff--check PASS.
- T15a.2/.3 ручная приёмка не отмечена пройденной; исторические NOT RUN сохранены, teacher/регулярное расписание/статистика не начинались.

### 16.10.2026 · сохранение основной очереди по уточнению владельца
- Предыдущая рекомендация вынести правки расписания перед teacher UI отменена последним ответом владельца; историческая запись выше сохранена как история, не текущий порядок.
- Обе конкретные правки (подписи/выбор недели, отметки дней с занятиями) закреплены в [T16.1](tasks/T16.md#t161--регрессия-и-понятность-полного-mvp) после teacher/admin кабинетов, перед итоговой регрессией.
- PRODUCT/T15a/T16/TASKS/STATUS/DESIGN согласованы; следующий основной этап T15b.1 только отдельным запросом, приёмка T15a.2/.3 и NOT RUN не закрыты.
- Только документы: код/DB/preview/зависимости не менялись, тесты не запускались; git diff--check PASS. Commit/push/deploy не выполнялись.


### 16.10.2026 · T15b.1 локальная реализация
- По отдельному разрешению реализована только [T15b.1](tasks/T15b.md#t15b1--локальная-реализация-16102026): свои ученики/invite, персональный курс и recovery двух транзакций, редактирование/обложка/detach/архив/read/download. Общий дизайн и предыдущие правки сохранены.
- Preview останавливался перед pytest; actual SQL DB/engine/session/temp-media preflight PASS. Scoped68 PASS/31.94s + permissions/lifecycle49 PASS/54.08s; dev8018 не трогали, schema/backend не менялись.
- Local Node: unit57, typecheck/lint/format/build/API types/tokens/premium strict0 PASS. Финальный Chromium37 PASS/2.2m (включая6 teacher); mobile/keyboard/axe, two-tab409, lost-response POST без дубля и archive PDF/download PASS, screenshots просмотрены.
- Ручная T15b.1 и T15a.2/.3 ожидает; historical NOT RUN/full backend/WebKit/device matrix не закрыты. T15b.2–4/T08b/T16 не начинались; недели/отметки дней остаются T16.1. Commit/push/PR/merge/deploy/установки не выполнялись.
- В конце оставлен свежий synthetic5173→8019→lgg-test55432/temp-media, актуальный вход ignored0600 `frontend/.artifacts/t15b1-login.txt`; короткий маршрут в карточке/STATUS. Сохранение в GitHub — только отдельным запросом; дальше T15b.1 не переходили.


### 16.10.2026 · T15b.1 — ученик, класс и упрощение маршрута
- Владелец явно подтвердил общий редактируемый teacher школьный класс. Реализованы identity «Имя Фамилия · 10», поиск/фильтр и Student→personal workspace без ручного курса/enroll; [evidence и приёмка](tasks/T15b.md#t15b1-student-first).
- Узкий shared-grade PATCH с active-link/self/admin/expected-value/lock/audit; atomic idempotent personal start с independent-session concurrency и rollback. Legacy/course files сохранены; PRODUCT/D01/A09/DESIGN/PRIVACY согласованы, остальные поля профиля teacher не редактирует.
- Guard actual DB/engine/session/temp-media PASS до backend; preview остановлен. Scoped134 PASS, final context36 PASS + exact-key assertion исправлен/повтор1 PASS; migration31 PASS/74.18s (legacy/null/guarded downgrade; head assertions актуализированы), grade/workspace11 cases PASS. Dev8018 не трогали.
- Local Node unit58/typecheck/lint/format/types/tokens/build/strict0 PASS, итоговый Chromium35 PASS/2.1m;4 новых сценария/360/keyboard/axe/grade409/unknown POST/archive download, screenshots просмотрены. Ранний общий run остановлен для fresh namespace, не объявлен PASS; зависимости не устанавливались.
- Свежий synthetic5173→8019→lgg-test55432/temp-media оставлен, current вход ignored0600 `frontend/.artifacts/t15b1-login.txt`. Ручная T15b.1/T15a.2/.3 и historical NOT RUN открыты; T15b.2–4/T08b/T16/Git/deploy не начинались.


### 16.10.2026 · T15b.1 — список и страница ученика, повторная доработка
- Только [T15b.1](tasks/T15b.md#t15b1--доработка-двух-экранов-по-повторному-поручению--16102026): linked rows/числовой класс/вторичный логин,4 server sort до paging со stable ties; явные занятия/материалы, настройки ниже. Основной personal и legacy данные/дизайн сохранены.
- Actual test engine/session/SQL/temp-media guard PASS; scoped38 PASS/43.02s, до него38/44.88s. Первый sandbox batch ошибочно продолжил DB-blocked pytest после stop failure; реальные прогоны после stop8019, детали в карточке. Dev8018 не трогали.
- Local Node unit58/quality/build/types/tokens/premium0 PASS; общий Chromium33 PASS/3 FAIL, repeat2 PASS/1 FAIL: cache ожидание теста исправлено, meeting-link повтор PASS; notification checkbox воспроизводится и открыт вне scope.
- Final teacher5 PASS/17.9s после fresh namespace (предыдущий повтор прерван из-за account login limit); оба экрана1280/360 визуально проверены, keyboard/axe/empty/error/PDF/recovery PASS. Fresh synthetic5173→8019 оставлен, актуальный вход ignored0600 `frontend/.artifacts/t15b1-login.txt`.
- Карточка/STATUS/PRODUCT/DESIGN/A13 обновлены. T15b.1 на приёмку владельцу; T15a.2/.3 и historical NOT RUN не закрыты. T15b.2–4/T08b/T16/Git/deploy/install не начинались.


### 16.10.2026 · напоминания преподавателю о ДЗ/конспекте — только план
- По запросу владельца в PRODUCT§6 и [дополнение T15b.2](tasks/T15b.md#дополнение-t15b2--занятия-без-дзконспекта-и-длинная-история) записаны признаки у занятий и фильтр/приоритет учеников без ДЗ/конспекта.
- Ученик→стандартная страница занятия→выдать ДЗ/загрузить конспект, с возвратом в контекст; для длинной истории предложены недельные группы, вид не утверждён.
- A09/TASKS/STATUS согласованы; перед кодом уточнить актуальность по времени/статусу, отмену/архив и намеренное отсутствие материалов, полный recipient-scoped server aggregate до paging.
- Только документы; код/DB/runtime/preview не менялись, тесты не запускались. T15b.1 и T15a.2/.3 приёмки/NOT RUN открыты; следующий этап и Git/deploy не начинались.


### 16.10.2026 · «Мой день» преподавателя — согласованный план
- Владелец согласовал обзор: занятия сегодня/ближайшая встреча, работы на проверку, напоминания без ДЗ/конспекта и прямые переходы. Требования PRODUCT§8, исполнение — [T15b.2/.3](tasks/T15b.md#дополнение-t15b23--мой-день-преподавателя).
- Расписание недели отдельно; база обзора в .2, очередь/полный обзор и стартовый `/teacher` после gate .3. Сейчас вход в «Ученики», макет нового обзора ещё не принят.
- PRODUCT/ARCHITECTURE/TASKS/DESIGN/STATUS согласованы; исправлена устаревшая будущая root-навигация на schedule, текущий runtime не менялся.
- Только документы, diff-check PASS; код/DB/preview/тесты/Git/deploy не трогали. T15b.1/T15a.2/.3 приёмки и NOT RUN сохранены; дальнейшая реализация не начата.


### Архив STATUS перед техническим чекапом ·16.10.2026

Сохранён полный вход до сокращения повторов. Это исторический snapshot; актуальное
состояние и текущий preview — только STATUS, проверки — карточки T15a/T15b.

# Текущее состояние LGG

Обновлено16.10.2026. **T15b.1 VERIFY — доработано, на приёмку владельцу**.
Предыдущий вид не принят как окончательный. Список: целиком кликабельные строки,
имя/фамилия, отдельная метка класса и вторичный логин; поиск/класс/четыре server
сортировки до пагинации со стабильными ties. Страница ученика: ясная шапка →
занятия со словами состояния → раскрываемые материалы; пустой select/повторная
навигация убраны. Настройки/приглашение/прежние курсы ниже. Один основной personal
course и прошлые курсы/данные сохранены, принятые tokens/Manrope прежние.
[Изменения, проверки и актуальный маршрут](tasks/T15b.md#t15b1--доработка-двух-экранов-по-повторному-поручению--16102026).

Новые проверки: actual engine/session/SQL/temp-media guard PASS; backend scoped
**38 PASS/43.02s** (предыдущий batch38/44.88s), unit**58 PASS**, typecheck/lint/format/
build/API types/tokens/premium strict0 PASS. Desktop1280/mobile360 визуально
проверены оба экрана, keyboard/axe/empty/error и teacher recovery. Полный Chromium
**33 PASS/3 FAIL**: два прежних student-сценария и неверное ожидание cache в новом
test. Ожидание test исправлено; узкий повтор — **2 PASS/1 FAIL**, ссылка встречи и
новый T15b PASS, checkbox уведомлений воспроизводится (T15a, не исправляли вне scope).
Финальный teacher scoped **5 PASS/17.9s** на fresh namespace; оба экрана1280/360
визуально просмотрены. Общий run не PASS; точные evidence/ограничения — карточка.

Ручная T15b.1 **ожидает**; T15a.2/.3 и historical NOT RUN открыты.
T08b/T15b.2–4/T15c/T16 не начинались, недели/отметки дней остаются T16.1.
Без commit/push/PR/merge/deploy/установок. Dev8018/55431 не трогали.
Новый запрос16.10 зафиксирован **только как TODO T15b.2**: признаки отсутствия
ДЗ/конспекта у занятий, быстрый фильтр/приоритет учеников, прямой переход в урок
для выдачи/upload и обозримая история (недельные группы — предложение).
Правила актуальности напоминаний уточнить до кода; текущую T15b.1 не расширяет.
Также согласован **TODO «Мой день» преподавателя**: сегодня/ближайшая встреча,
проверка работ, напоминания и прямые переходы (PRODUCT§8). База в T15b.2, полный
обзор/очередь и стартовый вход после gate T15b.3; сейчас по-прежнему «Ученики».

Работающий [synthetic preview](http://127.0.0.1:5173/login?returnTo=/teacher/students)
5173→8019→guarded lgg-test55432; временные media, не production persistence.
Актуальные username/password и direct path ученика с PDF — ignored0600
`frontend/.artifacts/t15b1-login.txt`, полный private набор `t14e-credentials.json`.
Маршрут: Ученики→сортировка/поиск/класс→строка ученика→открыть материалы→PDF;
проверить360px, возврат к списку, затем второстепенные настройки/архив по желанию.
Первый sandbox batch ошибочно продолжил попытку pytest после запрета stop/DB;
DB недоступна, не PASS. Реальные backend batches выполнялись после stop8019.

## Сохранённый результат T15a

Обновлено 16.10.2026. **T15a.3 VERIFY локально:** общий список конспектов,
уведомления и свой профиль реализованы по отдельному разрешению владельца.
Ручная приёмка T15a.3 ожидает. T15a.1 принята владельцем; T15a.2 VERIFY локально,
положительный частичный отзыв без полного чек-листа. Исторические технические
NOT RUN T14/T15a.1/.2 сохранены, parent T15a не DONE. Дальше T15a.3 не переходили.
Прежние изменения и согласованный дизайн сохранены; dev backend8018 не затронут.
Без commit/push/PR/merge/deploy/установки навыков или зависимостей.

Владелец16.10 дополнительно посмотрел готовое: в целом нормально, полный маршрут
не проходил. Положительный частичный отзыв записан в T15a, полный чек-лист не закрыт.
Отложено: ненавязчивые отметки дней с занятиями на narrow/mobile расписании;
[требование и критерии](tasks/T15a.md#отзыв-владельца-и-отложенная-доработка--16102026).
Дополнительно16.10 зафиксированы подписи «Прошлая / Текущая / Следующая неделя»
(полные подписи со словом «неделя») и видимое выделение открытой недели.
Обе доработки student-расписания закреплены в T16.1 после teacher/admin кабинетов,
перед итоговой регрессией. Не вставлять их перед T15b.1; идём по основному плану.
Позднее отдельным запросом разрешена только T15b.1, текущий результат указан выше.
Ручная приёмка T15a.2/.3 и historical NOT RUN остаются открытыми.

Расширение teacher MVP16.10 — только план: click по времени/поиск своих учеников,
недельная норма и недобор, регулярное время T08b (горизонт/продление открыты в D11), быстрый перенос с подтверждением;
затем T15b.4 недельные суммы/ставка (формулы/история требуют D12 перед кодом).
DnD — последующее удобство. [Карточка и порядок](tasks/T15b.md); новые API gaps
не реализованы. Код teacher этапов .2–4 не разрешён и не начинался.

## Приёмка текущего результата

[T15a.3 — реализация и evidence](tasks/T15a.md#t15a3--локальная-реализация-16102026).
Конспекты: real list/course/date/view/total/20–50, direct lecture/PDF/download/архив.
Уведомления: unread/list/read/authorized target, polling60s visible+online,
focus/resume/abort; недоступный target остаётся понятным. Профиль: own API/ID adapter,
nullable поля, conflict/dirty guard/unknown-save read-before-retry, avatar атомарно,
password revoke и повторный вход; admin без avatar-профиля не получает upload.
Оставлены teacher/admin учебные кабинеты и отложенные отметки дней.

Actual lgg-test DB/engine/session/temp-media guard PASS до scoped backend:
**61 PASS/57.68s**, pytest/preview не пересекались. Frontend local Node: unit55,
typecheck/lint/format/types/tokens/build и premium strict0findings PASS.
Общий Chromium **31 PASS/1.9m**; после финальной блокировки avatar retry при failed
read и common-page title — все6 T15a.3 сценариев повторены: **6 PASS/21.1s**. Финальный filename wrap360 — ещё **2 PASS/6.6s**
(materials + прежний protected-PDF). Full31 на последнем CSS не повторялся.
Real API/mobile360/keyboard/axe, PDF/архив, invalid/unavailable target, save409,
avatar failure+failed read/delete404, wrong-current password/revoke/reauth,
unknown save/same-user draft/logout PASS. Screenshots просмотрены.
Full backend/WebKit/физические устройства/full device+zoom matrix NOT RUN.
Эти результаты не заменяют ручную приёмку T15a.2/.3 и не закрывают прежние NOT RUN.

Текущий preview и вход T15b.1 — в начале STATUS; новый seed сменил пароли и media.
Прежний [ручной маршрут](MANUAL_ACCEPTANCE_T14_T15.md) остаётся незакрытым.

## Реализация

| ID | Статус | Факт / следующий шаг |
|---|---|---|
| T00–T13, T05b, T12a/b/c | DONE локально | Карточки [T00](tasks/T00.md)–[T13](tasks/T13.md), baseline по этапам |
| T13R | DONE локально | [Исправления Q01–Q04](tasks/T13R.md), full544/scoped48, migration/AST/diff PASS по прошлой сессии |
| T08b | TODO | По уточнению16.10 регулярное время входит в teacher MVP; D11→[T08b](tasks/T08b.md) до UI T15b.2 |
| T14a | DONE локально | SQL view/student filters, paginated my homeworks; scoped234/final31/full575 PASS, AST/diff PASS |
| T14b | DONE локально | Direct context/read-only API/debt picker/file metadata/conditional PATCH; scoped179/T14b24/full601 PASS, 26 final T14b cases |
| T14c | DONE локально | Admin users/search, links list/end; scoped378/full614 PASS, OpenAPI/AST/diff PASS |
| T14d | VERIFY локально | Визуальная основа одобрена; [runtime NOT RUN](tasks/T14d.md) сохраняются |
| T14e | VERIFY локально | [Вход принят владельцем](tasks/T14e.md); технические NOT RUN, включая WebKit, сохранены |
| T14f | VERIFY локально | [Файлы/восстановление](tasks/T14f.md) приняты владельцем; WebKit и остальные технические NOT RUN сохранены |
| T15a.1 | VERIFY локально | [Read-кабинет](tasks/T15a.md) принят владельцем16.10; технические NOT RUN сохранены |
| T15a.2 | VERIFY локально | [Решение/фото/отправка/результат](tasks/T15a.md#t15a2--локальная-реализация-16102026): реализованы, проверки PASS; ручная приёмка ожидает |
| T15a.3 | VERIFY локально | [Конспекты/уведомления/профиль](tasks/T15a.md#t15a3--локальная-реализация-16102026): реализация и проверки выполнены, ручная приёмка ожидает |
| T15b.1 | VERIFY локально | [Свои ученики, приглашение и персональный курс](tasks/T15b.md#t15b1--локальная-реализация-16102026), проверки PASS; ручная приёмка ожидает |
| T15b.2–4 / T15c.1–2 | TODO | Не начаты; [карточки](TASKS.md#интерфейс-и-качество-оставшийся-путь), только отдельное поручение |
| T16.1–2 | TODO | Реальные E2E/CI/понятность, [карточка](tasks/T16.md) |
| T17.1–2 / T18.1–2 | TODO | Bundle/server prep/backup restore/alerts |
| P01 / P02.1–2 / P03 | TODO | Допуск/релиз/пилот; отдельные ручные/публикационные gates |
| F01–F06 | DEFERRED | ВК/банк/SaaS и другие расширения вне MVP |

## Код, окружение и Git

Внутренний repo `API_online_school`, ветка `codex/t00-t01-environment`, HEAD`95b3560`.
T10–T12 commit`f6d41fd`, T13/T13R commit`95b3560`; commit/push не выполнялись.
Tracking refs/GitHub не обновлялись; исторический draft PR#1 не проверен заново.
Много planning/instruction файлов остаются untracked, прежний rules_project diff
сохранён. Поэтому пакет пока **локальный**, не «сохранён в GitHub».

T14c проверена на guarded `lgg-test` PostgreSQL: Compose project/loopback55432,
SQL DB/роль lgg_test/lgg_test_app без superuser/createdb, actual engine/session guard,
synthetic и temporary pytest media. Scoped378 PASS (302.56s), full614 PASS (488.83s),
включая 13 T14c cases/OpenAPI leak scan; AST218 (src217+test)/diff/whitespace PASS.
Схема не менялась; миграции не нужны. Dev DB/media/image не затронуты.
T14a full575/T14b full601 — отдельные предыдущие проверки; история — карточки/SESSION_LOG.
T14e проверки выполнены отдельно и описаны выше/в карточке; T14c scoped378/full614 — исторический результат.
Полный учебный E2E T15/T16, production/restore/load и отмеченные browser limits не выполнены.

## Решения и участие владельца

D01–D07 приняты; визуальная основа D07 уточнена последним одобрением, stack выбран агентом по
поручению: [RESEARCH](RESEARCH.md). Понятность обязательна (PRODUCT §8).
D08 оператор/основания/retention — перед реальными данными P01; D09 сервер —
перед T17.2/P02; D10 права/коммерция — F03. Внешняя рабочая БД всё ещё UNKNOWN.
Ручная приёмка T14e и файлов T14f получена; T14f: «д все кайф епта».
Она не заменяет технические проверки и не закрывает NOT RUN.
Read-сценарий T15a.1 принят владельцем. Отправка фото T15a.2 реализована локально,
ручная приёмка ожидает; полный teacher UI цикл T15b.3 ещё не реализован.

История из прежних 624 строк STATUS сохранена в существующем
[SESSION_LOG](SESSION_LOG.md#архив-status-перед-полным-frontend-планированием-15102026),
полные подтверждения по задачам — в карточках. CHECKUP_T13/CODE_REVIEW/АУДИТ —
исторические снимки, не конкурирующие требования. Следующее действие владельца:
ручная приёмка T15b.1 и T15a.2/.3; GitHub сохранение и следующая реализация требуют отдельного запроса.
Commit/push автоматически не разрешены. Preview5173 использует только synthetic
backend8019 → guarded lgg-test55432 и OS temporary media; dev8018/55431 не менялись.
Private credentials/одноразовые ссылки — ignored0600 `frontend/.artifacts/t14e-credentials.json`.


### Архив ручного маршрута до чекапа ·16.10.2026

Исторический seed и исходные инструкции/незаполненные чек-листы сохранены ниже.
Актуальный маршрут — MANUAL_ACCEPTANCE_T14_T15.md; старые numeric URL не использовать.

# Ручная приёмка локальной LGG: маршрут владельца

Подготовлено 16.10.2026. Все поля проверки ниже оставлены владельцу. Это инструкция для самостоятельной приёмки готового, а не свидетельство, что вы уже всё приняли. T15a.1 принята; T15a.2 вы посмотрели и оценили в целом нормально, подробная приёмка остаётся открытой. T15a.3, преподавательский и административный интерфейсы не начинались.

## 1. Быстрый старт

1. Откройте [вход](http://127.0.0.1:5173/login).
2. Откройте локальный [актуальный файл входа](../../frontend/.artifacts/t14e-credentials.json). Найдите объект `read_student`, скопируйте его `username` и `password` в форму. Не отправляйте содержимое файла в чат и не включайте его в скриншоты.
3. Начните с [«Мой день»](http://127.0.0.1:5173/student): занятие → PDF → расписание → курсы → архив. Это сценарий A ниже.
4. Затем выйдите и войдите через `answer_student` из того же файла. Пройдите подробный сценарий ДЗ в разделе 5.

Старые логины из прошлых сессий не используйте. Сегодня backend8019 восстановлен, файл входа обновлён. Закладки на конкретные задания ниже действуют для этого запуска. Новый запуск seed создаст другие аккаунты и ID; ориентиром снова станет актуальный локальный файл. До перезапуска preview текущие данные можно менять приёмкой.

Все адреса ниже — локальные, без приватных ссылок и токенов. Используйте везде `127.0.0.1`, не смешивайте с `localhost`.

### Что проверено при подготовке этого документа

- Frontend5173: HTTP200; synthetic backend8019: OpenAPI HTTP200 после восстановления.
- Перед восстановлением по списку процессов pytest не обнаружен. Read-only preflight подтвердил actual engine URL, session factory bind и фактическую session.bind; SQL: `lgg_test` / `lgg_test_app`, без superuser/createdb/createrole; временные media. Docker `lgg-test-postgres-1` healthy, PostgreSQL15 на `127.0.0.1:55432`.
- Указанные страницы отвечают оболочкой SPA HTTP200; через авторизованные GET подтверждены текущие курсы, уроки, ДЗ, оценки и доступность четырёх PDF у `read_student`. Входы student/teacher/admin доступны. Это короткая проверка доступности и данных, **не новый браузерный прогон и не ваша ручная приёмка**. HTTP200 у страницы-заглушки не означает готовую функцию.
- Pytest, E2E, build, миграции не запускались. Прежние результаты в карточках — исторические. Dev backend8018 и dev окружение не менялись.

## 2. Карта готовности и входов

В каждой строке «файл входа» означает [этот локальный JSON](../../frontend/.artifacts/t14e-credentials.json). Пароли здесь намеренно не приводятся.

| Роль / раздел | Проверенный адрес | Ключ в файле входа | Что работает сейчас | Дизайн / приёмка |
|---|---|---|---|---|
| Все: вход | [Войти](http://127.0.0.1:5173/login) | Нужная роль из строк ниже | Реальная авторизация, восстановление сессии, выход; неверный вход и ограничения попыток | Согласованный вид; вход T14e ранее принят |
| Активация / новый пароль | [Активация](http://127.0.0.1:5173/activate), [сброс](http://127.0.0.1:5173/reset-password) | `invite`, `reset`: локальные одноразовые URL в JSON | Реальное принятие приглашения/сброса, если ссылка ещё действительна; без ссылки — состояние ошибки | Реальный auth UI, не учебный кабинет; принятие входа не доказывает все редкие случаи |
| Ученик: мой день | [Мой день](http://127.0.0.1:5173/student) | `read_student`, файл входа | API ближайшего занятия, ДЗ к выполнению, последнего результата и курсов | Реализация принятой T15a.1 |
| Ученик: расписание | [Неделя](http://127.0.0.1:5173/student/schedule?view=all) | `read_student`, файл входа | API своих занятий; недели, дни, время МСК, переходы к уроку и курсу | Принятый компактный вид по дням; без часовой сетки |
| Ученик: курсы | [Курсы](http://127.0.0.1:5173/student/courses), [архив](http://127.0.0.1:5173/student/courses?view=archive) | `read_student`, файл входа | API списков/карточек/занятий; активные, архив, все | Принятая T15a.1; текущую работу можно перепроверить |
| Ученик: урок | [Квадратные уравнения](http://127.0.0.1:5173/student/lessons/1615) | `read_student`, файл входа | API урока, персонального получателя, материалов, ДЗ; защищённый PDF | Принятая T15a.1 и общие файлы T14f |
| Ученик: ДЗ | [Список](http://127.0.0.1:5173/student/homeworks), [рабочее задание](http://127.0.0.1:5173/student/homeworks/1915) | `answer_student`, файл входа | Реальные список/условие/черновик/файлы/отправка/изменение до проверки/история | Согласованный дизайн реализован; подробная приёмка T15a.2 ваша |
| Ученик: результаты | [Проверено](http://127.0.0.1:5173/student/homeworks?status=checked&view=all), [результат 0](http://127.0.0.1:5173/student/homeworks/1916), [результат 5](http://127.0.0.1:5173/student/homeworks/1919) | `answer_student`, файл входа | API read-only результата, оценки и комментария; подготовленные synthetic записи | Реальный экран T15a.2; результат заранее подготовлен, teacher UI отсутствует |
| Ученик: пустой кабинет | [Мой день](http://127.0.0.1:5173/student), [курсы](http://127.0.0.1:5173/student/courses), [ДЗ](http://127.0.0.1:5173/student/homeworks) | `read_empty` или `answer_empty`, файл входа | Реальные пустые ответы API, а не нарисованное отсутствие данных | Те же компоненты; отдельная проверка понятности |
| Ученик: общий список конспектов | [Конспекты](http://127.0.0.1:5173/student/materials) | `read_student`, файл входа | «Раздел ещё не подключён»; материалы уже доступны **внутри урока** | Экран списка пока отсутствует, T15a.3 |
| Общие профиль / уведомления | [Профиль](http://127.0.0.1:5173/profile), [уведомления](http://127.0.0.1:5173/notifications) | Любая роль, файл входа | Общая заглушка «Вход выполнен»; редактирования/списка нет | Готового продуктового экрана нет, T15a.3 |
| Преподаватель | [Расписание](http://127.0.0.1:5173/teacher/schedule) | `teacher`, файл входа | Настоящий вход, сессия и выход. После входа только «Вход выполнен» | Учебный кабинет **не реализован**. Наличие пунктов меню не означает готовность |
| Администратор | [Пользователи](http://127.0.0.1:5173/admin/users) | `admin`, файл входа | Настоящий вход, сессия и выход. Каталога пользователей/форм нет | Административный UI **не реализован** |
| Пример дизайна | [Галерея](http://127.0.0.1:5173/__ui) | Не требуется | Локальная демонстрация экранов и компонентов; не учебные API | Визуальная основа T14d одобрена. Макет не доказывает готовность кабинетов |
| Техническая файловая площадка | [Файлы](http://127.0.0.1:5173/__ui/files) | `files_student`, файл входа | «Открыть тестовые файлы» использует настоящее API ответа; PDF/фото и операции с файлами реальные. Ниже отдельно показаны искусственные ошибки | Общие файловые элементы T14f приняты; сама площадка — техническая демонстрация |
| Ошибки доступа/адреса | [Нет доступа](http://127.0.0.1:5173/403), [несуществующая страница](http://127.0.0.1:5173/no-such-page) | Не требуется | Настоящие общие экраны 403/404, возврат | Согласованный общий каркас, проверить понятность и возврат |

### Что есть только в backend, но нельзя принять через готовый UI

T14a/b добавили списки/фильтры/контекст и прямое чтение; ученические страницы используют часть этих контрактов. Подбор старого ДЗ как долга, управление уроками/курсами с защитой от устаревшей версии и выбор получателя материалов у преподавателя пока не имеют готовых форм.

У преподавателя через API уже существуют работа со своими учениками/курсами/занятиями, материалы и выдача ДЗ, очередь ответов и проверка 0–5. В UI сейчас нельзя создать ученика, выдать задание, перенести занятие, загрузить конспект или проверить ответ. Это будущие T15b.1–3. Не пытайтесь пройти эти действия через меню-заглушку.

T14c реализовала административные API списка/поиска пользователей, деталей и связей преподаватель–ученик, завершения связи. Существуют также backend-контракты приглашений, статуса аккаунта, квот, архива/восстановления/удаления и аудита. Административных форм, каталога и журнала сейчас нет (T15c). Ранее выполненные API-тесты не являются ручной проверкой этих экранов.

Профиль/аватар/пароль, уведомления/прочтение и общий список конспектов имеют backend-основу, но соответствующий UI ещё отсутствует. Не считать это работающими разделами из-за наличия ссылок в шапке.

## 3. Конкретные данные этого запуска

Названия повторяются намеренно: два независимых ученика (`read_student` для просмотра, `answer_student` для изменений), у каждого два преподавателя и архив. Одинаковое название урока в другом курсе — другая запись. При повторных автоматических прогонах/seed создавались отдельные synthetic аккаунты и миры; это не реальные ученики и не ваши многократные отправки. Старые ID из SESSION_LOG не используйте.

Текущий seed подготовлен скриптами `scripts/t14e_preview.py` и `scripts/t15a_seed.py`. Он не удалял прежние записи. У актуального ученика должно быть три курса и семь занятий/ДЗ, а не весь накопленный каталог test DB. Два проверенных ответа в каждом мире — заранее подготовленные fixture записи; они не получены вашей отправкой. В этом восстановленном запуске E2E не запускались и новых результатов E2E нет.

| Вход | Курс и его URL | Занятия → соответствующие ДЗ |
|---|---|---|
| `read_student` | [Алгебра · учебный курс, 1576](http://127.0.0.1:5173/student/courses/1576?view=all) | [Квадратные уравнения, 1615](http://127.0.0.1:5173/student/lessons/1615) → [1908](http://127.0.0.1:5173/student/homeworks/1908); [Разбор решения, 1616](http://127.0.0.1:5173/student/lessons/1616) → [1909, проверено 0](http://127.0.0.1:5173/student/homeworks/1909); [Практика, 1617](http://127.0.0.1:5173/student/lessons/1617) → [1910](http://127.0.0.1:5173/student/homeworks/1910) |
| `read_student` | [Геометрия · второй преподаватель, 1577](http://127.0.0.1:5173/student/courses/1577?view=all) | [Квадратные уравнения, 1618](http://127.0.0.1:5173/student/lessons/1618) → [1911](http://127.0.0.1:5173/student/homeworks/1911); [Разбор решения, 1619](http://127.0.0.1:5173/student/lessons/1619) → [1912, проверено 5](http://127.0.0.1:5173/student/homeworks/1912); [Практика, 1620](http://127.0.0.1:5173/student/lessons/1620) → [1913](http://127.0.0.1:5173/student/homeworks/1913) |
| `read_student` | [Архив · повторение, 1578](http://127.0.0.1:5173/student/courses/1578?view=all) | [Квадратные уравнения, 1621](http://127.0.0.1:5173/student/lessons/1621) → [1914](http://127.0.0.1:5173/student/homeworks/1914), только чтение |
| `answer_student` | [Алгебра · учебный курс, 1580](http://127.0.0.1:5173/student/courses/1580?view=all) | [Квадратные уравнения, 1622](http://127.0.0.1:5173/student/lessons/1622) → [1915, начать здесь](http://127.0.0.1:5173/student/homeworks/1915); [Разбор решения, 1623](http://127.0.0.1:5173/student/lessons/1623) → [1916, проверено 0](http://127.0.0.1:5173/student/homeworks/1916); [Практика, 1624](http://127.0.0.1:5173/student/lessons/1624) → [1917, запасное чистое](http://127.0.0.1:5173/student/homeworks/1917) |
| `answer_student` | [Геометрия · второй преподаватель, 1581](http://127.0.0.1:5173/student/courses/1581?view=all) | [Квадратные уравнения, 1625](http://127.0.0.1:5173/student/lessons/1625) → [1918, запасное чистое](http://127.0.0.1:5173/student/homeworks/1918); [Разбор решения, 1626](http://127.0.0.1:5173/student/lessons/1626) → [1919, проверено 5](http://127.0.0.1:5173/student/homeworks/1919); [Практика, 1627](http://127.0.0.1:5173/student/lessons/1627) → [1920](http://127.0.0.1:5173/student/homeworks/1920) |
| `answer_student` | [Архив · повторение, 1582](http://127.0.0.1:5173/student/courses/1582?view=all) | [Квадратные уравнения, 1628](http://127.0.0.1:5173/student/lessons/1628) → [1921](http://127.0.0.1:5173/student/homeworks/1921), только чтение |

«Квадратные уравнения» активных курсов имеют scheduled; «Разбор решения» — completed; «Практика» — cancelled. Даты искусственные: seed ставит даже completed в будущее для проверки подписи статуса. Это не реальный школьный календарь. Алгебра read_student: 16 октября 16:21 МСК, геометрия 18:21, архив 20:21; остальные занятия на следующие дни. Если проходите позднее, ближайшее занятие может исчезнуть из «Мой день»: используйте прямой адрес и неделю 12–18 октября. «Уже прошло» — подпись по времени, она не переводит scheduled в completed.

У `read_student` четыре настоящих PDF «Учебный пример.pdf»: три алгебраических урока и архивный. У геометрии материалы пустые. У `answer_student` конспектов сейчас нет. В файловой площадке `files_student` есть `math.pdf` и `notebook.webp`.

Условие ДЗ: «Решите уравнение x² − 5x + 6 = 0». В этом seed сроки null: ожидается «До следующего занятия», не выдуманная дата и не 1970 год. Долги и история переносов в текущем наборе не подготовлены; интерфейс их чтения существует, но честно проверить реальный перенос через UI сейчас нельзя. Отсутствие долга не считать ошибкой.

## 4. Основной проход на desktop

### A. Ученик: занятие → материалы → расписание → архив

1. Войдите `read_student` → «Мой день». Должны быть независимые блоки ближайшего занятия, заданий, последнего результата, курсов. В активных курсах алгебра и геометрия, архив отдельно. Чужого скрытого курса быть не должно.
2. Откройте занятие «Квадратные уравнения» алгебры (1615). Ожидайте тему, время МСК, длительность, описание, материалы и ДЗ. Встреча не настроена: «Ссылка на встречу ещё не добавлена». Реального созвона здесь нет.
3. Нажмите файл в «Материалы занятия». Откройте вторую страницу PDF, увеличьте масштаб, скачайте. Должен открыться читаемый двухстраничный synthetic документ, а скачанный файл находится в загрузках браузера. Просмотр/скачивание не создают решение.
4. Закройте просмотр Escape, затем снова откройте/закройте кнопкой. Фокус должен вернуться к действию открытия. Внутри PDF проверьте Tab/Enter и доступность кнопок масштаба/страниц. Возврат браузера из просмотра с адресным состоянием не должен неожиданно выбрасывать из кабинета; если ушли к предыдущей странице, повторно откройте урок и запишите точный путь.
5. Откройте «Расписание» → «Все». На desktop ожидайте неделю по дням с компактными занятиями, **без** часовых пустых строк. Предыдущая/следующая неделя и «Сегодня» меняют диапазон. Проверьте переход и к уроку, и отдельно к курсу. Вернувшись браузерной кнопкой «Назад», найдите прежнюю неделю/фильтр.
6. Откройте «Мои курсы» → геометрия1577 → урок1618. Материалы пустые: понятное сообщение, без предложения ученику загрузить конспект. ДЗ доступно. Возврат — через «К занятиям курса» или «Назад».
7. «Мои курсы» → «Архив» → «Архив · повторение»1578 → при необходимости «Все»/«Архив» у занятий → урок1621. Ожидайте причину режима чтения. PDF можно открыть/скачать. ДЗ1914 открывается, но добавлять ответ и файлы нельзя. Результат проверки сохранён в тех же страницах; отдельного ZIP-экспорта нет.
8. Откройте список ДЗ → «Проверено» → 1909. Ожидайте 0 из 5 и «Синтетическая проверка.». Ноль — полноценная оценка, не отсутствие результата. Для 1912 — 5 из 5. Не должно быть кнопок редактирования.

### B. Пустые разделы и восстановление входа

1. Выйдите → войдите `read_empty`. Откройте «Мой день», курсы, расписание, ДЗ. Должны быть объяснения отсутствия данных; у ученика нет кнопок создания урока/курса.
2. На пустом расписании выберите другой день; пустота относится к выбранному дню. На списке ДЗ смените фильтр, затем «Показать все задания»: ничего не должно ломаться.
3. Выйдите, войдите `read_student`, откройте прямой URL урока1615 и сделайте reload. Урок должен открыться без предварительного выбора курса; если сессия истекла, сначала вход.
4. Откройте конспекты, профиль, уведомления: сравните с картой готовности. Здесь вы проверяете честность заглушек, не принимаете отсутствующие функции.

### C. Преподаватель и администратор — граница готового

1. Выйдите → войдите `teacher` → адрес `/teacher/schedule`. Должны быть активная сессия, общая навигация, «Вход выполнен» и сообщение о будущем подключении разделов. Проверить ДЗ через этот экран нельзя.
2. Откройте ученический URL под teacher: ожидается «Нет доступа». Не меняйте URL на API для создания/удаления данных.
3. Выйдите → войдите `admin` → `/admin/users`. Ожидайте ту же честную заглушку, не каталог пользователей. Ученический кабинет этой роли недоступен.
4. Выход и повторный вход — реальные действия. Не отмечайте управление учениками/курсами, проверку и администрирование как пройденные: UI отсутствует.

## 5. Полный сценарий домашнего задания

Вход `answer_student`, [ДЗ1915](http://127.0.0.1:5173/student/homeworks/1915). Если вы уже изменили его, используйте чистое1918 или1917. Не удаляйте существующее решение ради восстановления начального состояния.

Подготовьте на компьютере четыре искусственных картинки `synthetic-1.png`…`synthetic-4.png` и одну `synthetic-replace.png`: например, создайте в любом редакторе изображения только с цифрами и подписью «Тест». Можно сделать копии [искусственного notebook.png](../../frontend/e2e/fixtures/notebook.png) с разными именами. Не используйте фотографии людей, настоящих тетрадей учеников и документов. Размеры небольшие, меньше20 МиБ. Фото на сервере преобразуются в WebP, поэтому имя/расширение после загрузки может измениться. Для PDF используйте [math.pdf](../../frontend/e2e/fixtures/math.pdf).

| Шаг: откуда и действие | Что ожидается и где найти результат |
|---|---|
| 1. Список ДЗ → «К выполнению» →1915. Просто открыть, затем reload | «Решение ещё не сохранено», нет сохранённых файлов. Одно открытие не создаёт ответ. В списке «К выполнению» |
| 2. Ввести `Synthetic: x=2 и x=3. Проверка приёмки.` → «Добавить файлы» → выбрать3 картинки | Текст и очередь3 файлов видны в текущей вкладке. Это ещё не серверный черновик, преподавателю не отправлено |
| 3. Попробовать перейти в «Мои курсы» → в предупреждении нажать «Отмена» | Остаётесь на форме, введённый текст и все3 выбранных файла сохранены в памяти. Не подтверждайте уход на этом шаге |
| 4. «Сохранить черновик», дождаться окончания всех загрузок/обработки | «Черновик · ещё не отправлен», текст на сервере,3 сохранённых файла. При ошибке одного файла не считайте весь шаг успешным. В общем списке это по-прежнему **«К выполнению»** |
| 5. Reload, при запросе браузера не подтверждать потерю, пока загрузка не завершилась | Вновь открывается серверный черновик с тем же текстом и3 файлами. После успешного сохранения локальной очереди быть не должно. Откройте каждое фото и проверьте содержимое |
| 6. «Добавить файлы» →4-я картинка → «Сохранить черновик» | Статус черновика, теперь4 сохранённых файла; предыдущие3 остались. Новый выбор сам по себе ещё не подтверждение загрузки |
| 7. У одного сохранённого файла «Заменить» → synthetic-replace → «Сохранить черновик» | По-прежнему4 файла: новая картинка вместо выбранной, остальные не поменялись. До сохранения замена находится в очереди |
| 8. «Удалить» у одного другого сохранённого файла → сначала «Отмена», затем снова «Удалить» → подтвердить «Удалить файл» | Отмена оставляет4 файла. Подтверждение сразу обращается к серверу: остаются3. Отдельная кнопка сохранения текста для этого удаления не нужна. Reload подтверждает точное удаление |
| 9. «Отправить решение», дождаться явного подтверждения | Сначала завершаются сохранение текста/файлов, затем отправка. Только после успеха — «На проверке». При частичном сбое файлы/черновик могут уже сохраниться, но отправку нельзя считать завершённой |
| 10. Перейти в список → статус «На проверке» → открыть1915 снова; reload | Тот же текст и3 файла, статус «На проверке». В «К выполнению» эта работа больше не должна оставаться. Одно задание не превращается в несколько ответов |
| 11. Добавить к тексту `Дополнение после отправки.` → «Сохранить изменения» | Статус остаётся «На проверке», тот же рабочий ответ. После повторного открытия текст с дополнением. До проверки также можно добавить, заменить или удалить файл; итоговую версию получит преподаватель |
| 12. Список → «Проверено» →1916 | Отдельная заранее подготовленная работа: «Проверено», 0 из5 и «Синтетическая проверка.». Текст/файлы только для чтения. Затем1919:5 из5. В вашем1915 проверка сама не появится |

**Последний шаг не является проверкой только что отправленного1915.** Teacher UI пока не позволяет завершить цикл. Чтобы сделать именно его checked, нужна отдельная согласованная подготовка через API fixture; этот маршрут её не выполняет и не предлагает вам вводить токены/команды. Существующие1916/1919 позволяют сейчас принять вид результата и запрет редактирования. В них может не быть текста/фото: seed подготовил статус/оценку/комментарий, а не полноценное решение с вложениями.

### Где искать статусы и историю

- В списке есть фильтры «К выполнению», «На проверке», «Проверено», «Все статусы». Отдельной вкладки «Черновики» нет: черновики входят в «К выполнению».
- На странице ДЗ различаются «Решение ещё не сохранено» и «Черновик · ещё не отправлен». Общая карточка ДЗ эти два состояния подписывает одинаково «К выполнению».
- После успешной отправки и в карточке, и в форме — «На проверке»; после сохранения изменений статус не откатывается.
- Оценка/комментарий — на странице проверенного ДЗ; последний результат также показывается в «Мой день».
- «Исторические попытки» раскрываются отдельно; текущий ответ находится выше. Пустая история допустима, каждое сохранение не создаёт историческую попытку.
- «Сроки и переносы задания» показывает историю размещения/дедлайнов. В этом seed есть первоначальное задание, но нет реального сценария переносов. «До следующего занятия» при отсутствии даты — ожидаемо.

## 6. Какие действия действительно меняют данные

| Действие UI | Последствие |
|---|---|
| Открыть раздел, курс, урок, ДЗ; фильтр/неделя/страница списка | Чтение API и изменение адреса/навигации. Ответ не создаётся |
| Открыть/закрыть фото/PDF, масштаб, страница PDF, скачать | Чтение защищённого файла; скачивание создаёт копию на вашем устройстве, не новое решение |
| Печатать текст, выбрать фото, выбрать замену | Меняет память вкладки/очередь; без сохранения не обещает сохранность на сервере |
| «Убрать из очереди» | Убирает ещё не сохранённый выбор; не удаляет другой серверный файл |
| «Сохранить черновик» | При первом сохранении создаёт рабочий draft, дальше изменяет его текст и последовательно загружает выбранные файлы/замены |
| Подтверждённое «Удалить файл» | Немедленно удаляет выбранное вложение ответа через API, остальные сохраняет. Это не просто визуальное скрытие |
| «Отправить решение» | Сохраняет незавершённые изменения и затем переводит draft в submitted. Backend создаёт событие для преподавателя. Внешней отправки во ВК/email нет |
| «Сохранить изменения» после отправки | Изменяет тот же submitted ответ до проверки. Преподаватель при следующем чтении видит актуальное решение; повторного уведомления об отправке и нового рабочего ответа нет |
| «Перечитать список файлов» / повтор чтения | Получает серверное состояние; не заменяет явное сохранение локального текста. После спорного запроса сначала читать, потом решать о повторе |
| «Остановить загрузку» | Останавливает ожидание/передачу, но сервер мог успеть записать файл. Требуется перечитать, а не считать отмену откатом |
| «Выйти» | Реально завершает сессию и очищает локальную несохранённую работу после предупреждения. Уже сохранённый ответ не удаляет |
| Принять приглашение/сбросить пароль | Реально меняет аккаунт, ссылка одноразовая; это отдельная необязательная проверка |
| Действия в образце `/__ui` | Демонстрация локальных переходов; не выдаёт ДЗ и не ставит оценки |
| Загрузить/заменить/удалить в `/__ui/files` | Реальные операции API для отдельного `files_student`; подписанные ниже примеры ошибок — демонстрационные |

«Преподаватель получил решение» здесь означает: backend подтвердил submitted, работа доступна в его API очереди, событие создано. Это не означает, что человек уже открыл её, и не означает готового teacher UI. Draft в очередь проверки не отправлен. До checked разрешены текст, append, замена и удаление своих файлов. После checked нельзя изменить текст/файлы/оценку/комментарий или удалить попытку; сценария возврата на доработку нет. Архив дополнительно закрывает запись даже непроверенного ответа.

## 7. Сохранность — что переживает какие действия

| Событие | Только набранный текст / выбранные фото | Серверный черновик | Отправленное решение | Проверенный результат |
|---|---|---|---|---|
| Отменить уход в предупреждении | Должны остаться в форме | Остаётся | Остаётся последняя сохранённая версия | Остаётся |
| Подтвердить уход с несохранённой формой | Локальная работа удаляется; возврат не обещает её | Остаётся ранее сохранённое | Остаётся ранее сохранённое | Остаётся |
| Переходы после завершённого сохранения, повторное открытие | Нечего терять; несохранённые дополнения требуют guard | Читается с сервера | Читается с сервера | Читается с сервера |
| Reload / закрытие вкладки | Не сохраняется надёжно; browser prompt зависит от браузера. Не подтверждать потерю ценных данных | Читается после входа | Читается после входа | Читается после входа |
| Явный выход / смена аккаунта | Очищается; не должна появляться у другого пользователя | Остаётся у исходного ученика | Остаётся у исходного ученика | Остаётся у исходного ученика |
| Истекла сессия, повторный вход тем же пользователем поверх страницы | Память сохраняется, пока вкладка жива; не делать reload | Остаётся | Остаётся | Остаётся |
| Перезапуск текущего synthetic seed/preview | Не обещается восстановление | Старые записи DB могут остаться, но новый аккаунт их не видит | То же; старые файлы не гарантированы | То же; новые fixture результаты — другие записи |

В браузере нет периодического автосохранения текста/фото и нет надёжной offline очереди. Не хранить их в localStorage/IndexedDB — намеренная граница реализации. Верхний DraftProvider помогает держать память вкладки и переавторизацию; это не резервная копия. «Отмена» в предупреждении оставляет форму; «Уйти» явно разрешает отбросить локальное состояние.

Фактическое хранилище preview: PostgreSQL test-контейнера `lgg-test-postgres-1`, отдельная база `lgg_test`, порт55432; PostgreSQL хранится в Compose named volume `lgg-test_postgres_data` (ключ `postgres_data` в compose.test.yaml); media — OS temporary `lgg-test-media-preview-*`. Точный **текущий** каталог находится в поле `files.media_root` локального файла входа; не публикуйте весь JSON ради этого поля. Файлы читаются через защищённое API, не по публичной ссылке на каталог.

Reload frontend не удаляет DB/media. Но запуск `scripts/t14e_preview.py` создаёт новый namespace, новый временный media root и перезаписывает файл входа. Он не восстанавливает владельцу прежние ответы автоматически. Даже если старые строки остаются в test DB, нельзя обещать чтение старых файлов новым backend root. Pytest использует ту же выделенную test DB и способен сбросить fixtures: поэтому его и preview не запускают одновременно. Очистка temporary OS каталогов, удаление test volume или reset уничтожают соответствующие данные. Сейчас нет обещания production persistence, резервной копии и восстановления; приёмочные файлы не должны быть единственным экземпляром чего-либо важного.

Dev8018/55431 и его media не использованы. Обычный dev Compose volume не является хранилищем этого synthetic preview.

## 8. Телефон 360px — отдельный проход

На компьютере: откройте инструменты разработчика браузера → режим устройства → ширина360 CSS px, высота примерно800, масштаб страницы100%. Это эмуляция узкого экрана, а не проверка настоящей экранной клавиатуры. На физическом телефоне адрес127.0.0.1 указывает на сам телефон; текущие loopback-сервисы так недоступны. Для этого маршрута используйте эмуляцию, не открывайте сервер в сеть и не меняйте dev настройки.

1. Войдите `read_student` → «Мой день». Должен быть один читаемый столбец; заголовки и действия без обрезки, нижнее меню не закрывает кнопки. Прокрутите страницу полностью.
2. Нижнее меню → «Расписание». Выберите16 октября, затем17 и18 внутри недели12–18 октября. Видны только занятия выбранного дня; пустой день коротко объяснён. Переключение недели/«Сегодня» и переходы к уроку/курсу доступны касанием.
3. Урок1615 → PDF. Проверьте вторую страницу/масштаб/скачивание и закрытие. Фото смотрите через файловую площадку либо после загрузки в ДЗ. Кнопки должны помещаться, изображение не обрезается без возможности просмотра.
4. Через «Ещё» найдите курсы и архив. Откройте архивный PDF. Убедитесь, что архив понятен и не предлагает отправку.
5. Выйдите → `answer_student`. Повторите сценарий раздела5 на чистом1918, чтобы не пытаться сделать отправленную1915 «пустой». Выберите3 фото обычным picker без drag; после сохранения/перезагрузки добавьте4-е, замените и удалите. Все действия должны быть достижимы прокруткой, статус не перекрыт нижней панелью.
6. Введите длинный synthetic текст, попробуйте уйти → «Отмена». Форма и фото остаются. После отправки откройте результат1916: оценка/комментарий и запрет редактирования читаемы.
7. Отдельно можно включить zoom200% в обычном desktop браузере: текст, формы и кнопки должны оставаться доступными. Записывайте устройство/браузер/масштаб. WebKit, физические iOS/Android и полный набор экранных клавиатур сегодня не проверялись.

## 9. Необязательные дополнительные проверки

### PDF/фото и техническая площадка

Войдите `files_student` → [файловая площадка](http://127.0.0.1:5173/__ui/files) → «Открыть тестовые файлы». Откройте `math.pdf`, вторую страницу, масштаб, скачивание; затем `notebook.webp`, масштаб мелких дробей, Escape. Повторно откройте: исходные файлы остались. Замены/удаления здесь реальные — для проверки чтения их выполнять не обязательно. Фраза площадки «Учебный кабинет ещё не подключён» относится к старой технической демонстрации; актуальный ученический кабинет находится в `/student`.

### Приглашение / восстановление пароля

«Забыли пароль?» на входе показывает инструкцию обратиться к администратору, не отправляет email. Публичной самостоятельной регистрации нет.

Если хотите отдельно проверить активацию/сброс: возьмите URL только из `invite.url` или `reset.url` текущего локального файла; здесь он не дублируется. Срок seed-ссылок — один час от создания, каждая одноразовая. Обычный `/activate` без fragment недостаточен. Введите новый synthetic пароль дважды → успех → обычный вход соответствующим username. Новый пароль теперь ваш, JSON после такого действия не обновляется автоматически. Повтор той же ссылки должен дать понятное состояние недействительной ссылки. Если ссылка уже истекла, не перезапускайте preview ради неё посреди приёмки — пометьте «не проверено: ссылка истекла».

### Ошибка сети — безопасно и только по желанию

Используйте отдельное ещё не отправленное1917 и только synthetic текст/фото. Не останавливайте backend, Docker и не меняйте DB.

1. В инструментах разработчика откройте Network → Offline. Откройте ещё не посещённую страницу: ожидается локальная ошибка чтения и «Повторить», а не ложная пустота. Если данные взяты из памяти, это не доказательство успешного запроса.
2. Верните Online → «Повторить»: содержимое должно загрузиться. Для проверки сохранения на уже открытой форме сначала наберите текст, включите Offline, нажмите сохранить: не должно быть ложного успеха, текст остаётся в живой вкладке.
3. Верните Online. Если показано «Сохранение не подтверждено», сначала перечитайте серверное состояние соответствующей кнопкой, затем сравните текст/файлы и только после этого повторяйте осознанно. Не нажимайте отправку много раз.
4. Всегда верните Network → Online после проверки. Потеря сети после записи на сервере не воспроизводится этим способом достоверно; не считать её проверенной. Примеры timeout/quota/409 ниже в галерее показывают вид сообщения, но не реальную такую ошибку.

### Конфликт версий — две вкладки одного ученика

Простыми словами: вы открыли старую копию ответа, а другая вкладка уже его изменила. Сервер должен остановить перезапись новой работы старой.

1. Под `answer_student` сохраните synthetic черновик1917. Откройте тот же адрес во второй вкладке, дождитесь загрузки обеих.
2. В первой вкладке наберите `Локальный вариант А`, **не сохраняйте**. Во второй — `Серверный вариант Б` → сохранить. Не делайте reload первой вкладки.
3. В первой нажмите сохранить. Ожидайте сообщение конфликта/предложение перечитать и сравнение с сервером; локальный текст А не должен пропасть. После чтения сервер должен содержать Б. Если фоновые обновления уже показали конфликт до нажатия — это тоже допустимая защита.
4. Скопируйте нужный synthetic текст в отдельную заметку, перечитайте актуальное состояние и выберите дальнейшее действие осознанно. Не ожидать автоматического объединения двух текстов.

Не нужно пытаться одновременно ставить оценку через API: teacher UI нет, fixture гонки из прошлых автотестов не являются шагом вашей ручной приёмки.

### Несохранённая работа / повторный вход

На1917 наберите synthetic строку → «Выйти» → сначала отмените: текст остаётся. Затем подтвердите выход, войдите тем же аккаунтом: должен остаться только последний **серверный** вариант, локальная строка исчезает. Под другим аккаунтом она не появляется. Аналогично можно проверить reload/закрытие на одноразовом тексте: браузер может показать собственное предупреждение, после подтверждения восстанавливается только серверное. Не используйте реальные ответы для такого опыта.

## 10. Чек-лист владельца

В «проверил» поставьте дату/галочку; в «работает» — да/нет/частично/не проверял. Все клетки намеренно пусты. Отсутствующую функцию отмечайте «нет UI», а не «ошибка готового».

### Основной проход всего готового

| Проверка | Проверил | Работает | Замечание |
|---|---|---|---|
| Актуальный вход read_student и выход | | | |
| Мой день: занятие, задачи, результат, курсы | | | |
| Урок → PDF2 страницы → скачать → назад | | | |
| Расписание: неделя, день, МСК, урок/курс | | | |
| Два активных курса и архив только для чтения | | | |
| answer_student: весь цикл черновик → отправка → изменение | | | |
| Подготовленные результаты0/5 без редактирования | | | |
| Пустой кабинет read_empty | | | |
| Teacher/admin: вход работает, кабинет честно отсутствует | | | |
| Повтор основных действий на360px | | | |

### Подробные проверки по разделам

| Проверка | Проверил | Работает | Замечание |
|---|---|---|---|
| Вход: показать/скрыть пароль, Enter, понятная ошибка без многократных попыток | | | |
| Прямой URL урока после повторного входа/reload | | | |
| Назад возвращает к прежнему списку/фильтру | | | |
| Расписание: предыдущая/следующая/Сегодня, пустой день | | | |
| Scheduled/completed/cancelled различимы; «Уже прошло» не стирает данные | | | |
| Курсы: активные/архив/все; нет чужих курсов | | | |
| Геометрия: пустые материалы без teacher-кнопок | | | |
| Архив: открыть PDF/ДЗ, нет записи | | | |
| PDF: страница2, масштаб, скачать, Escape, возврат фокуса | | | |
| Фото: открыть каждое, увеличить, закрыть, снова открыть | | | |
| ДЗ1915: открытие не создало ответ | | | |
| Текст+3 фото до сохранения; отмена ухода сохранила всё | | | |
| Серверный черновик: reload сохранил текст+3 фото | | | |
| 4-е фото добавилось, первые3 остались | | | |
| Замена ровно одного файла сохранила соседние | | | |
| Отмена удаления безопасна; подтверждение удалило только один | | | |
| Отправка закончилась «На проверке», запись найдена через фильтр | | | |
| Правка submitted сохранилась без второй работы | | | |
| Проверено0 и5: комментарий, нет редактирования/файловых операций | | | |
| Исторические попытки: текущий ответ не дублируется; пустота объяснена | | | |
| Сроки/переносы: открываются, null не превращается в1970 | | | |
| Фильтры ДЗ: статус, курс, архив/все, просроченные, сброс | | | |
| Размер страницы20/50; на7 записях следующей страницы может не быть | | | |
| Профиль/уведомления/конспекты соответствуют заявленной границе | | | |
| Общие403/404 и понятный возврат | | | |
| Desktop клавиатура Tab/Enter/Escape, видимый фокус | | | |
| 360px: нижнее меню/Ещё, день, длинная форма, кнопки без обрезки | | | |
| Повторный вход возвращает серверные данные исходного ученика | | | |

### Необязательные сложные сценарии

| Проверка | Проверил | Работает | Замечание |
|---|---|---|---|
| Offline чтение → Online → повтор | | | |
| Offline сохранение не объявлено успешным; локальный текст остался | | | |
| Две вкладки: конфликт сохраняет локальный текст | | | |
| Reload/закрытие с одноразовым несохранённым текстом | | | |
| Выход с предупреждением: отмена и подтверждение | | | |
| Активация/сброс по ещё действительной локальной ссылке | | | |
| Показ ошибки повторной/просроченной ссылки | | | |
| Desktop zoom200% | | | |
| Техническая площадка: PDF/фото; примеры ошибок отделены от реального API | | | |

## 11. Как сообщать замечания

Для каждого замечания отдельный короткий блок:

```text
URL: (адрес страницы, без токенов и приватного fragment)
Роль / ключ аккаунта: student / answer_student (без username/пароля)
Устройство: desktop или360px; браузер; масштаб
Что сделал: 1… 2… 3…
Что ожидал:
Что получилось: точная подпись/статус, какие данные остались или исчезли
Повторяется: всегда / иногда / один раз
Скриншот: приложить экран без файла входа, паролей и приватных ссылок
```

Можно отдельно написать «непонятно, что нажать» или «визуально не нравится» — это тоже результат приёмки. Не нужно самостоятельно диагностировать API. Отметки в чек-листе ставите вы; замечания не означают автоматического разрешения на исправления или следующий этап.

Источники для сверки фактов: [STATUS](STATUS.md), [T14a](tasks/T14a.md), [T14b](tasks/T14b.md), [T14c](tasks/T14c.md), [T14d](tasks/T14d.md), [T14e](tasks/T14e.md), [T14f](tasks/T14f.md), [T15a](tasks/T15a.md), [PRODUCT §4–8](PRODUCT.md), [ARCHITECTURE A06/A09/A11–A13](ARCHITECTURE.md), [DESIGN](../../DESIGN.md), релевантные записи16.10 в [SESSION_LOG](SESSION_LOG.md). Более ранние формулировки «frontend отсутствует» в GPT и «вход ещё не подключён» в старых разделах карточек — исторические; текущая карта выше основана также на router/компонентах и текущих API GET.


### 16.10.2026 · комплексный технический чекап текущего состояния
- [T15b: inventory/evidence](tasks/T15b.md#технический-чекап-текущего-состояния-16102026): удалены только Finder metadata и проверенный generated JSON-дубль; прежний diff/untracked/user data сохранены, новых функций/установок/Git/publication нет.
- Вводные README/rules/PRODUCT/DESIGN/A10/A11/T14 headers согласованы с кодом; опасный stale proxy8018 исправлен на synthetic8019. STATUS и ручной маршрут сокращены/актуализированы, полные прежние версии сохранены выше; приёмки и NOT RUN открыты.
- Guard actual test engine/session/SQL/temp-media PASS; preview остановлен до полного default pytest **647 PASS/525.46s**. Dev8018/55431 и UNKNOWN DB не затронуты, новых migrations нет.
- Node .local-runtime: unit58/quality/types/tokens/build/npm ls PASS, premium strict0; AST325/links/diff PASS. Chromium сначала34 PASS/2 FAIL; checkbox transition, first-save test race и week-boundary ожидания расследованы, [evidence T15a](tasks/T15a.md#чекап-t15a3-checkbox-уведомлений-16102026), финальный общий **36 PASS/2.1m**, desktop360 screenshots просмотрены.
- Fresh synthetic5173→8019→test55432/temp-media оставлен для приёмки: финальный browser login/list→ученик→PDF/mobile360 PASS, вход ignored0600 t15b1-login.txt/JSON. Далее ручная T15b.1/T15a.2/.3, затем D11/T08b только новым поручением; reminders/history/«Мой день» остаются планом, недели истории предложением.


### 16.10.2026 · D11 согласован, без реализации
- Владелец ответил «все согласую» на полный пакет регулярного расписания и нормы; принят [D11](DECISIONS.md#d11--регулярное-расписание-и-недельная-норма-принято-16102026).
- PRODUCT §5/ARCHITECTURE A05/[T08b](tasks/T08b.md)/TASKS/GPT/STATUS синхронизированы:1–12/default4, ручное продление, исключения/остановка, атомарность, недельная норма/история.
- Только документация; код/миграции/окружение не менялись. T08b TODO, проверки реализации NOT RUN; ручные T15a.2/.3/T15b.1 и исторические NOT RUN открыты.
- Далее отдельное поручение на локальную T08b. D12 и правила напоминаний до T15b.2 открыты; commit/push/deploy/установок нет.


### 18.10.2026 · запуск платформы по запросу владельца
- Прервана дальнейшая работа над T08b для просмотра: [текущий факт и незавершённые проверки](tasks/T08b.md#ход-локальной-реализации--запуск-preview-18102026), статус IN PROGRESS, не VERIFY.
- Guard фактических engine/session/SQL/temp-media PASS; upgrade head на lgg-test PASS; fresh seed; localhost5173/8019 запущены без установок, dev/UNKNOWN не затронуты.
- Входы teacher/read/answer/profile/password/empty/admin и scoped API через frontend proxy PASS; ignored0600 helper обновлён без вывода паролей. Admin только session shell, teacher schedule/UI regularity ещё нет.
- Приёмки T15a.2/.3/T15b.1 и historical NOT RUN открыты. DB tests не запускать одновременно с preview; commit/push/deploy не выполнялись.
- Browser smoke: установленный Chrome, teacher/student login+render PASS; стартовая страница открыта в панели. Автоматическая приёмка владельца не закрывалась.
# AST Index · 19.10.2026

По явному запросу владельца установлен официальный v3.56.0 darwin-arm64, SHA256 PASS.
Локальные бинарник/cache в ignored .local-runtime; wrapper/config и правила AGENTS.
Rebuild/update/stats, Python/TS symbol, outline/refs PASS:416 файлов,9791 символ.
Подробности: [AST_INDEX](AST_INDEX.md); БД/продукт не менялись, commit/push/deploy нет.

### 19.10.2026 · T08b backend gate пройден, VERIFY до UI
- [Карточка: команды/результаты/остаток](tasks/T08b.md#финальные-проверки-backend--19102026): corrected fixture is_deleted; deferred avatar cleanup import removes standalone collection cycle. Старые FAIL/ERROR сохранены.
- Guard actual engine/session/SQL/temp-media PASS; scoped112 PASS/127.77s, standalone44 PASS/1.20s, полный default675 PASS/582.22s; migration clean/prior/rollback в общем suite, upgrade head/check PASS.
- Source API types/tsc/compileall/diff/docs links PASS, frontend58 PASS/2.36s. T08b VERIFY: backend gate .2 пройден, UI4 weeks/move/extend/360/keyboard/unknown POST NOT RUN; прежние ручные приёмки/NOT RUN открыты.
- Новые AGENTS/AST_INDEX использованы: update/symbol/outline/refs,23 строки outline vs431 сервиса; [польза/границы](AST_INDEX.md#применение-в-t08b--19102026), общего процента экономии не измеряли. Владелец принял правила напоминаний .2, PRODUCT§6/T15b обновлены без кода .2.
- После tests fresh synthetic5173→8019→55432 восстановлен, входы ignored0600 обновлены19.10, login/scoped API PASS; media временные. Далее T15b.2 backend→UI; D12 открыт. Без commit/push/deploy/установок, внешний Git/dev/UNKNOWN не менялись.

### 20.10.2026 · T15b.2 backend→UI, VERIFY
- По явному local разрешению реализованы нормы/недельные агрегаты/recipient reminders, teacher calendar/regular preview/receipt recovery, урок/материалы/ДЗ/долг; [карточка с файлами/диагностикой](tasks/T15b.md#t15b2--локальная-реализация--1920102026). .3/.4/D12 не затронуты.
- Guard actual DB/engine/session/SQL/temp-media PASS, preview перед DB tests остановлен; backend681 PASS/570.39s, final scoped102 PASS/112.27s, standalone44 PASS. Schema reset отклонён auto-review; вместо него exact metadata/defaults/enums read-only PASS→revision stamp без удаления данных→upgrade/check PASS.
- Frontend59 PASS, typecheck/lint/format/API types/tokens/build PASS, premium0. Последний full Chromium38 PASS/1 FAIL; реальная first-save refetch/blocker race исправлена и scoped1 PASS; final teacher filter/back/norm1 PASS, отдельный teacher4 PASS. Общий39 после последних fixes NOT RUN; прежние FAIL/NOT RUN сохранены.
- Fresh5173→8019→guarded55432 и helper/JSON0600 восстановлены20.10; browser login/calendar/lesson/protected PDF/360 PASS, media temporary. Private helper теперь обновляется каждым seed автоматически; planning actor изолирован без ослабления rate limits.
- Ручные T15a.2/.3/T15b.1/T08b/T15b.2 ожидают, WebKit/device/production/restore и historical NOT RUN открыты. Без Git/publication/install/reset/stash; внешняя папка/dev/UNKNOWN не менялись. Далее ручная .2 в этом чате, не переход к .3/.4.

### 20.10.2026 · T15b.2 — дневная сетка
- По запросу владельца преподавательский календарь ограничен08:00–22:00 МСК; PRODUCT §5 актуализирован, дизайн сохранён.
- Typecheck/lint PASS; Chrome real API desktop/mobile360 PASS; sandbox launch ERROR→вне sandbox PASS. DB-тестов не было, preview продолжает работать.
- [Подробности и остаток](tasks/T15b.md#t15b2--часы-преподавательского-календаря--20102026): ручные приёмки и исторические NOT RUN открыты; commit/push/deploy/install нет, .3/.4 не начаты.

### 20.10.2026 · T15b.2 — пять скринов и фокус MVP
- [Карточка: исправления/диагностика/остаток](tasks/T15b.md#t15b2--замечания-владельца-по-пяти-скринам--20102026): календарь/единый поиск/материалы/недобор упрощены, признаки готовности отделены от due reminders.
- Guard SQL/engine/session PASS; DB pytest/reset не запускались.10 ночных fixture уроков архивированы штатным API; preview с прежними accounts/media восстановлен, helper0600 обновлён.
- Frontend59 PASS/build PASS, real API smoke desktop/mobile360 PASS; teacher2 PASS/1 FAIL→regular scoped1 PASS/4.2s, premium0/detect[]. Исторические FAIL/NOT RUN и ручные приёмки открыты.
- AGENTS/GPT/PRODUCT/DESIGN: доводить MVP, говорить об избыточных идеях и откладывать расширение. T15b.3/.4 не начаты; без commit/push/deploy/install.

### 20.10.2026 · Основной MVP без лишних функций
- По запросу владельца [TASKS](TASKS.md#фокус-mvp--решение-владельца-20102026) и PRODUCT задают приоритет законченного учебного пути обеих ролей; очередь/проверка T15b.3 остаётся следующим функциональным пробелом, без разрешения реализации.
- AGENTS/GPT: прямо отделять нужное сейчас от отложенного; простой расширяемый код без временных обходов и гипотетических движков. DESIGN: интуитивность и осмысленные цветовые акценты входят в MVP.
- Только документы; diff/внутренние ссылки проверены. Код/БД/preview не менялись, runtime tests не запускались. Открытые приёмки и NOT RUN сохранены; commit/push/deploy/install нет.


### 20.10.2026 · T15b.3 — local code, runtime BLOCKED
- По явному разрешению реализованы queue/context batch→review exact version/grade0–5→checked result и MyDay; стартовый home сохранён до полного gate. [Карточка: код/ошибки/остаток](tasks/T15b.md#t15b3--локальный-код-и-блокер-runtime--20102026).
- Frontend68 PASS (до jsdom fonts test-platform fix67 PASS/1 FAIL), standalone46 PASS без DB; typecheck/lint/format/API types/tokens/build PASS, premium0. Подготовленные real-API review E2E NOT RUN.
- Actual SQL guard ERROR PermissionError/Docker denied; browser refused5173 и vite listen EPERM. DB pytest/reset/seed/остановка backend не выполнялись; preview восстановить нельзя в текущих правах. Конкретное сохранение отправленных ответов не прочитано; пропажа не утверждается.
- Прежние accounts/owner lessons/media и private JSON не заменены; helper0600/git-ignore обновлён с отметкой непроверенных входов. Исторические FAIL/NOT RUN и все ручные приёмки сохранены; .3 IN PROGRESS, не DONE/VERIFY; .4/D12/commit/push/deploy/install нет.

### 20.10.2026 · Продолжение T15b.3: ограничения среды подтверждены
- Повтор actual SQL guard → PermissionError; Vite5173 → listen EPERM. Runtime/real API gate остаётся BLOCKED, без DB tests/seed/reset.
- Повтор frontend68 PASS, standalone46 PASS без DB, typecheck PASS; существующая state model review просмотрена без изменений кода.
- Accounts/owner lessons/media и непроверенные private входы сохранены; preview восстановить в текущем профиле невозможно. [Остаток и evidence](tasks/T15b.md#продолжение-20102026--повторная-диагностика-runtime); приёмки и исторические FAIL/NOT RUN открыты.

### Повторный запрос T15b.3 · 20.10.2026, 22:47 МСК
- Повтор actual SQL preflight ERROR PermissionError; Vite5173 ERROR listen EPERM. Сквозной runtime gate BLOCKED.
- Frontend68 PASS/3.09s, typecheck PASS, standalone46 PASS/2.51s без БД; AST update/outline выполнены.
- Код/данные сохранены; DB tests/reset/seed не запускались, preview не восстановлен, private helper0600 актуализирован. [Evidence и остаток](tasks/T15b.md); ручные приёмки/исторические FAIL/NOT RUN открыты.


### 20.10.2026 · T15b.3: real API путь завершён локально, VERIFY
- Runtime доступен через разрешённое повышение прав; actual SQL/project guard PASS. Реально сохранённый submitted ответ найден, пропажа не подтверждена.
- Обе роли review/MyDay3 PASS, auth/home2 PASS; PostgreSQL149 PASS, frontend68/standalone46 PASS, static/build/premium0 PASS. Teacher home теперь «Мой день».
- Preview остановлен перед DB tests; private snapshot восстановлен с точным совпадением26 таблиц/sequence.109 missing media восстановлены из старых roots по SHA256 без overwrite. Аккаунты/owner занятия сохранены.
- Preview5173→8019 восстановлен, verified private helper0600 обновлён. [Файлы, промежуточные FAIL, команды и ручной чек-лист](tasks/T15b.md#t15b3--сквозной-runtime-gate-пройден--20102026). Приёмки и historical NOT RUN открыты; .4/commit/push/deploy/install не выполнялись.


### Пустой preview по запросу владельца ·20.10.2026
Владелец явно попросил удалить все тестовые данные и начать ручную проверку с нуля.
После actual SQL/project guard PASS остановлены только preview8019/5173; очищены
все domain tables guarded lgg_test (schema/Alembic сохранены), создан один активный
учитель `teacher`. Ученик намеренно не создан: владелец добавит его сам через UI.
Прежние52 synthetic media roots и private snapshot удалены по этому новому запросу;
новый пустой media root выделен отдельно, dev8018/55431 не затронут.
Первый bootstrap import FAIL до commit/rollback; после регистрации db_models повтор PASS.
Preview восстановлен, private helper0600 заменён новым входом; старые planning
credentials больше недействительны. Исторические тестовые evidence/приёмки сохранены.
Финальный browser smoke PASS: новый вход, students/courses/lessons/queue/reminders total0, форма «Добавить ученика» открывается; ученик не создавался.


### 21.10.2026 · Учебный UX по11 скринам, VERIFY
- По явному запросу упрощены файлы/календарь/статусы/MyDay/notifications/feedback; согласованы auto-completed, reminders только finished и несколько teacher PDF/фото. Миграция11ffc0656a8a additive, grade0–5/exact version/checked immutable сохранены.
- PostgreSQL232 PASS/1 FAIL(test URL)→targeted1 PASS; preview остановлен, actual guard/snapshot/точный restore всех rows/sequence/media PASS. Owner accounts/5 lessons/media сохранены; отдельные UX21 fixtures после browser убраны.
- Real API обе роли3 PASS, отдельно toast/auto-completed1 PASS; frontend69/standalone46 PASS, static/build/premium0/detect[] PASS. Intermediate contrast/locator/format FAIL сохранены в [T15b](tasks/T15b.md#учебный-ux-по11-скринам-владельца-21102026).
- Preview5173/8019 и прежний teacher вход проверены, private helper0600 актуализирован. GPT сокращён, STATUS current/history разделены, PRODUCT/ARCHITECTURE/DESIGN актуальны. Приёмки/historical NOT RUN открыты; .4/commit/push/deploy/install нет.

### 21.10.2026 · Расписание ученика без архивного фильтра
По уточнению владельца убраны «Активные / Архив / Все». Запрос занятий всегда
использует `view=active`, включая переход по старой ссылке с `view=archive/all`.
Архив остаётся в курсах. Typecheck, targeted ESLint/Prettier PASS;
новый browser gate и DB-тесты для этой правки NOT RUN, данные не менялись.

### 21.10.2026 · Материалы рядом с отправкой ДЗ
На HomeworkPage над условием добавлены «Материалы занятия» из существующего
GET /lectures, с lesson_id исходного задания и student_user_id текущего ученика.
Без привязанного занятия блок отсутствует; пустое состояние и ошибки — общие ReadState.
Общий ReadFiles открывает защищённый preview через material-file; DirtyFormGuard
разрешает этот просмотр без сброса текста решения. Палитра/компоненты сохранены.
Typecheck/targeted ESLint/Prettier и frontend69 tests PASS. Real API/browser/mobile
для этого дополнения NOT RUN; ручная приёмка ожидает. Данные/preview не менялись.

## 21.10.2026 — сверка, безопасная уборка и единый план
- Код/API/schema/UI сверены через AST Index + rg; [evidence](CHECKUP_2026_10_21.md), свежие PASS/FAIL/NOT RUN разделены.
- Короткие GPT/README/STATUS, единый [TASKS](TASKS.md); старые версии и приёмка сохранены в history, противоречивые текущие TODO устранены.
- `.dockerignore` исключает приватные frontend артефакты/runtime; исходники/данные/untracked не удалены, функций/установок/Git/deploy нет.
- Frontend69/standalone46/static/build/premium0 PASS; read-only schema/media и teacher Chrome1280/360 PASS. DB/full E2E/ручные gates не закрыты.
- Preview сохранён без seed/reset; private helper0600 актуален. Дальше только T15b.3 VERIFY по новому запросу, затем D12/.4 и очередь TASKS.

### 21.10.2026 · Codex economy setup
- Внедрены локальные defaults Sol medium/Luna high, один worker и автоматическая политика AGENTS.
- Добавлен режим глубокого аудита в WORKFLOW; PROMPTS/SKILLS согласованы.
- Strict runtime config/read и один bounded worker smoke PASS; модель backend worker не аттестована.
- [Файлы, проверки, пределы](tasks/CODEX_SETUP.md); платформа/DB не менялись, T15b.3 VERIFY остаётся.
- Commit/push/deploy не выполнялись; отдельная новая desktop inference-сессия NOT RUN.

### 21.10.2026 · T15b.3 UX-доведение и полный local gate
- [T15b](tasks/T15b.md): после исследования и visual review упрощены shell/иерархия действий/отступы/подписи обеих ролей; палитра и текущие контракты сохранены.
- На физически отдельной synthetic DB полный backend694 PASS; frontend69/static/build/premium strict0; Chrome E2E47 PASS по группам,39 route×width без overflow/axe/JS errors, keyboard8/8. Единый E2E запуск ограничен rate-limit/одноразовыми токенами, исторические FAIL сохранены.
- Исходный preview/volume/media/private helper восстановлены и проверены; через штатное приглашение добавлена отдельная synthetic пара, оба входа PASS. [Ручной маршрут](MANUAL_ACCEPTANCE_T14_T15.md) ожидает владельца.
- MVP/нагрузка/production/CI/физические устройства не объявлены готовыми; T15b.3 VERIFY, дальше D12/.4 после приёмки. Commit/push/deploy/установок нет.

### 21.10.2026 · Ручной маршрут T15b.3, первый шаг
- Preview5173/API8019 доступны (HTTP200), private helper существует0600; сбросов/перезапусков не было.
- Владелец подтвердил создание занятия, открытие материала и сохранение ДЗ учителем; замечаний не сообщил.
- [Маршрут](MANUAL_ACCEPTANCE_T14_T15.md) и [T15b](tasks/T15b.md) обновлены только по этому подтверждению; остальной путь ожидает, T15b.3 VERIFY.
- Код/T15b.4/commit/push/deploy/установки не выполнялись.

### 21.10.2026 · Ручной маршрут T15b.3, отправка ученика
- Владелец подтвердил весь шаг ученика: материал над условием открывается, текст с фото/PDF явно отправлен, после reload ответ/файлы/«На проверке» сохранены.
- Конкретных замечаний не сообщил; [ручная приёмка](MANUAL_ACCEPTANCE_T14_T15.md), T15b и STATUS обновлены по подтверждению.
- Проверка и результат ещё ожидают; T15b.3 VERIFY. Код/T15b.4/commit/push/deploy/установки не выполнялись.

### 21.10.2026 · Ручная приёмка T15b.3 закрыта
- Владелец уточнил, что весь маршрут проходил20.10, и подтвердил оценку/комментарий/открываемый файл проверки у ученика; повтор остановлен.
- T15b.3 DONE локально в карточке/STATUS/TASKS; [ручная приёмка](MANUAL_ACCEPTANCE_T14_T15.md) содержит точный объём и неподтверждённые детали, остальные gates не присвоены автоматически.
- В [D12](DECISIONS.md) записано одно предложение цены за занятие со снимком; решение открыто, T15b.4 TODO.
- Изменены только документы; runtime/данные/дизайн не менялись. Тесты/сбросы/commit/push/deploy/установки не выполнялись.

### 21.10.2026 · D12: цена занятия и компактная сумма недели
- Владелец определил цену занятия у своего ученика (рубли), смену только для новых занятий, один компактный итог недели с историей; потенциальный доход исключён.
- [D12](DECISIONS.md#d12--цена-занятия-и-недельный-итог-принято21102026) принят в этом объёме; технические следствия completed/снимков/исключений отмечены отдельно.
- PRODUCT/DESIGN/T15b/STATUS/TASKS согласованы с решением; прежнее предложение сохранено как история.
- T15b.4 TODO, реализации/тестов/сбросов/commit/push/deploy/установок не было.

### 21.10.2026 · T15b.4: цена, снимок и недельный итог
- По отдельному разрешению реализованы D12 и добавленная владельцем плашка количества всех неотменённых занятий недели; дизайн сохранён.
- Teacher-only цена пары/CAS, снимки single/regular/extend, точный completed aggregate с архивной историей/NULL/0; API и UI связаны.
- PASS: Python621+34+46=701, frontend74 и types/lint/format/types/tokens/build, premium0;4 Chrome сценария по группам1280/360/keyboard/axe. Промежуточные FAIL и NOT RUN — [карточка .4](tasks/T15b.md#t15b4--локальная-реализация--21102026).
- Исходный preview/data/sequence/22 media сохранены, additive e738d7c0dec3/schema diff0, обе роли/4 protected downloads PASS; тесты на2 отдельных disposable volume.
- VERIFY локально, ручная приёмка .4 ожидает; далее T15c.1 по запросу. Commit/push/deploy/установок не было.

### 21.10.2026 · Минимальный расход после T15b.4
- По требованию владельца зафиксированы ошибки чтения/команд/test-helper/readiness и отсутствие измеренной экономии worker — [разбор](tasks/CODEX_SETUP.md#ошибки-t15b4-и-минимальный-расход--21102026).
- AGENTS: самому по умолчанию, worker по ожидаемой общей экономии, scoped чтения/тесты, проверка cwd/контрактов, остановка зависимых команд при ошибке; обязательные gates/сохранность сохранены.
- Только документация; сверка правил/diff, без продуктовых тестов, DB, конфигурационных изменений и Git-действий.

### 21.10.2026 · Архив исключён из недельного учёта
- По прямому уточнению владельца архив занятия/курса больше не входит ни в деньги, ни в количество, ни в unpriced; прежняя трактовка D12 отменена.
- Общий scope активного teacher-календаря, снимки сохранены;6 scoped API PASS на disposable, live Chrome4/1600 ₽/1 без цены.
- Исходные строки/цены/sequence/22 media сохранены, preview возвращён; [подробности](tasks/T15b.md#исправление-учёта-архива-по-уточнению-владельца--21102026). Без миграций/commit/push/deploy/установок; ручная приёмка ожидает.

### 21.10.2026 · T15c.1: административные пользователи
- По отдельному разрешению реализована только .1: list/detail/create/profile, invite/reset, shared links/local detach, account status/quota поверх existing API; дизайн/D12 сохранены.
- PASS: frontend77 + scoped7 после shared Select, types/lint/format/API types/tokens/build, premium0;3 Chrome сценария по группам real API/negative/recovery/1280/360/keyboard/axe. [Файлы, команды, промежуточные FAIL и NOT RUN](tasks/T15c.md#t15c1--локальная-реализация--21102026).
- Guard и preservation PASS: исходные строки,22 media и старые credentials/helpers совпали; только additive synthetic .1, без reset/DB pytest/миграций/перезапуска preview. Отдельный private admin login helper.
- T15c.1 VERIFY, ручная приёмка ожидает; следующее .2 только по запросу. Без commit/push/deploy/установок.


### 21.10.2026 · T15c.2: все курсы, архив и журнал
- По отдельному запросу локально реализована только .2: read-only course/lesson/recipient, restore/history, typed purge, cleanup retry и actor/action audit; принятый дизайн сохранён.
- PASS: frontend77 + scoped shell4, types/lint/format/API types/tokens/build/premium0; единый3 Chrome E2E и39 scoped lifecycle/admin на отдельном disposable volume. [Команды, FAIL→PASS/границы](tasks/T15c.md#t15c2--локальная-реализация--21102026).
- Source container/27 таблиц/sequence/22 media/входы побайтно сохранены и возвращены. Purge только isolated synthetic;7 старых pending files не тронуты. Затем additive2 preview synthetic курса; старые строки/файлы и login/download обеих ролей повторно PASS.
- T15c.2 VERIFY: ручная приёмка ожидает; следующее T16.1 по новому запросу. Без commit/push/deploy/установок.


### 22.10.2026 · admin storage: teacher/student и понятные единицы
- Исправлен нулевой student-budget в teacher карточке: новый admin-only scoped course report/разбивка; student общий usage/limit с пояснением, decimal МБ/ГБ. Existing limits/files не менялись.
- PASS: frontend78/остальные npm checks/premium0;1 Chrome real API storage E2E и4 PostgreSQL scoped quota/report tests;1280/360/keyboard/axe0. [Подробности](tasks/T15c.md#доработка-хранилища-по-запросу-владельца--22102026).
- Тесты на отдельном disposable; source27 таблиц/sequence/22 media/старые входы сохранены. Original teacher1 показывает7423074 bytes/2 курса; source smoke/read/download PASS, без quota/cleanup mutations.
- Ручная приёмка ожидает; следующее T16.1 по новому запросу, без commit/push/deploy/установок.


### 22.10.2026 · приёмка storage и переход к T16.1
- Владелец подтвердил «все окей»: закрыта ручная приёмка только storage teacher/student; другие пункты не отмечены за него.
- STATUS/T15c/MANUAL_ACCEPTANCE обновлены; подготовлен следующий шаг T16.1 и prompt для нового чата. Код/данные не менялись, commit/push/deploy не выполнялись.


### 22.10.2026 · новый приоритет: визуал до общей регрессии
- По прямому запросу владельца добавлена следующая главная задача [T15d](tasks/T15d.md): цвет/композиция/кнопки/понятность существующего frontend, сохранение основы, без backend/API и новых функций.
- Порядок: T15d с targeted UI checks/визуальной приёмкой → T16.1 → T16.2 → подготовка запуска. TASKS/STATUS/GPT/PRODUCT/DESIGN/T16 обновлены.
- Только планирование: код/данные/входы не менялись, commit/push/deploy/установок нет; подготовлен prompt для нового чата.

### 22.10.2026 · T15d: начало обсуждения
- Локальная задача разрешена; последующее уточнение владельца — сначала варианты конкретных страниц, админку пока отложить.
- Прочитаны входные документы/навыки; в browser осмотрены teacher «Мой день» и занятие, включая narrow360. Первичные проблемы и пределы проверки — [T15d](tasks/T15d.md#первичный-осмотр--22102026).
- Код приложения и сохраняемые данные не менялись; preview5173 доступен, backend8019 не перезапускался. Ученика/review/расписание ещё предстоит осмотреть; реализация и targeted gates впереди.

### 22.10.2026 · T15d: исследование реальной нагрузки
- Владелец попросил постоянно сохранять интервью для отчёта/анализа ошибок/UX и логики; подробные факты, недельное расписание, гипотезы и открытые решения внесены в [T15d](tasks/T15d.md#исследование-рабочего-процесса-владельца--22102026).
- Согласованы отдельный тестовый Тимур/17 учеников,24 встречи по55 минут МСК,9 постоянных и15 разовых; только additive создание через API, прежний preview сохраняется.
- ДЗ старшим ссылкой bank-zadach.ru, младшим фото/файл; PDF-конспект после урока/вечером; ответ часто перед уроком, проверка на занятии. Порог5–10 минут, родители/статистика и ВК не реализуются автоматически.
- На момент записи новые учебные данные ещё не создавались; следующие действия и результаты дописывать в ту же карточку. Backend/API/schema и UI не менялись.

### 22.10.2026 · T15d: пример Тимура создан
- Через существующий API добавлены только новые Тимур/17 pupils/17 personal workspaces,24 встречи текущей недели,75 с будущими регулярными продолжениями,9 настоящих серий;7 конспектов/7 ДЗ/2 submitted/3 checked/1 draft.
- PASS guarded исходная сохранность и повторный read-only fingerprint, API календарь/ученики/очередь, protected PDF teacher+student; browser smoke teacher/MyDay/calendar и CSS1280/360 DOM width. Нормальный auth/session bookkeeping исключён из сравнения business rows.
- Интервью, ограничения (оценка0–5, нет реальных ссылок на варианты/подмены timestamps), файлы/команды/промежуточные ошибки и новые UX-наблюдения — [T15d](tasks/T15d.md#заполненный-пример-тимура--22102026).
- Новый вход только ignored0600 `frontend/.artifacts/t15d-login.txt`; browser оставлен в кабинете Тимура. Прежние данные/файлы/квоты/входы/schema сохранены; UI/API код не менялся, визуальные варианты/приёмка и gates ещё впереди. Без commit/push/deploy/установок.

### 22.10.2026 · T15d: цены17 учеников Тимура
- По поручению владельца через существующий API назначены12 цен800 ₽ и5 случайных100 ₽; состав пятёрки/проверки — [T15d](tasks/T15d.md#цены-учеников-тимура--дополнительный-запрос22102026).
- PASS teacher/roster guard, expected-price PUT и17 GET readbacks;75 существующих lesson DTO совпали до/после. По D12 цены применяются к новым встречам, прежние snapshots/итоги не пересчитаны; другие аккаунты и приложение не менялись.

### 22.10.2026 · промпт Astra для teacher UX/UI исследования
- Подготовлен [T15d_ASTRA_PROMPT](tasks/T15d_ASTRA_PROMPT.md): заполненный Тимур, все teacher разделы, сохранённое интервью, frontend/AST, ограниченные внешние UX источники, evidence и конкретный план для Sol.
- Исследование без реализации/данных/backend изменений, один агент, сохранение отчёта по ходу; PROMPTS/T15d/STATUS обновлены. Astra не запускалась, отчёт ещё не существует; гарантии account limit нет.
- Проверки только docs/ссылки/маршруты; приложение и preview не менялись. Без commit/push/deploy/установок.

### 22.10.2026 — T15d teacher UX research
- Осмотрен заполненный кабинет Тимура; сохранён [отчёт](T15d_TEACHER_UX_RESEARCH.md) с17 findings, схемами и пакетамиA–F для Sol.
- Приоритеты: ученик/время, актуальная встреча в workspace, ссылки ДЗ, календарь768, проверка рядом с решением.
- Только исследование/документация; приложение/API/учебные данные не менялись, gates NOT RUN; ограничения browser и непроверенные состояния записаны.
- По указанию владельца завершено без новых проверок. T15d DESIGN REVIEW; следующий шаг — согласовать направление и отдельно разрешить пакетA.

### 22.10.2026 · T15d пакет A — локальная реализация
- По новому разрешению: имя/время ближайшего первыми,5 компактных встреч, очередь и материалы в правой колонке; на768/360 последовательный порядок. [Результат и evidence](tasks/T15d.md#пакет-a--локальная-реализация--22102026).
- PASS unit78/types/lint/format/API types/tokens/build/premium0;1 Chrome real-API read-only сценарий1340/768/360/Tab/axe0 плюс GET loading/empty/503/retry/long names. Историческое ожидание2 работ исправлено на фактический API1, данные сохранены.
- Preview возобновлён штатным guarded helper; backend/API/учебные данные не менялись, seed/reset/DB suites/commit/push/deploy нет. Impeccable context/layout detect PASS/0; designmd CLI NOT RUN, полная device/session matrix остаётся T16.
- Пакет A VERIFY: визуальная приёмка владельца ожидает. B–F не реализованы и требуют отдельного разрешения; DESIGN/STATUS обновлены.

### 22.10.2026 · T15d пакет B — локальная реализация
- По явному запросу: safe HTTP(S) в teacher descriptions, сохранение route state/фильтров/истории/фокуса при PDF/фото; dirty review и композиция A сохранены. [Файлы, evidence, ограничения](tasks/T15d.md#пакет-b--локальная-реализация--22102026).
- PASS unit90/types/lint/format/API types/tokens/build/premium0/Impeccable0;1 read-only Chrome real-API сценарий1340/768/360, teacher + targeted student, axe0/GET503/retry/loading. Учебных writes/JS errors0; harness animation/null-state ожидания исправлены, финальный PASS13.6s.
- Backend/API/БД/данные примера не менялись; seed/reset/DB tests/commit/push/deploy/установок нет. Preview не перезапускался; full device/session/offline/200% и общая регрессия — NOT RUN/T16.
- A/B VERIFY: ручная приёмка ожидает; C–F не реализованы. T15d/STATUS/DESIGN/A13 обновлены.

### 22.10.2026 · T15d пакет C — локальная реализация
- Только календарь/формы встречи: day-view≤1023, desktop7/08–22,72px/subgrid/44px, имя первым/тема/красные материалы/оба перехода; pristine close/dirty protection/pending/unknown/focus. A/B сохранены. [Evidence и ограничения](tasks/T15d.md#пакет-c--локальная-реализация--22102026).
- PASS unit99/22, финальный scoped dirty9/types/lint/format/build; API types/tokens/premium0/Impeccable0.1 read-only Chrome9.4s:1340/1024/1023/768/360, обе недели24, дни/выравнивание/Select/Dialog/keyboard/axe0 + GET fixtures; writes/errors0.
- Исправлены обнаруженные return-focus и контраст названия; harness ожидания исправлены. Guarded preview возобновлён без seed/reset; read-only preservation PASS. Backend/API/БД/schema/данные примера не менялись, mutation suite не запускался.
- A/B/C VERIFY, ручная приёмка ожидает; D–F не делались. Полный device/session/offline/200%/E2E — T16. Без commit/push/deploy/установок; T15d/STATUS/DESIGN обновлены.


### 22.10.2026 · T15d пакет D — workspace и урок
- Только D/§4.3–4.4: ближайшее над past-desc/future-asc, независимые API страницы/архив/отмена/recipient scope; имя/время → конспекты/ДЗ → управление,4 статуса ответа, раскрываемая выдача с text/File. A/B/C сохранены. [Файлы/evidence/границы](tasks/T15d.md#пакет-d--workspace-и-урок--локальная-реализация22102026).
- PASS unit105/24, финальный scoped11/3 (paging/route state/preview/material forms); type/lint/format/build/API types/tokens/premium0/Impeccable0. Финальный B+D Chrome2 PASS/28s:1340/768/360, PDF/фото/dirty, Select/Dialog/axe0, независимые API страницы и GET empty/loading/error; writes/errors0.
- Исправлены contrast ближайшей ссылки, сохранение route state при paging/recipient switch и ожидания harness; настоящий login limit переждан без сброса. Read-only preservation PASS; существующий preview не заменялся, seed/reset/DB mutations не запускались.
- T15d/STATUS/DESIGN обновлены. A–D VERIFY/ручная приёмка ожидает; E/F, реальное сохранение/серии и общий T16 device/session/offline/200% остаются NOT RUN. Backend/API/БД/данные примера не менялись; без commit/push/deploy/установок.

### 22.10.2026 — T15d E: только первый этап §4.5
- Компактные existing фильтры/раскрываемый курс; review имя/класс, открытое условие,2:1 desktop/mobile порядок, Radio.Group0–5/44px, checked readonly.
- ReviewDraft/API/версии/recipient keys/final confirm/multipart прежние; embedded/F/backend/деньги/права не менялись.
- PASS unit109/scoped13, types/lint/format/API types/tokens/build/premium0/Impeccable0; Chrome B+E2/23.1s, D1/14.3s,360/768/1340/keyboard/PDF/photo/Select/Dialog/axe0, writes0.
- Исправлен перехват raw radio клика декоративной рамкой; browser harness ожидания URL/имени img/default-open уточнены. Exact preview fingerprint и прежний preservation PASS, seed/reset/сброса лимитов нет.
- Реальная отправка/DB mutations NOT RUN (disposable target не поднимался), ручная приёмка A–E ожидает. Без commit/push/deploy. [Файлы, evidence, ограничения](tasks/T15d.md#пакет-e--первый-этап-очереди-и-проверки--локально22102026).


### 22.10.2026 — T15d F: вторичная ясность
- Компактные notification rows без enrichment/preload read, profile/avatar/password disclosures с mounted drafts, история перед участием, точные архив/обложка; A–E/общие API сохранены.
- Invitation capability отсутствует в teacher DTO; POST выдачи не использован для probe, новая функция не добавлена.
- PASS unit113/27, types/lint/format/build/API types/tokens/premium0/Impeccable0; финальный F Chrome1/14.2s + E regression1/9.5s:360/768/1340/keyboard/44px/Select/Dialog/axe0, async/drafts/files/return; real writes0.
- Exact E fingerprint до/после PASS; preview не заменялся, seed/reset/сбросов лимитов/реальных mutations нет. Настоящие auth/password/read/upload/membership mutations на disposable и полный T16 NOT RUN.
- T15d/STATUS/DESIGN обновлены; A–D/E1/F VERIFY, ручная приёмка и optional E2 отдельно. Без commit/push/deploy. [Результат/evidence/остаток](tasks/T15d.md#пакет-f--вторичная-ясность--локально22102026).


### 22.10.2026 — T15d E2: встроенный просмотр решения
- По явному запросу E2 завершён локально: shared FilePreviewBody для inline/fullscreen, PDF container fit/page/zoom память, один active viewer; narrow/checked/text-only и ReviewDraft/API/atomic confirm прежние.
- PASS unit118/scoped15, types/lint/format/build/API types/tokens/premium0/Impeccable0; финальный E2 Chrome1/14.3s, E1 regression1/9.7s, B teacher/student1/12.9s, F1/13.3s:1340/1024/768/360/keyboard/Select/Dialog/axe0/drafts/files/return/recovery/cleanup.
- Закрыта гонка late arrayBuffer после unmount, PDF render отменяется при смене вида; tooltip landmark исправлен без axe исключений. Exact preview fingerprint до/после PASS, реальные учебные writes0, seed/reset/сбросов лимитов нет.
- T15d/STATUS/DESIGN/A12–A13 обновлены. A–F/E2 VERIFY/ручная приёмка ожидает; полный teacher проход следующий по запросу, student23.10. Backend mutations/disposable/T16 matrix NOT RUN; без commit/push/deploy. [Файлы/evidence/границы](tasks/T15d.md#пакет-e2--встроенный-просмотр-решения--локально22102026).


### 22.10.2026 — цветовые акценты «Мой день» по owner screenshot
- «На проверку» — #FFF7DB, «Нужно выдать материалы» — #FFF3EB; semantic tokens/theme→CSS, только teacher overview, без смены композиции/поведения.
- PASS unit118/types/lint/format/build/tokens (8 новых пар≥4.57)/premium0/Impeccable0; Chrome1/7.6s:1340/768/360/GET filled-empty-loading-error/keyboard/axe0/writes0.
- Owner сам проводит manual проверку и меняет записи; старый fingerprint не сравнивался. Цветовая работа без mutations/seed/reset/лимитов/commit/push/deploy; оттенки ждут приёмки. [Подробности](tasks/T15d.md#цветовые-акценты-мой-день--отзыв-владельца22102026).


### 22.10.2026 — принят белый фон материалов
- По выбору первого chat-варианта вернули исходный белый panel «Нужно выдать материалы»; жёлтый «На проверку» принят/сохранён, unused peach token/variant удалены.
- PASS types/lint/format/tokens/build/premium0; Chrome1/5.6s:1340/768/360/GET states/keyboard/axe0/writes0. Последний unit118 сохранён, повтор для снятия CSS variant не запускался.
- DESIGN/STATUS/T15d обновлены. Без изменений данных/API/seed/reset/commit/push/deploy.


### 22.10.2026 — материалы занятия: вариант А и мягкие фоны
- После обсуждения владелец выбрал видимые «Не добавлять конспект»/«Не задавать ДЗ», primary справа и красный→зелёный фон секций; not-needed/pending/error/readonly white.
- Canonical picker portaled в header без remount queue/нового upload input; API/flags/dirty/File/readonly прежние. Цвет из подтверждённого GET, без optimistic green; контраст исправлен ink на green.
- PASS unit124/scoped10/types/lint/format/build/API types/tokens/premium0/Impeccable0; Chrome1/7.0s:1340/768/360/axe0/not-needed/reverse/mock upload-issue/PDF/draft/File/readonly/loading/error/unknown, source writes0.
- Owner пример не менялся этой работой; реальные mutations только browser mocks, disposable/server matrix NOT RUN. DESIGN/T15d/STATUS обновлены; manual приёмка ожидает, без commit/push/deploy. [Подробности](tasks/T15d.md#ясность-материалов-занятия--выбор-а-и-мягкие-фоны-22102026).

###22.10.2026 · T15d: видимые кнопки удаления материалов
- Убраны раскрытия управления, удаление размещено под статусом конспекта/ДЗ.
- Мягкий красный фон/рамка, прежние confirmation и ограничения сохранены.
- Typecheck/10 component checks/короткий Chromium1340/360 PASS; writes0.
- По просьбе владельца без полного gate; реальное удаление не проверялось. См. T15d.

22.10 · T15d: «Файл условия (необязательно)» → «Добавить файл»; обновлены связанные тестовые selectors, diff check PASS.

### 22.10.2026 · T15d: действия занятия без раскрытия
- Перенос/завершение/отмена вынесены под ДЗ; архив и серия остаются ниже.
- Заголовки secondaryDisclosure полноширинные с padding и фоном.
- Права, dirty guard, API и диалоги сохранены; typecheck PASS.

Короткая browser-проверка остановилась на login: сохранённая тестовая сессия
больше не авторизует. Повторный вход и mutation не запускались; проверка
нового расположения в браузере остаётся владельцу. Diff check PASS.

### 23.10.2026 · T15d: карточка ученика преподавателя
- По явному разрешению: последнее/мята, месячная история с server pagination,
  файлы/переход в урок, компактное будущее и единые настройки; backend/API прежние.
- Unit129, types/lint/format/build/API types/tokens, premium0/Impeccable0;
  Chrome card + B/E2 PASS, writes0. Ручная приёмка ожидает; результаты — tasks/T15d.md.
- Backend/test337 source и media/schema/входы совпали. DB fingerprint отличается:
  lesson26 cancelled и notification56; источник не установлен, не откатывалось.

### 23.10 · T15d: видимый переход к ученику из занятия
- Кнопка-ссылка в шапке справа, mobile wrap, прежняя скрытая ссылка убрана.
- Recipient/list context/dirty guard сохранены; typecheck/diff check PASS.
- Короткий browser smoke: timeout ожидания ссылки; без новых логинов и mutations.

### 23.10 · T15d: заметные состояния ответа ДЗ в занятии
- Ожидание/draft/submitted/checked разделены; новые заметные review-кнопки.
- Typecheck/15 component/browser1340/768/360 PASS; открытие real review15 и10 PASS.
- Состояния GET-моки, учебных writes0; ручной просмотр поочерёдно ожидает выбора ДЗ.

23.10 · T15d manual submitted: зелёная «Проверить работу» с белым текстом;
исправлен CSS override текста Button-ссылок внутри ready material panel.

23.10 · T15d: submitted-кнопка смягчена до тёплой жёлтой с ink-текстом,
рамкой и hover/active; насыщенный зелёный отклонён владельцем.

23.10 · T15d: владелец принял жёлтую кнопку submitted; показан checked.
Открытие mock результата 5/5 и возврат PASS, сохранённые данные не менялись.

23.10 · T15d checked: мятная кнопка результата с зелёной рамкой/текстом
и hover; текстовый контраст5.08/4.65, переход и данные прежние.

23.10 · T15d checked: исправлено понимание запроса — жёлтой сделана сама
плашка результата, мятная кнопка прежняя. CSS-only, diff check PASS.

23.10 · финальное уточнение checked: сама плашка mint с success-текстом
и зелёной рамкой, отличается от successSurface общей секции ДЗ. Кнопка
результата белая с зелёной рамкой, hover successSurface. Жёлтый только submitted.

23.10 · владелец принял финальный checked («вот щас норм»); последовательный
просмотр4 состояний ДЗ24 завершён. Финальный вид сохранён в DESIGN/T15d/STATUS.

23.10 · подготовлен синтетический student preview Артёма Турова: 33 прошлых
урока, 66 PDF, 29 checked/2 submitted/1 draft/1 unanswered; два будущих урока.
Student GET total33 конспектов/ДЗ, unread4, protected PDF200; PDF render PASS.
Ограничения и данные: T15d_STUDENT_PREVIEW; read-only маршрут Astra:
tasks/T15d_STUDENT_ASTRA_PROMPT. Приложение и backend не менялись.

###23.10 · T15d: оформление работ очереди в «Моём дне»
- Scoped CSS: жёлтые карточки с рамкой/радиусом10 и gap12, исходные ссылки.
- Formatter/diff PASS; короткий browser smoke timeout, runtime не подтверждён.
- Данные/API прежние, mutations/повторных входов не было; ручная приёмка ожидает.

###23.10 · T15d: стабильные месяцы карточки ученика
- Выбор месяца и лента разделены, URL history-strip; стрелки5/3, Back сохранён.
- Последние материалы слегка насыщеннее зелёные, read-only нейтрален.
- Types/6unit/lint/build/tokens/browser1340/768/360 PASS; writes0, приёмка ожидает.

23.10 · T15d student: жёлтая палитра teacher очереди применена к «К выполнению»,
scoped оформление всех заданий, ссылки/API/данные прежние.

23.10 · student «К выполнению»: метка «Долг» — мягкая красная
materialMissingSurface/danger, обычная метка — successSurface/success.
Жёлтые карточки и логика определения долга по placement_kind прежние.

23.10 · завершено owner-интервью по student: PDF viewer, история занятий и
статусы ДЗ — приоритет; остальные замечания и премиальное визуальное направление
сохранены в T15d_STUDENT_OWNER_INTERVIEW. Astra prompt обновлён: самостоятельный
read-only UX/UI проход, экономный ast-index/browser маршрут, отчёт+план для Sol.

23.10 · student UX исследование: [отчёт](T15d_STUDENT_UX_RESEARCH.md),16 findings,
целевые экраны/матрица ДЗ и последовательные пакеты Sol S1–S6. PDF/история/ДЗ —
первые; предмет и enrichment уведомлений требуют отдельного решения.
Read-only browser/code, выбранные360/768/1340; ограничения и drift preview записаны.
Приложение/API/данные не менялись; tests/build/DB/commit/push/deploy не запускались.


23.10 · [T15d S1](tasks/T15d.md#s1--общий-pdf-viewer--локально23102026): общий PDF —
компактная шапка/continuous virtual pages/anchor, единый protected pipeline обеих ролей.
PASS student Chrome38.2s/teacher23.4s, scoped и повтор timeout-групп unit, types/lint/
format/API-types/tokens/build; premium2 ложных Link findings вне S1, Impeccable0.
VERIFY: реальный touch/pinch/browser200%/полный Tab/ручная приёмка ожидают; fixture
ограничения в карточке. Данных/API/S2–S6/seed/reset/commit/push/deploy не касались.


23.10 · S1 follow-up по скриншоту владельца: исправлена узкая полоса fullscreen
(Mantine Content className влиял на inner); style теперь только content.
PASS real ДЗ33/full viewport1920×1080, student+teacher Chrome2/2, types/lint/format/
build. Добавлены geometry assertions1920/1340/768/360; детали — T15d S1 follow-up.


23.10 · S1 по отзыву: прямые minus/plus/download без имени/процентов/popover;
pinch PDF/фото с anchor, native one-finger scroll, исправлена гонка быстрых zoom.
PASS full unit141/141, student Chrome26.1s с CDP touch emulation; реальные телефоны/
Safari/browser200% NOT RUN. Scope/data/API прежние, commit/push/deploy нет. Детали T15d.


23.10 · [T15d S2](tasks/T15d.md#s2--мои-занятия-и-возвраты-23102026): student history,
completed latest/server pages/month strip/course/lazy files/URL/scroll реализованы.
Full unit157 + scoped16/types/lint/format/API types/tokens/build PASS; Impeccable0,
Premium2 прежних false positives. Продолжение/финальные команды — в карточке.
VERIFY: bind5173/8019 и DB read-only preflight запрещены sandbox; real browser/
teacher regression/ручная приёмка NOT RUN. Seed/reset/DB tests/commit/push/deploy нет.


### 26.10.2026 · T15d S4 день/расписание
- Только локальный S4: mobile DOM/Tab, compact nearest/result, scoped course/teacher metadata, student Video join, единые submitted; duration display без изменения расчётов. [Карточка/команды](tasks/T15d.md#s4--день-и-расписание-26102026).
- PASS scoped12/full185(maxWorkers2),types/lint/format/API types/tokens/build,Impeccable0; Premium FAIL2 старых false positives, новых0. Промежуточные harness/lint FAIL исправлены, детали в карточке.
- Chrome student1/13.4s и teacher shared1/2.5s PASS,1340/768/360/Tab/Back/axe0: реальные GET отдельно от HTTP fixtures; учебных writes0. Preview штатно resume5173/8019 с прежним media, ДЗ58 не трогали.
- S4 VERIFY до owner; S2/S3 остаток сохранён, physical/full200%/write E2E/T16 NOT RUN. Без backend/API/данных/seed/reset/установок/Codex config/commit/push/PR/deploy; S5/S6 не начаты.


### 26.10.2026 · student homework workspace
- По новому owner запросу: desktop документы слева/ответ справа, auto inline/collapse, narrow compact, крупное кликабельное условие в уроке/ДЗ, scoped ровные кнопки. Canonical ReadFiles/FilePreviewBody расширены, отправка/UploadQueue прежние. [Карточка](tasks/T15d.md#student-homework-workspace--локальная-проба-26102026).
- PASS scoped24/full187(maxWorkers2)/viewer12,types/lint/format/API types/tokens/build,Impeccable0; Premium2 прежних false positives. Axe duplicate viewport исправлен; harness FAIL/старый teacher fixture FAIL описаны в карточке.
- Chrome student12.8s/teacher current3.1s/S3 regression32.6s PASS;1340/1024/768/360/центры кнопок≤1px/axe0. Реальный GET отдельно от HTTP mock upload/send/edit, source учебных writes0, ДЗ58 не трогали.
- VERIFY/owner отзыв ожидает; S2/S3/S4 остаток сохранён. Без DB/seed/reset/backend/API/установок/Codex config/Git/deploy; physical/full200%/server write E2E/T16 NOT RUN, S5/S6 не начинались.


### 26.10.2026 · «Мои занятия» на student дне
- По новому owner запросу: compact latest completed/date/topic/course/teacher, урок/история; desktop под nearest, mobile после result, canonical query/cache/ReadState/LinkButton. [Карточка](tasks/T15d.md#мои-занятия-на-student-дне-26102026).
- PASS scoped14/full189(maxWorkers2),types/lint/format/API types/tokens/build/Impeccable0, Premium2 прежних false positives; промежуточные TS/harness FAIL исправлены, детали в карточке.
- Chrome1/7.4s PASS: real GET отдельно от HTTP fixtures,1340/768/360/Enter/Back/empty/error/loading/metadata/long/readonly/axe0; центр кнопок≤1px, source учебных writes0, ДЗ58 не трогали.
- VERIFY/owner отзыв ожидает; прежний S2/S3/S4/workspace остаток сохранён. Без backend/API/DB/seed/reset/установок/Codex config/Git/deploy; physical/full200% NOT RUN, S5/S6/T16 не начаты.


### 26.10.2026 · уточнение блока «Мои занятия»
- По owner: только дата/МСК и teacher; без темы/курса/урочного CTA. Одна «Открыть занятия» → месячная история; canonical CourseContext teacher-inline, full default прежний. [Карточка](tasks/T15d.md#уточнение-владельца-вход-в-раздел-мои-занятия-26102026).
- PASS scoped14/types/lint/format/API types/tokens/build/Impeccable0; Premium2 прежних false positives. Chrome1/9.1s real GET/отдельные HTTP fixtures/1340/768/360/Back/axe0/центр кнопок≤1px, source writes0.
- VERIFY/owner отзыв ожидает; прежние остатки сохранены. Без данных/ДЗ58/backend/API/Git/deploy/установок/Codex config; full unit без причины не повторялся, S5/S6/T16 не запускались.


### 26.10.2026 · student конспект начально свёрнут
- По owner: initiallyCollapsed только для конспекта HomeworkPage на всех ширинах, явное раскрытие; keyed homework.id сбрасывает открытость нового ДЗ. Condition/teacher/viewer engine/отправка прежние. [Карточка](tasks/T15d.md#конспект-на-странице-дз--начально-свёрнут-26102026).
- PASS scoped4/types/lint/format/API types/tokens/build/Impeccable0; Premium2 прежних false positives. Chrome1/13.6s PASS,1340/1024/768/360/axe0; harness FAIL→PASS описан в карточке, без source учебных writes/ДЗ58.
- VERIFY/owner отзыв ожидает; прежние остатки сохранены. Без backend/API/DB/Git/deploy/установок/Codex config, S5/S6/T16 не начаты.


### 26.10.2026 · короткая подсказка student файлов
- Integrated UploadQueue: «Фото или PDF · до 20 МБ на файл. Макс. 10 файлов.»; без перечисления форматов/100МиБ в подсказке. Настоящие лимиты/validation/default variant прежние.
- Target formatter/lint/typecheck и read-only live IAB ДЗ63 PASS; full unit/build/browser suite NOT RUN для copy-only. [Карточка](tasks/T15d.md#короткая-student-подсказка-файлов-26102026).
- Учебных данных/ответов/ДЗ58/Git/deploy/установок изменений нет; owner отзыв ожидает.

### 26.10.2026 · визуальные варианты student дня, только исследование
- Live screenshot/DOM/computed CSS: white hover #F8F9FA почти белый;4 основных CTA label смещены вверх5px, recent CTA0; разный padding/ArrowRight, active nav hover перезаписывает selected.
- Предложены3 направления (голубая оболочка/тёплый стол/контрастная шапка), рекомендован1; общие единые навигационные кнопки/сильный hover/стрелки/умеренные иконки/короткие подписи. [Разбор](tasks/T15d.md#визуальные-варианты-student-мой-день-26102026--исследование).
- Только docs/read-only, приложение/токены/данные не менялись. Не формальный dual-agent critique; tests/build/DB/seed/Git/deploy/установки NOT RUN, направления ожидают выбора owner.


### 26.10.2026 · student вариант1 «Голубая оболочка»
- Owner выбрал1: student tokens/фон/шапка, короткое меню/Lucide, canonical opt-in day navigation Button/ArrowRight/центр/strong hover, короче copy/ровные отступы; teacher/admin default прежние. [Карточка](tasks/T15d.md#вариант1-голубая-оболочка-student-26102026).
- PASS full189(maxWorkers2)/types/lint/format/API types/tokens/build/Impeccable0; Premium2 прежних false positives. Fix browser mobile contrast/overflow, harness selectors/exit portal описаны в карточке.
- Chrome student1/4.1s, teacher real+admin dev nav1/1.9s, history1/7.2s PASS;1340/1024/768/360/hover/центр≤1px/Back/axe0. Preview штатно resume5173/8019 с прежним media; source учебных writes0/ДЗ58 не трогали.
- VERIFY до owner; старые остатки сохранены. Без backend/API/DB/seed/Git/deploy/установок/Codex config; full admin/physical/full200%/T16 NOT RUN, S5/S6 не начаты.


### 27.10.2026 · student mobile shell
- По owner: header56/Bell/unread badge, bottom53/day/занятия/расписание/More, «Д/з» в More; min44, canonical AppShell/NotificationCount, без учебных mutations. [Карточка](tasks/T15d.md#компактная-student-mobile-навигация-27102026).
- PASS unit193 по группам (full192/1 FAIL→scoped7), types/lint/format/API types/tokens/build, Impeccable0; Premium2 прежних. Все harness FAIL/исправления перечислены в карточке.
- Chrome real mobile1/4.3s, unread HTTP fixtures1/3.3s PASS; independent student-blue student3.9s/teacher+admin dev1.7s PASS.360/388/768, keyboard/Back/PDF/axe0 shell; старый lesson link contrast4.39 вне scope отдельно, full lesson axe PASS не заявляется.
- VERIFY до owner; сохраняемые данные/ДЗ58 прежние, без seed/backend/API/DB/Git/deploy/установок; physical/Safari/OS keyboard/full200%/T16 NOT RUN, старые приёмки S2/S3/S4 сохранены.


### 27.10.2026 · исследование student latest
- Read-only source/Chrome /student/materials1280/360: latest353/640px, mobile история top952; лишние intro/повторы/длинные filenames/четыре конкурирующих CTA.
- [Предложен компактный белый latest](tasks/T15d.md#student-занятия--исследование-компактного-latest-27102026): date/topic/context, два коротких material/HW действия, secondary lesson; multiple/loading/error/архив/URL/Back сохранить.
- Это исследование, выбор owner впереди; UI/данные/ДЗ58 прежние, implementation/tests/build/Git/deploy/установки не выполнялись.


### 27.10.2026 · компактная student latest сводка
- Owner выбрал предложенный white latest: короткие Конспект/Д/з, date/topic/teacher, secondary lesson, multiple раскрытие/Pages; архив/read-only/scoped metadata/URL/origin/S1 сохранены. [Карточка](tasks/T15d.md#student-latest--компактная-белая-сводка-27102026).
- Unit196 по группам: full195/1 archived-context FAIL→scoped18 PASS; types/lint/format/API types/tokens/build PASS, Impeccable0, Premium2 прежних false positives.
- Chrome real2.9s/fixtures7.4s/teacher compatibility2.6s PASS;1340/768/360/44px/центр/Back/PDF/axe0. Исправлены label abbreviations и сохранена archive подпись. Текущий mobile latest≈196 против640, history top≈354 против952.
- VERIFY до owner; source learning writes0/ДЗ58 не открывали. Без backend/API/DB/seed/Git/deploy/установок; physical/full200%/T16 NOT RUN, прежние S2/S3/S4 остатки сохранены.


### 27.10.2026 · latest: заметный переход принят владельцем
- Незаметная header-стрелка заменена голубой подписанной «Открыть занятие →» под материалами, mobile full width; canonical navigation/URL/Back прежние. [Карточка](tasks/T15d.md#latest--заметная-кнопка-и-принятие-владельцем-27102026).
- PASS full196/maxWorkers2/types/lint/format/API types/tokens/build/Impeccable0; Premium2 прежних. Chrome1/3.6s/1340/768/360/hover/focus/Back/PDF/axe0/writes0; runtime resume без seed после начального browser FAIL входа.
- Owner явно одобрил текущий визуальный блок и попросил запомнить вкус: закреплено в DESIGN как образец для похожих экранов. Эта визуальная приёмка принята, прочие S2/S3/S4/device остатки сохранены; данные/ДЗ58 прежние, Git/deploy/установок нет.


### 27.10.2026 · исследование student monthly history
- Read-only DOM/source выявили year/current offset12px из-за label+Group center; mobile controls не помещаются рядом, count/range и generic title дублируются.
- [Предложен компактный white toolbar](tasks/T15d.md#student-history--исследование-управления-и-строк-27102026): выровненные year/«Этот месяц», unselected outlined/selected blue, короткие counts и строки; альтернатива — tinted toolbar. Latest явно вне scope.
- Только исследование/docs, выбор owner впереди; код/tests/build/data/ДЗ58/Git/deploy/установки не затронуты, временный viewport/scroll восстановлен.


### 27.10.2026 · student history вариант1
- Owner выбрал1 с прежним «Текущий месяц»: выравнивание year/current, white/selected month, компактные counts/rows, «Материалы». [Карточка](tasks/T15d.md#student-history--вариант1-реализован-27102026). Latest JSX и прежний CSS prefix совпали с backup.
- PASS full198/maxWorkers2/scoped20/types/lint/format/API types/tokens/build/Impeccable0; Premium2 прежних. Browser initial real landmark-unique FAIL исправлен только в history names.
- Real1/8.0s и отдельные HTTP fixtures1/10.3s PASS;1340/768/360/Select popup/keyboard/Back/lazy lesson129/PDF/axe0/source writes0. Успешные независимые группы не повторялись.
- Новая история VERIFY до owner; принятый latest/старые S2/S3/S4 остатки сохранены. ДЗ58 не открывали; без backend/API/DB/seed/Git/deploy/установок; physical/full200%/T16 NOT RUN.


## 28.10.2026 — student mobile header48
- Шапка48px вместо56, studentCanvas без линии, Bell44 и badge прежние; scoped CSS.
- PASS unit198/types/lint/API types/tokens/build/format после форматирования assertion;
  Chrome real mobile5.0s + HTTP badge fixtures3.1s, teacher/admin shell regression;
  Impeccable0. Premium FAIL2 прежних, physical/full200%/T16 NOT RUN.
- Preview сохранён без seed/учебных writes/ДЗ58/Git действий; S2/S3/S4 приёмки прежние.
- Отзыв owner о хорошем общем визуале и будущие teacher schedule/drag/Undo/VK
  требования записаны в T15d. Новые возможности пока только wishlist, без реализации.


### 28.10.2026 — уточнение белой mobile полосы и bottom49
Owner попросил вернуть разделение: белая шапка48 с border1; bottom49 вместо53,
кнопки≥44/safe inset. PASS198 unit/frontend gates/Impeccable0; Premium2 старых.
Browser initial FAIL login при неработающем backend → retained resume без seed →
PASS2 (real5.1s/HTTP unread fixtures3.3s),360/388/768/Tab/More/Back/PDF/axe0/writes0.
Визуал360 просмотрен; physical/200%/T16 NOT RUN. Старые приёмки/данные/ДЗ58 прежние.


### 28.10.2026 — сверка и передача к teacher schedule
Git root/branch/SHA/status/diff check и логи header-white49 gates сверены, source
после них не менялся. Preview listeners5173/8019 работают; IAB teacher/schedule
загрузил реальные занятия/недельный итог, без мутаций. Full gates не повторяли
без причины, smoke не объявляется полной регрессией. Создан T15d_TEACHER_SCHEDULE_HANDOFF.md:
вход в контекст/существующие owners/интервью/границы/fixtures/data invariants.
STATUS intermediate header48 явно помечен superseded. Старые S2/S3/S4 VERIFY
сохранены; никаких commit/push/PR/merge/deploy/установок/учебных записей.

### 28.10.2026 — исследование teacher schedule, интервью продолжается
Real IAB desktop/narrow: карточки155–208/226px, высокая шапка и растущие часовые строки;
create/move/cancel/series UI изучены без сохранения, server version/receipts/notifications сверены.
Owner: отменённое сразу убрать из сетки с сохранением истории. Остальное ещё обсуждается.
[Наблюдения и пределы](tasks/T15d_TEACHER_SCHEDULE_HANDOFF.md#исследование2810--обсуждение-продолжается-без-реализации).
Без реализации/DB tests/seed/ДЗ58/Git/deploy/установок; прежние приёмки открыты.

### 28.10.2026 — teacher schedule, явное разрешение реализации после макета
Компактная сетка/day, HH:00 drag+confirm, прямой урок/отдельное меню, hide cancelled,
одиночный versioned Undo15s и подтверждаемое восстановление; shared mutation/dialog/series owners.
PASS203 frontend unit/50 standalone Python, types/lint/format/build/API types/tokens;
2 Chrome группы20.1s real read-only+HTTP fixtures, preview учебных writes0/ДЗ58 нет.
Impeccable0 (узкий font false-positive ignore), Premium2 прежних. Local VERIFY,
[факты/ограничения/owner остаток](tasks/T15d.md#teacher-schedule--рабочая-реализация28102026); Git/deploy/install/VK нет.

### 28.10.2026 — teacher schedule: стабильный цвет, широкая область и компактное утро
Owner уточнил: planned голубой при press/drag; completed зелёный. Убрана mint active,
desktop route main1440/padding24, пустые08–11 по44/занятые88 синхронно7 дней+axis.
RAF edge scroll, memoized input, reduced-motion/loading; height animation исключена.
PASS204 unit/types/lint/build/format; Chrome2/25.2s+targeted1/10.9s, real read-only/HTTP
fixtures отдельно, source writes0; Impeccable0/Premium2 прежних, DB/ДЗ58/Git/VK нет.
[Детали и owner visual остаток](tasks/T15d.md#teacher-schedule--цвет-рабочая-область-и-утро-28102026).


### 29.10.2026 — teacher shell по принятому образцу student
Общие компактные header48/footer49+safe-area, teacher icons/More, bell с реальным unread;
teacher role routes/Students/Profile сохранены. PASS205 unit/types/lint/build/format,
Chrome1/6.5s+Аxe0: real teacher reads, HTTP unread fixtures и dev showcase отдельно.
Impeccable0/Premium2 прежних, учебных writes0/ДЗ58/DB/Git/deploy/install/VK нет.
[Доказательства/ограничения/owner VERIFY](tasks/T15d.md#teacher-shell--компактная-навигация29102026);
CUA недоступен, использован проектный Chrome; старые S2/S3/S4 приёмки открыты.


### 29.10.2026 — teacher «Мой день», компактно и с сохранением цвета
Owner сохранил «К ученику»/жёлтый review; next time/name выровнены, Today без МСК,
плоский compact ReviewRows, mint материалы с одним действием/причинами/expansion.
205unit, финальные types/lint/build/format/tokens; Chrome16.0s+7.4s, Axe0,
real teacher reads/HTTP long-empty-error fixtures отдельно, учебных writes0.
Impeccable0/Premium2 прежних; данные/ДЗ58/DB/Git/deploy/install/VK прежние.
[Ограничения и owner VERIFY](tasks/T15d.md#teacher-мой-день--компактная-реализация29102026).


### 29.10.2026 — teacher day, доработка по просмотру владельца
Материалы pink/badge насыщеннее, «Свернуть»→offset0/первые3; review отдельная
LinkButton без hover всей строки. Today dot+label green/blue, highlight сохранён.
AA failure primary/lesson исправлен lgg8; финал205unit/types/lint/build/format/tokens,
Chrome1/8.4s/Axe0/writes0, Impeccable0/Premium2 прежних. Real reads/HTTP fixtures
раздельно; DB/ДЗ58/Git/deploy/install/VK нет, owner/S2/S3/S4 приёмки открыты.


### 29.10.2026 — исследование teacher карточки ученика, без реализации
StudentWorkspace/StudentHistory/ReadFiles через AST+source; real Dmitry33 empty/
expanded history и HTTP notes/HW/both/long/503/no-lessons/mobile отдельно.9 captures,
overflow0/pageerrors0/учебных writes0/ДЗ580. Latest319→463px с ДЗ, long984;
рекомендованы компактные header/material/history, latest сразу открыт неизменно.
[Исследование/границы](tasks/T15d.md#teacher-карточка-ученика--занятия--исследование29102026).
Owner обсуждение впереди; UI/данные/DB/Git/deploy/install/VK не менялись.


### 29.10.2026 — teacher карточка ученика, локальная реализация
Owner разрешил после исследования: общая шапка/settings, compact latest+notes/HW
без вложенных заливок/растяжения, иконки, выровненная history и dot+status.
Latest всегда открыт/текст ДЗ целиком/ReadFiles+URL contract прежние.205unit/gates,
Chrome9captures/Axe0/overflow0/writes0/ДЗ580; empty latest319→222px, both463→374.
Impeccable0/Premium2 прежних; [детали](tasks/T15d.md#teacher-карточка-ученика--занятия--реализация29102026).
Owner/S2/S3/S4 открыты; DB/Git/deploy/install/configCodex/VK нет.


### 29.10.2026 — teacher список учеников
Scoped compact header/filters/rows76+, красные dot+text missing counts, Lucide;
поиск/IME/сортировка/фильтры/переходы прежние.205unit/gates, Chrome10.5s+10.8s,
Axe0/overflow0/writes0, real GET отдельно от HTTP edge fixtures. Narrow field
span исправлен после QA, locator Mantine уточнён. Impeccable0/Premium2 прежних.
[Детали](tasks/T15d.md#teacher-список-учеников--компактность29102026); owner/S2/S3/S4
открыты, учебные данные/ДЗ58/DB/Git/deploy/install/VK не тронуты.


### 30.10.2026 — общий Back для student/teacher
ArrowLeft20/target44 рядом с LGG, shared role-safe planner/80 session entries,
Router POP skips query-only и сохраняет источник; direct-link fallback/dirty guard.
PASS213unit/types/lint/build/format/tokens, real Chrome2/9.2s/Axe0/writes0/HW580;
Impeccable0/Premium2 прежних. [Результат/ограничения](tasks/T15d.md#общая-стрелка-назад--30102026).
Owner/S2/S3/S4 открыты; учебные данные/ДЗ58/DB/Git/deploy/install/VK не тронуты.


### 30.10.2026 — итоговая сверка и сводный вход
Pinned Node24/npm11.19:213unit/gates/API types;32 frontend/50 Python pins совпали,
26 standalone mocks/pip check/read-only SQL guard PASS. Chrome5PASS+drag initialFAIL,
trace native drop16 и стабилизация fixture viewport→final1PASS10.7s; workspace9
states/Axe0/writes0/HW580. Product code в чекапе не менялся, только test input/docs.
[Сводка](tasks/T15d_UI_HANDOFF_2026_10_30.md); STATUS565→короткий current, история
сохранена, README D12/ENV resume/GPT синхронизированы. VK по уточнению owner пока
не исследовать/не реализовывать; manual/S2/S3/S4/полная T16 не закрыты.

Документационные пути:14 canonical/108 и весь docs/plan69 Markdown/459 local targets,
missing0; relative links архива STATUS пересчитаны после переноса. Anchors этим
скриптом не проверялись. Исследование/реализация VK остаются отложенными владельцем.

## 30.10.2026 · начало исследования VK по новому запросу

- Разрешены исследование/интервью/документирование, без реализации; [черновик](VK_RESEARCH_2026_10_30.md).
- Проверены внутренний Git/dirty и AST owners auth/invite/access/notifications/lessons/series; данные/preview не трогали.
- Первые2 вопроса заданы; SDK/schema VKCOM доступны, правила VK частично недоступны (web error/browser site-safety), правовая сверка РФ неполна.
- `git diff --check` PASS; DB/browser integration tests NOT RUN; прежние gate/приёмки сохранены, Git/publish/install не выполнялись.
- Продолжение интервью: найден/прочитан локальный VK_math_bot без запуска/импорта/секретов/JSON базы. В [исследование](VK_RESEARCH_2026_10_30.md) добавлены реальные владельцы, различие weekday-сетки и датированных Lesson, риски отмен/гонок/родительской привязки и варианты Sheets. Вопросы о смысле записи и прямом редактировании таблицы ожидают ответа; ст3/18/22 сверены в ведомственной копии152-ФЗ с ограничением актуальности.

## 31.10.2026 · интервью VK: расписание и пожелание в backlog

- В [исследовании](VK_RESEARCH_2026_10_30.md) зафиксированы постоянное время и разовая запись текущей недели только в открытые преподавателем окна; желание редактировать Sheets и платформу.
- По просьбе владельца в TASKS/F04 записано копирование выбранных занятий прошлой недели на следующую; исходные встречи сохраняются, детали копии/конфликтов ещё обсуждаются.
- Зафиксировано расхождение сказанного «S» и локального parser `C`, без изменения кода/таблиц. Только документация; реализация/прежние gate не разрешены и не закрыты.
- Продолжение31.10: выбран простой вход VK, первичная связь с User пока не утверждена; демо student/teacher с synthetic данными записано F07. Владелец сообщил, что оформления команды и уведомлений РКН нет; ПД бота квалифицированы по составу кода, оператор не назначен.
- Повторно проверены официальный SDK VK и разъяснения прокуратуры/сообщение РКН2026; VK cabinet/terms и портал подачи недоступны. Источники/ограничения в исследовании, PRIVACY/STATUS обновлены; никаких реализаций/подач/создания apps/данных/секретов.
- Упрощение31.10: обсуждается минимальная связь бота с платформой без VK ID, с учётом будущих SaaS/подписок. В исследовании/F01/F03/F05 записаны явные открытые окна, переход с нынешней Sheets-записи на одного владельца расписания и запасной read-only экспорт с timestamp; периодичность/переход ещё согласуются. T18 backup/restore не заменяется таблицей. Только документация, `git diff --check` PASS.
- Владелец подтвердил рабочее использование бота родителями/учениками, попросил безопасный способ проверки без нового сообщества. В исследовании/STATUS записаны offline fixtures, сохранение parent→student, отдельный ограниченный живой пилот; параллельный local start_bot с боевым token не изолирован, ночная остановка влияет на клиентов. Только документация, сервер/бот/секреты/данные не тронуты; `git diff --check` PASS.
- Дополнение31.10: владелец разрешил будущие тесты/изменения таблицы и контекста Даниила, сообщил, что настоящие пользователи/расписание только Тимура. Это не изоляция общих JSON/Long Poll/reminders и не разрешение deploy. Запрошены полное интервью → исследование/подробный план с адаптацией существующих canonical docs/промптов, без множества новых файлов; интервью продолжается, код/сервер/данные не менялись.
- Выбор владельца31.10: ночные live тесты с остановкой серверного бота, локальной проверкой Даниила и возвратом прежнего сервера; заменяет рекомендацию обязательного серверного пилота. В исследовании/STATUS записаны один экземпляр, изоляция global reminders/JSON и возврат при ошибке; сейчас никаких запусков/остановок/deploy, интервью продолжается.
- Ответы31.10 закрыли маршрут записи/недельные окна/parent actions: сохранить нынешние дни→часы→confirm, без teacher approval, серии ставит teacher, reminder ребёнку. Подробно прочитаны все handlers/keyboards/database/google_sheets/reminders и main; живые данные/секреты не открывались, код не запускался. В исследовании отмечены raw имя+класс, профиль до проверки слота и отдельная задача identity-link; дальнейшие вопросы о связи с User/новых уведомлениях, без пересогласования прежнего UX.

## 01.11.2026 · интервью VK: первая запись и доступ

- Владелец принял «запись сразу в платформе → teacher выдаёт приглашение → после активации доступ к уже связанному занятию»; в исследовании/STATUS отделены бронь и выдача доступа, без сопоставления User по имени.
- Следующий блок — доставка ребёнку при родительской записи и новые уведомления ДЗ/review. Только документация; код/бот/сервер/данные не менялись, `git diff --check` PASS.
- Ответ01.11 принял неблокирующую бронь при недоставке ребёнку и точный набор коротких VK уведомлений с переходом в кабинет. В исследовании/STATUS записаны отдельные результаты брони/доставки, запрет≠transient error, dedupe/revoke/неактуальный reminder и матрица проверок; parent ДЗ/оценки не получает. Только документы, без live действий/реализации; `git diff --check` PASS.
- Последним ответом01.11 принято одноразовое подтверждение parent→child преподавателем. Основное интервью достаточно для углублённого исследования; в начале VK research добавлена текущая сводка, в существующем PROMPTS — подробный следующий исследовательский запуск; GPT/STATUS указывают актуальный scope вместо прежнего запрета исследования. Новых файлов/реализации/live действий нет; технические/правовые пробелы не объявлены закрытыми.

## 01.11.2026 — F01.R: углублённое исследование/планирование VK

- Только docs/source review, [результат/официальные источники/ограничения](VK_RESEARCH_2026_10_30.md); локальные main/src бота прочитаны без импорта/запуска/защищённых файлов.
- Принято владельцем: бронь сразу, аккаунт при приглашении; отмена возвращает подходящее исходное окно. PRODUCT/D13, проект A14 и [F01.0–.9/F05.1](tasks/F01.md) разделяют разработку/live/cutover/export; MVP/T16/P01/P03 прежние.
- Старые research/STATUS сохранены в history; canonical документы и prompt обновлены. VK rules/quotas/полный текущий закон/формы РКН UNVERIFIED, P01 открыт.
- Docs PASS:16 документов/133 local targets+anchors,73 Markdown/523 file targets missing0;925 source hashes changes0, diff/whitespace PASS; итог в F01.R. Bot/данные/preview/DB tests/VK/Google/SSH/install/Git/deploy NOT RUN. Следующий F01.0 только документация по новому запросу, код не разрешён.


## 02.11.2026 — F01.0: local contract DONE, external gates открыты

- Только документация/source review: [карточка и checks](tasks/F01.md#результат-f010-02112026), [A14.7](ARCHITECTURE.md#a147-f010-local).
- DTO/errors/receipts, lock prefix/stages/implicit FK/purge и четыре walkthrough; NULL price/late review/D01/D13 сохранены, без нового бизнес-решения.
- [VKCOM pins](VK_RESEARCH_2026_10_30.md#f010--ревизии-и-внешние-gates) отделены от UNVERIFIED rules/quota/ACK/replay/permissions; P01/live не закрыты. Исходники/данные/бот не менялись.
- Gate PASS:10 docs/89 targets+anchors,73 Markdown/538 file targets missing0;519 source hashes changes0, diff/whitespace PASS. DB/browser/runtime/миграции/VK/Google/preview/SSH/install/commit/push/deploy NOT RUN. F01.1 новым запросом, порядок MVP/P03 прежний.

## 02.11.2026 — F01.1: offline harness local DONE

- Явный запрос перенёс только F01.1 перед MVP/P03; [результат/файлы/gates/остаток](tasks/F01.md#результат-f011-02112026). F01.2+ не разрешены/не реализованы.
- Synthetic ports/fakes/clock, strict normalized events, temporary JSON checkpoint/replay/restart, explicit offline CLI; app startup/бот/данные не менялись.
- PASS:43 standalone tests, clean-env subprocess с guard до import и negative network/JSON/reminder/credentials probes, self review/diff/scoped33 docs links. Два первых isolation FAIL (PYTHONPATH/tempdir probe) исправлены; expanded docs scan FAIL на3 старых anchors вне scope, история в карточке.
- DB/browser/retained preview/VK/Google/Long Poll/бот/server/install/commit/push/PR/merge/deploy NOT RUN. VK external gates UNVERIFIED/P01 открыт; далее F01.2 только по новому запросу.


## 02.11.2026 — F01.2: local identity/parent/invite DONE

- Отдельный explicit приоритет только .2 перед MVP/P03; [результат/файлы/gates](tasks/F01.md#результат-f012-02112026). .3+ не реализованы.
- Additive `f01220261102`, canonical recipient/identity/grants/challenges/operations; atomic inactive account/workspace/invite; public D01 и admin-only second teacher сохранены, connector HTTP закрыт до .4.
- PASS: новый container/actual DB-engine-session-role-media preflight55433;72 DB/migration/access/concurrency/failure/retry/HTTP tests +61 standalone regression; compile/diff/docs. Retained55432/dev55431/media/бот не использованы.
- Conditional Git разрешён, но branch/commit/push NOT RUN: F01.1/общие зависимости/карточка отсутствуют в HEAD и dirty/untracked; чужое не включалось/не stash/reset. Нужен отдельный baseline checkpoint.
- Synthetic container остановлен с сохранением volume; UI/live/VK/Google/Long Poll/server/install/PR/merge/deploy NOT RUN. VK/P01 gates открыты; F01.3 только новым запросом.


## 02.11.2026 — сохранение накопленной работы и понятный следующий вход

- По последующему явному поручению владельца Git-разделение решено исполнителем: `codex/save-project-f012-20261102`, `daabcb5` — прежняя платформа/frontend/документы/F01.0–.1, `1456d76` — отдельно F01.2. Рабочие файлы при разделении не заменялись; без stash/reset/delete.
- Проверены706 project files/689 pre-.2 index blobs, исходные hashes, оба Git roots и пользовательский origin; private-key/token scan0, совпадения password/URL — templates/runtime variables/явные synthetic fixtures. .env/DB/media/private artifacts/runtime dependencies исключены. Внешний root и upstream не изменялись.
- Frontend: initial203 PASS/10 FAIL (таймауты и зависимость fixture от текущей недели); Date теста зафиксирован, Vitest maxWorkers2; final **213/40 PASS**, types/lint/build/scoped formatting PASS. Сохранён прежний build chunk warning; UI не менялся. Ошибка cwd первого scoped Prettier исправлена до PASS. F01.2 прежние72 DB+61 standalone PASS остаются; DB/preview/browser/live повторно не запускались.
- Git blocker снят. Итоговая служебная запись отдельно сохраняет test/config fix и текущий handoff; push в origin проверяется по exact remote branch SHA. PR/merge/deploy/server/VK/Google/Long Poll/install NOT RUN.
- [Один актуальный prompt F01.3](PROMPTS.md#актуальный-следующий-чат-f013) подготовлен без реализации .3+: затем .4 UI → .5 offline bot adapter → .6 reminders → .7 synthetic E2E; live gates отдельно. От владельца техническое решение по Git не требуется.


## 02.11.2026 — F01.3 local booking backend DONE

- По новому explicit prompt/приоритету/scope/commit-push реализована только .3: [результат/файлы/границы](tasks/F01.md#результат-f013-02112026). Dated windows, CAS/handles/receipts, confirmed Booking, atomic resolve/invite/Lesson/D04/outbox; teacher warnings/series/restore и cancellation reopen, без UI/live.
- Новый контейнер dbd480208622…/labels F01.3 synthetic/DB55434, restricted role и actual engine/session/media preflight PASS; прежние DB55433/55432/55431/retained preview/бот не тронуты. Additive f01320261102 и protected downgrade, clean/prior upgrade metadata diff0.
- Final **115 actual DB PASS /71.47s +61 standalone PASS**, 2 retained-env tests deselected;42 booking checks включая concurrent connections/rollback/timeout/access/OpenAPI/D04 checked/D12. Initial fixture/assertion/concurrent preview failures исправлены и сохранены в карточке, final FAIL0.
- Отдельная codex/f013-booking-20261102 от17923bb, только изменения .3 в origin после PASS; baseline commits не переписываются. PR/merge/deploy/server/install/VK/Google/Long Poll/live NOT RUN; UI acceptance ожидает .4, external VK/P01 gates открыты.
- Следующий вход — [один prompt F01.4](PROMPTS.md#актуальный-следующий-чат-f014), только новым запросом; .4+ не начинались.


## 02.11.2026 — F01.4 local teacher UI · VERIFY

- По explicit scope/приоритету/commit-push владельца только .4: [результат, gates и ручная приёмка](tasks/F01.md#результат-f014-02112026). Окна/confirmed брони в расписании, parent confirm/revoke, invite/activation и self-link; UI skills/DESIGN/A12–A14, прежние tokens/owners сохранены.
- Новые guarded synthetic55435 (preview5174→8020) и55436 (финальная regression), restricted roles/temporary media; retained5173/8019/55432/dev55431/старые55433/55434/бот не тронуты. Финальные119 actual DB +61 standalone +218 frontend PASS, types/lint/build/tokens/DTO/format PASS; 2 прежних premium finding/chunk warning отдельно в карточке. Preview cookie `lgg_f014_refresh` отделена от retained, default auth contract сохранён.
- Real browser two-role same Lesson, parent grant/revoke, existing User self-link/materialize, own student context/foreign read PASS; viewport360/390/768/1280/CSS200/keyboard/Escape/focus/Axe0. Initial fixture/mock/locator/focus/rate-limit failures и оставшиеся факты сохранены в карточке, owner acceptance ожидает.
- После final автоматических PASS создана отдельная codex/f014-teacher-booking-ui-20261102 от75636a0, только .4 commit/push в пользовательский origin; точный SHA/remote verification — в финальном ответе. Preview оставлен для ручной приёмки; без F01.5+/live/внешних отправок/server/install/PR/merge/deploy.
