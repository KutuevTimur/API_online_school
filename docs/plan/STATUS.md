# Текущее состояние LGG

**02.11.2026 · F01.1 local DONE: synthetic offline harness, без live.**
Принято новое уточнение: бронь сразу занимает время/видна teacher, аккаунт при
приглашении; известная подтверждённая связь создаёт Lesson сразу. Полные ответы
[PRODUCT/F01](PRODUCT.md#будущий-f01--существующий-vk-бот--принято301001112026)/[D13](DECISIONS.md#d13),
проект [A14](ARCHITECTURE.md#a14), источники/ограничения [research](VK_RESEARCH_2026_10_30.md),
этапы/проверки/возврат [F01](tasks/F01.md).

**F01.0 local завершён:** [A14.7](ARCHITECTURE.md#a147-f010-local),
[pins/external gates](VK_RESEARCH_2026_10_30.md#f010--ревизии-и-внешние-gates),
[результат/gates](tasks/F01.md#результат-f010-02112026).
**F01.1 local завершён** по явному переносу приоритета владельцем перед MVP/P03:
[результат/границы/gates](tasks/F01.md#результат-f011-02112026).
`src/modules/integrations_vk/` + standalone `tests_unit/integrations_vk/`:
fake transports/clock, strict normalized events, temporary JSON/replay/restart,
explicit offline entrypoint, fail-closed isolation до import. **43 tests PASS**,
clean env subprocess/tripwires и diff/docs links PASS. Это fixture HTTP admission,
не booking/parent domain, не live adapter. F01.2+ не реализованы/не разрешены;
следующий VK ID F01.2 только новым запросом с отдельным synthetic DB scope.
Остальная F01 после MVP/P03; исключение приоритета относится только к F01.1.
Текущий основной план T15d → T16.1/.2 → подготовка запуска прежний.
F01.0 docs gate PASS:10 docs/89 local targets+anchors; весь пакет73 Markdown/
538 file targets missing0;519 source hashes changes0, diff/whitespace PASS.
Исторический gate F01.R:16 документов/133 local targets+anchors PASS; весь пакет73 Markdown/
523 file targets без пропусков,925 source hashes без изменений, diff/whitespace PASS.
Неполные правила/квоты VK, полная актуальная правовая редакция/процедуры РКН и P01
остаются открытыми; доступные schemas не подтверждают live допуск.

## Рабочая точка и сохранность

- Internal repo `API_online_school`, branch `codex/t00-t01-environment`, базовый
  HEAD `95b3560bdb429a06e7e5567a78ed6ef589886e4a`; dirty/untracked сохранён.
- Внешний root main без первого commit/HEAD; не добавлять inner repo как gitlink.
- Локальный bot main/`cae7b8f175fc4b967bb9cfacd8764e3c14494f6e`, dirty/staged
  сохранены, read-only. Серверная версия/процессы не проверены.
- F01.1: новый offline module и synthetic unit tests; существующий app startup,
  bot repo и данные не менялись. Bot/DB/preview/E2E/Long Poll/VK/Google/SSH/server
  stop/install/commit/push/PR/merge/deploy NOT RUN. Чужой dirty/untracked сохранён.
- Ночной порядок согласован как будущий .8; Даниил test scope разрешён ранее,
  mapping/JSON/reminders/получатели требуют проверки перед запуском. Тимур и
  настоящие пользователи/общий JSON не disposable. Сейчас live действия запрещены.

## Существующая платформа ·30.10 local VERIFY

[Единая сводка реализации/версий/gates/ограничений](tasks/T15d_UI_HANDOFF_2026_10_30.md).
Не production release/не автоматическая приёмка владельцем. Local label
`T15d-ui-local-2026-10-30` не Git tag; frontend/lock0.1.0.

| Gate30.10 | Сохранённый факт;01.11 не повторялся |
|---|---|
| Frontend |213 unit/40 files, types/lint/build/format/tokens/DTO PASS |
| Python |26 standalone mock PASS; pip check PASS, не DB suite |
| Chrome |5 PASS общий run; schedule drag первоначально FAIL, после исправления тестового viewport адресный1 PASS10.7s |
| Карточка ученика |9 real/HTTP states, Axe0/overflow0/errors0/writes0/HW580 |
| DB |Только read-only preflight SELECT target/role/engine PASS30.10 |
| Прежние ограничения |2 premium findings/chunk warning, T16/full DB/physical/Safari/Firefox/full200% NOT RUN |

Storage owner acceptance принят. Визуальная приёмка текущих teacher экранов и
прежние S2/S3/S4/прочие manual gates открыты по [TASKS](TASKS.md), не переотмечены
исследованием. T16/production не DONE; D12 исключает архив из денег/количества.

## Preview

5173→8019→retained test55432, прежний media. Работающие процессы не перезапускать.
Resume по [ENVIRONMENT](ENVIRONMENT.md#сохранение-текущего-preview), без seed/reset/
DB tests поверх preview. Данные/ДЗ58 не трогать. Логины только ignored login files,
не документы/чат. Commit/push/PR/merge/deploy/установки не разрешены.

## История

Предыдущий [STATUS до исследования01.11](history/STATUS_before_2026_11_01_vk_planning.md),
[история до handoff30.10](history/STATUS_before_2026_10_30_handoff.md),
[прежнее VK интервью](history/VK_RESEARCH_before_2026_11_01.md),
[SESSION_LOG](SESSION_LOG.md). Исторические694 PostgreSQL PASS не текущая проверка.
