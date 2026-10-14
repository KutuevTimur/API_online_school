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
