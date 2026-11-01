# PostgreSQL baseline — T02, 15.10.2026

> Историческое доказательство своего этапа. Актуальные требования — PRODUCT/DECISIONS,
> состояние — STATUS. Сохранённые failures/NOT RUN относятся к указанному снимку.

Цель: только созданный проектом disposable lgg-test (PostgreSQL 15,
127.0.0.1:55432, lgg_test/lgg_test_app). Compose project/container/healthy
подтверждены перед изменениями; guard T01 проверяет конфиг, фактический DSN
и session bind. Неизвестная внешняя БД не исследовалась и не менялась.
Ветка codex/t00-t01-environment, исходный HEAD 662a992. Новых commit/push/merge/deploy нет.

## Миграционная цепочка и проверка схемы

d98c55d6402c: исторически исправлена только опечатка autcrement → autoincrement.
56c4070bf9cd сгенерирована autogenerate относительно initial и затем дополнена
безопасным поэтапным backfill для synthetic baseline.
Единственные различия ORM/initial — soft-delete в courses/student_courses:
is_active удаляется, is_deleted/deleted_at добавляются. NOT is_active сохраняет
активное/неактивное состояние synthetic строк; это не автоматически разрешённый
mapping реальных строк. Дата неизвестного события остаётся NULL.
Перед удалением старого поля проверено отсутствие читателей в текущем коде.

Проверки tests/migrations/test_baseline.py:
- empty schema → upgrade head; повторный upgrade no-op;
- downgrade только новой revision → upgrade head;
- metadata/inspector всех 12 таблиц: типы, nullable, server defaults, индексы,
  unique/FK через compare_metadata; enum names/labels проверены отдельно;
- prior initial snapshot всех 12 таблиц: PK, counts, FKs и значения сохраняются;
  оба статуса в courses/student_courses; обратный mapping также проверен;
- main marker 1c3d40e331ff → явный отказ, marker сохранён,
  доменные таблицы не созданы. Это иной baseline, auto-merge не поддержан.

После head autogenerate diff пустой. Python-side defaults/onupdate не являются
server defaults и не требуют DDL. Downgrade теряет deleted_at, проверка на
synthetic DB не означает безопасность production downgrade.

## Команды и результаты

- Compose ps: lgg-test-postgres-1 healthy, project lgg-test, loopback 55432.
- MODE=TEST .venv/bin/alembic upgrade d98c55d6402c: PASS на пустой test schema.
- MODE=TEST .venv/bin/alembic revision --autogenerate -m 'align soft delete baseline':
  создана 56c4070bf9cd; только ожидаемые шесть column operations.
- MODE=TEST .venv/bin/python -m pytest tests/migrations -q --confcutdir=tests/migrations:
  3 passed (первый snapshot run выявил ошибку сравнения физического порядка
  колонок после downgrade; исправлен тест на сравнение по именам, данные сохранены).
- MODE=TEST .venv/bin/python -m pytest --ignore=tests/migrations -q:
  **141 passed, 0 failed, 0 skipped**, 34.95s.
- MODE=TEST .venv/bin/python -m pytest -q: **144 passed, 0 failed, 0 skipped**, 37.86s.
- Финальное состояние БД записано ниже.

## Известные ограничения и следующие задачи

Непройденных существующих тестов нет; expectations/xfail не менялись.
Зелёный legacy baseline не покрывает известные продуктовые/защитные дефекты:
T03 — public hash/active/JWT regression; T04 — refresh replay/concurrency/revoke;
T05–T06 — роли и объектный доступ. Их новые regression tests ещё предстоят.
Следующим auth regression tests этот baseline не препятствует.

Функциональные fixtures пока вызывают metadata.create_all; migration tests
независимы от них и переопределяют autouse schema/row fixtures.
Не запускать DB tests параллельно: они используют одну disposable schema.
Для повторения после полного pytest: migration tests → alembic upgrade head →
alembic check. Не stamp legacy schema, неизвестную БД не сбрасывать.
Не проверены реальные данные, production downgrade/restore, frontend/E2E и deploy.


Финальное состояние lgg-test: после общего pytest повторно выполнены migration tests
(3 passed, 5.34s), затем MODE=TEST .venv/bin/alembic upgrade head и alembic check:
PASS, «No new upgrade operations detected». Оставлена пустая synthetic схема
из 12 доменных таблиц на head 56c4070bf9cd, контейнер работает.
git diff --check: PASS. Новых commit/push/merge/deploy нет.


## T07 — итоговый baseline 15.10.2026

Полный pytest: **290 passed**, 128.63s (0 failed/0 skipped), включая 24 T07
regressions и 3 новых migration checks. Финальная migration suite: **11 passed**,
17.11s; upgrade head/check PASS, schema diff пустой. Guarded lgg-test оставлена
пустой на head 811d7911d0b4: 19 domain tables, 0 rows. AST 230 Python files и
diff check PASS. Подробности/промежуточные failures: tasks/T07.md.
Внешняя БД/рабочее media не затронуты; UI/dev build/start/E2E не проверялись.
Новых commit/push/merge/deploy нет.
