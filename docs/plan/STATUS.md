# Текущее состояние LGG

**02.11.2026 · F01.4 код/автопроверки готовы; local VERIFY по отдельной ручной приёмке.**
Владелец дал положительный визуальный отзыв, поручил функциональные проверки агенту;
полный ручной walkthrough не заявлял. Панель компактнее: «Время для записи» +
«Открыть» / «Убрать», прежние paint/batch/keyboard/target≥44px сохранены.
[Результат125 actual DB +222 frontend/real API20+20](tasks/F01.md#доработка-f014-по-ручному-отзыву-02112026).
Финальная copy/CSS правка: types/lint/build/scoped9 unit/format PASS;
read-only desktop1280/mobile390 PASS, Axe0/page errors0, кнопки93/81×44px;
вход/выбор/отмена PASS, без booking writes и нового DB reset.
Owner preview5174→8020→synthetic55435 и ignored `frontend/.artifacts/f014-login.txt`
сохранены; retained5173/8019/55432 и все прежние данные не менялись.
Task branch `codex/f014-teacher-booking-ui-20261102`:835bb6b +fa5b47a уже в origin;
последний compact/handoff commit сохраняется после PASS. Без PR/merge/deploy.

**Дальше — F01.5 только в новом чате**, local/offline в API_online_school и
VK_math_bot перед MVP/P03 явно разрешены последним ответом владельца.
[Готовый prompt](PROMPTS.md#актуальный-следующий-чат--f015-offline-в-двух-репозиториях),
[backup/возврат и границы](tasks/F01.md#финал-f014-и-handoff-f015-02112026).
Code-only backup сохранён/тестово восстановлен, bot dirty/staged не менялись;
секреты/users_data.json/server data не копировались. F01.5 код не начат; .6+ не разрешены.
Будущая live .8 — только Даниил после точного mapping/allowlist/gates; Тимур и его
данные неприкосновенны, Сергей не включён. Сейчас без live/VK/Google/Long Poll/
внешних отправок/остановки server bot/установок. Основной MVP/P03 порядок прежний.

**F01.3 local backend DONE (предыдущий этап):**
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
clean env subprocess/tripwires и diff/docs links PASS. Это fixture HTTP admission; история .1 сохранена в карточке.
**F01.2 local завершён** по отдельному явному переносу перед MVP/P03:
[результат/файлы/gates/Git-сохранение](tasks/F01.md#результат-f012-02112026).
Scoped recipients/identity/parent grants, challenges, inactive accounts/invites;
исторические72 DB+61 standalone PASS. Результат .2 сохраняется в карточке.
**F01.3 local завершён** по новому явному переносу приоритета/scope/commit-push:
[результат/файлы/gates](tasks/F01.md#результат-f013-02112026).
Dated окна/confirmed Booking, CAS/handles/immutable receipts, atomic resolve/invite/
Lesson/D04/domain outbox, own teacher API; предупреждения одиночных/серий/restore
учитывают provisional Booking, отмена условно переоткрывает исходное окно.
**115 actual DB tests PASS +61 standalone PASS**, новая guarded synthetic DB55434/
restricted role/media; retained55432/dev55431/прежняя55433 не использованы.
Connector HTTP fail-closed до .5, delivery .6 и UI .4 не реализованы. Separate owner
Это исторический результат .3; последующий статус .4/.5 и VK/P01 gates указан выше.
Git задачи: отдельная `codex/f013-booking-20261102` от `17923bb`, commit/push в
пользовательский origin после PASS; без PR/merge/deploy и переписывания истории.
Следующий вход — F01.5 offline в новом чате, по актуальному prompt выше; .4 реализована.
**Git blocker снят** последующим явным поручением сохранить накопленную работу:
новая ветка `codex/save-project-f012-20261102`; `daabcb5` — вся платформа/frontend/
документы до .2, `1456d76` — отдельно .2. Пользовательский origin,
без PR/merge/deploy. Дополнительная проверка накопленного frontend:213/40 unit PASS,
types/lint/build/scoped format PASS; исправлены только test Date/config workers,
не UI. Initial10 FAIL сохранены в SESSION_LOG. Исторические prompts F01.3/.4 выполнены; следующий F01.5 указан выше.
Остальная F01 после MVP/P03; новое исключение приоритета распространяется только на local/offline .5.
Текущий основной план T15d → T16.1/.2 → подготовка запуска прежний.
F01.0 docs gate PASS:10 docs/89 local targets+anchors; весь пакет73 Markdown/
538 file targets missing0;519 source hashes changes0, diff/whitespace PASS.
Исторический gate F01.R:16 документов/133 local targets+anchors PASS; весь пакет73 Markdown/
523 file targets без пропусков,925 source hashes без изменений, diff/whitespace PASS.
Неполные правила/квоты VK, полная актуальная правовая редакция/процедуры РКН и P01
остаются открытыми; доступные schemas не подтверждают live допуск.

## Рабочая точка и сохранность

- Internal repo `API_online_school`, branch .4 `codex/f014-teacher-booking-ui-20261102` от `75636a0`; .3 `codex/f013-booking-20261102` сохранена.
  Сохранённая baseline branch `codex/save-project-f012-20261102` не переписывается.
  Предыдущий HEAD95b3560 и ветка сохранены; накопленная работа теперь в daabcb5,
  F01.2 в1456d76. Секреты/данные/runtime artifacts остаются ignored локально.
- Внешний root main без первого commit/HEAD; не добавлять inner repo как gitlink.
- Локальный bot main/`cae7b8f175fc4b967bb9cfacd8764e3c14494f6e`, dirty/staged
  сохранены; offline code scope .5 разрешён для нового чата. Серверная версия/процессы не проверены.
- F01.2: app/router/model registry и commit-free account/workspace stages обновлены;
  только новая synthetic DB55433/ограниченная роль, контейнер после gates остановлен,
  volume сохранён. Retained preview/бот/существующие БД не менялись. Чужой dirty/
  untracked сохранены без stash/reset. Последующее поручение разрешило отдельное
  сохранение всей накопленной проектной работы и сняло Git blocker.
  E2E/live/Long Poll/VK/Google/SSH/server/install/PR/merge/deploy NOT RUN.
- Ночной порядок согласован как будущий .8; Даниил test scope разрешён ранее,
  mapping/JSON/reminders/получатели требуют проверки перед запуском. Тимур и
  настоящие пользователи/общий JSON не disposable. Сейчас live действия запрещены.

- F01.3: новый container `lgg-f013-synthetic-20261102`/55434, собственная DB/роль/media;
  после gates останавливается с сохранением synthetic volume. Только .3 commit/push
  в origin разрешены текущим запросом; UI/live/server/bot/PR/merge/deploy NOT RUN.

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
не документы/чат. Git scope выше; PR/merge/deploy/установки не разрешены.

## История

Предыдущий [STATUS до исследования01.11](history/STATUS_before_2026_11_01_vk_planning.md),
[история до handoff30.10](history/STATUS_before_2026_10_30_handoff.md),
[прежнее VK интервью](history/VK_RESEARCH_before_2026_11_01.md),
[SESSION_LOG](SESSION_LOG.md). Исторические694 PostgreSQL PASS не текущая проверка.
