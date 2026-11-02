# LGG — короткий вход

Рабочий репозиторий — `API_online_school`, основа dev.
1. [AGENTS](AGENTS.md): полномочия, AST Index, сохранность данных и workflow.
2. [STATUS](docs/plan/STATUS.md): текущее состояние, свежие проверки и следующий шаг.
3. [TASKS](docs/plan/TASKS.md): единственный последовательный план до реального MVP;
   открыть одну указанную в STATUS карточку. Перед кодом — [rules_project](rules_project.md).

Требования — [PRODUCT](docs/plan/PRODUCT.md), решения — [DECISIONS](docs/plan/DECISIONS.md),
контракты/общие компоненты — [ARCHITECTURE](docs/plan/ARCHITECTURE.md), вид — [DESIGN](DESIGN.md).
Последние согласованные решения сохраняются; новые уточнения записывать в эти
источники и связанную карточку, а не дублировать здесь. Неоднозначный новый UX:
один конкретный вариант → согласование → реализация по разрешению владельца.

Приоритет владельца: существующая платформа и T15d, затем T16.1/.2 и подготовка
запуска. Локальные UI-изменения28–30.10 реализованы по явным запросам; текущая
сверка — [handoff30.10](docs/plan/tasks/T15d_UI_HANDOFF_2026_10_30.md).
Storage принят; остальные ручные приёмки сохраняются. По запросу01.11 выполнено
углублённое исследование/планирование VK, без реализации/живых действий.
Принято: бронь сразу, аккаунт при приглашении; подробности PRODUCT/D13, проект A14,
источники/ограничения docs/plan/VK_RESEARCH_2026_10_30.md, этапы tasks/F01.md.
F01.0 local DONE02.11: A14.7/ревизии источников, external gates остаются;
F01.1 local DONE02.11 по явному переносу только этой задачи перед MVP/P03:
offline harness/43 tests PASS, без live; результат в tasks/F01.md и STATUS.
F01.2 local DONE02.11 по отдельному explicit приоритету: identity/parent/invite,
новая synthetic DB55433;72 DB+61 standalone PASS, retained preview не тронут.
Git blocker снят последующим поручением сохранить накопленную работу:
ветка codex/save-project-f012-20261102, daabcb5 — прежняя платформа/frontend/.1,
1456d76 — отдельно .2; детали tasks/F01.md/STATUS. F01.3 local backend DONE02.11 по новому explicit scope/приоритету/commit-push:
115 actual DB+61 standalone PASS, новая synthetic55434; windows/Booking/receipts/
atomic materialization/D04/domain outbox, без UI/live. Отдельная branch
codex/f013-booking-20261102 от17923bb; прежняя история сохранена. F01.4 код/автопроверки готовы, visual feedback положительный; полный ручной
walkthrough не заявлен. Следующий вход — local/offline F01.5 в новом чате по
PROMPTS: оба repo/приоритет явно разрешены02.11; code-only backup/возврат в F01.md.
.6+/live не разрешены; Тимур/его данные неприкосновенны, будущая live .8 только Даниил.
Правила/квоты VK и правовой допуск P01 полностью не подтверждены.
D12: архивные занятия/курсы исключены из денег и количества.
Git сохранение разрешено в текущем scope; PR/merge/deploy/установки не разрешены.
Preview содержит сохранённые данные:
не запускать seed/reset или очищающие тесты поверх него. Входы только в ignored
`frontend/.artifacts/t15b1-login.txt`, без копирования секретов в документы/чат.
