# Документация LGG

Актуализировано01.11.2026. Факт — [STATUS](STATUS.md), единственный план —
[TASKS](TASKS.md), сводка текущей сверки — [T15d handoff30.10](tasks/T15d_UI_HANDOFF_2026_10_30.md).
[CHECKUP21.10](CHECKUP_2026_10_21.md) — исторический аудит.
Этот файл — карта документов, без собственного списка TODO.

## Обычная сессия

[GPT](../../GPT.md) + [STATUS](STATUS.md) + одна текущая карточка tasks/;
AGENTS применяется автоматически, rules_project перед кодом.
Текущий шаг и разрешение — только [STATUS](STATUS.md); шаблоны запросов —
[PROMPTS](PROMPTS.md). Не повторять завершённые T14a–c.
Весь путь/ID/зависимости — [TASKS](TASKS.md), не второй параллельный план.

| Документ | Назначение / читать по необходимости |
|---|---|
| [PRODUCT](PRODUCT.md) | Что должна делать платформа, принятые правила/границы/понятность |
| [DECISIONS](DECISIONS.md) | Принятые D01–D07/D11/D12 и открытые D08/D09 с точками решения |
| [ARCHITECTURE](ARCHITECTURE.md) | Backend инварианты; A09–A13 страницы/единый UX-контракт/API gaps/runtime owners |
| [DESIGN](../../DESIGN.md) | Принятый вид, актуальные [общий вид](assets/lgg-hybrid-overview.html)/[учебные экраны](assets/lgg-learning-sections.html), tokens и ограничения |
| [RESEARCH](RESEARCH.md) | Официальные источники, сравнение stack, точные версии/совместимость |
| [TASKS](TASKS.md) / [T14](tasks/T14.md) | Зависимости/контрольные точки; детали реализации только в карточках |
| [ENVIRONMENT](ENVIRONMENT.md) | Guard/local/test/media, не выводить секреты |
| [FILES_AND_RELEASE](FILES_AND_RELEASE.md) | File budget, ops/backup/release рекомендации; исполнение T17/T18/P02 |
| [PRIVACY](PRIVACY.md) / [P01](tasks/P01.md) | Условия допуска реальных данных, нормы перепроверить перед запуском |
| [WORKFLOW](WORKFLOW.md) / [PROMPTS](PROMPTS.md) | Проверки/Git/ручная приёмка/короткая передача Sol |
| [SKILLS](SKILLS.md) | Доступные automatic навыки, trust/permissions, proposed отдельно |
| [SESSION_LOG](SESSION_LOG.md) | Исторический журнал, включая перенесённый полный прежний STATUS |

## Исторические доказательства

[VK: исследование01.11 и ограничения источников](VK_RESEARCH_2026_10_30.md);
принятые ответы PRODUCT/D13, технический проект A14, [этапы F01](tasks/F01.md).
Реализация не разрешена, действующий порядок MVP/T16/P01/P03 прежний.

[CHECKUP_T13](CHECKUP_T13.md) — аудит до исправлений + результат T13R;
Q01–Q04 закрыты; Q05 реализован в T14a/b, Q06 — сокращение входов.
Снимки прежних README/STATUS/TASKS — [history](history/README_before_2026-10-21.md),
они не являются текущими инструкциями или дополнительными планами.
[CODE_REVIEW](CODE_REVIEW.md) — исходный snapshot веток до T00;
[TEST_BASELINE](TEST_BASELINE.md), [T00_T07_ACCEPTANCE](T00_T07_ACCEPTANCE.md) —
доказательства своих этапов. [Старый аудит](../АУДИТ.md) не источник новых требований.
Не читать все эти файлы автоматически и не трактовать старое NOT RUN как текущий статус.

Новых FRONTEND_PLAN/MASTER_PLAN/UX-CONTRACT не создавали: назначения разделены
между существующими документами, ARCHITECTURE содержит maintained UX equivalent.

История STATUS до сводки30.10 сохранена [целиком](history/STATUS_before_2026_10_30_handoff.md).
