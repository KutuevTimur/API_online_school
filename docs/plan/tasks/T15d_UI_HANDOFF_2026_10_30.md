# Сводка существующей платформы ·30.10.2026

**Результат: локальные изменения сведены и основные проверки завершены.**
Это готовый вход в следующую рабочую сессию, **не production-релиз и не закрытие
ручных приёмок**. Новый функционал VK сейчас не исследовался и не реализовывался.
Единый дальнейший план — [TASKS](../TASKS.md), фактическая точка — [STATUS](../STATUS.md).

## Идентичность и версии

| Что | Факт этой сверки |
|---|---|
| Репозиторий | Внутренний `API_online_school/`; внешний `.git` не использовался |
| Ветка / базовый HEAD | `codex/t00-t01-environment` / `95b3560bdb429a06e7e5567a78ed6ef589886e4a` |
| Версия frontend / lock | `0.1.0` / `0.1.0`, совпадают; версия не объявлена новым релизом |
| Локальная метка состояния | `T15d-ui-local-2026-10-30`, **не Git tag** |
| Git | Существующий dirty/untracked сохранён; commit/push/PR/merge не выполнялись |
| Node / npm | **24.22.0 / 11.19.1**, существующий `.local-runtime/bin` |
| Системный runtime | Node26.0.0 / npm11.12.1 — отличается, в итоговом прогоне не использован |
| Frontend | React19.3.1, React Router8.4.0, Mantine9.7.2, Vite8.3.4, TypeScript5.9.3 |
| Браузер проверки | Playwright1.64.1, installed Chrome156.0.8078.79 |
| Python |3.14.0; FastAPI0.141.1, Uvicorn0.52.1, Pydantic2.13.4, SQLAlchemy2.0.51, asyncpg0.31.0, Alembic1.18.5 |
| Согласованность зависимостей |32 frontend dependencies/devDependencies: package/lock/installed совпали;50 Python requirements совпали; `pip check` PASS |

Установок/обновлений зависимостей не было. Инвентарь без секретов:
`frontend/.artifacts/session-handoff-versions.json` (локальный ignored файл).
Один базовый SHA **не воспроизводит** текущую незакоммиченную работу: нужен весь
сохранённый working tree. Не делать checkout/reset/clean для «приведения к SHA».

## Что уже сделано

| Область | Текущее поведение / канонические владельцы |
|---|---|
| Расписание teacher | Компактная неделя/день; planned голубой при press/drag, completed зелёный; пустые утренние строки короче; HH:00 drop, подтверждение; отдельное меню действий; cancelled скрыт из обычной сетки; versioned Undo и восстановление. `TeacherSchedulePage`, existing editor/status/series/undo owners |
| Общая оболочка | Teacher использует принятую student геометрию: mobile header48/footer49+safe-area, bell с реальным unread, teacher пункты/More. `AppShell`, `NotificationCount` |
| Teacher «Мой день» | Compact next + отдельная «К ученику»; Today без МСК в заголовке, dot+status; review жёлтый с отдельной rounded кнопкой; материалы мягко-красные/badge в тон, раскрытие/«Свернуть». `TeacherDayPage`, `TeacherToday`, `TeacherReminders`, `ReviewRows(compact)` |
| Teacher список учеников | Desktop4 filters в ряд, compact строки, красные dot+label/count для missing HW/lecture; mobile полноширинные поиск/материалы. `StudentsPage`, scoped students CSS; query/sort/IME/offset прежние |
| Teacher карточка ученика | Settings рядом с именем; последнее проведённое **сразу открыто**, конспекты доступны напрямую; independent materials, весь текст ДЗ; history controls/строки выровнены. `StudentWorkspace`, `StudentHistory`, existing `ReadFiles` |
| Общий Back | Arrow20/target44 перед LGG для student/teacher; предыдущая отличающаяся страница с native Router POP, query-only шаги пропускаются; фильтры/месяц/state сохраняются; reload/direct-entry fallback, existing dirty cancel/confirm. `PageBackButton`, `pageBack.ts`; bounded80 local URL/index/key entries в sessionStorage, без drafts/credentials |
| Предыдущие student S2/S3/S4 | История/занятие/«Мой день» имеют прежнюю локальную реализацию; новая стрелка проверена на student. Их прежние ручные приёмки **не закрыты** |

Подробные решения, прежние результаты и границы — [T15d](T15d.md),
актуальный вид/контракты — [DESIGN](../../../DESIGN.md), [PRODUCT](../PRODUCT.md),
[A12/A13](../ARCHITECTURE.md). Новый backend/API в текущем чекапе не добавлялся.

## Проверки30.10 — на закреплённом Node24

| Проверка | Результат и предел |
|---|---|
| Frontend unit | **213 PASS /40 files** |
| Types / lint / build / format / contrast tokens | **PASS**; финальные types/lint/format после правки drag test также PASS |
| OpenAPI DTO ↔ source | `api:types:check` **PASS**, export без DB connection |
| Python standalone | **26 PASS /0.79s**: browser config, schedule restore/version mocks, review queue mocks, test guard mocks. Нет DB fixtures/соединений/очистки retained DB |
| Сводный Chrome | PageBack2, teacher day, teacher shell, teacher list — **5 PASS** в первом прогоне; schedule initially FAIL, отдельно исправлен тестовый ввод и подтверждён **1 PASS /10.7s**. Не выдавать первый прогон за чистые6 PASS |
| Schedule drag input | Диагностика на HTTP fixture подтвердила native dragstart→drop16→dragend. Источник/назначение в тесте теперь центрируются вдали от edge auto-scroll и проверяются bounding boxes; assertions move/confirm/Undo/409 сохранены. Production calendar не менялся |
| Карточка ученика | Дополнительный Chrome9 состояний/captures: real empty/history/settings; HTTP notes/HW/both/long/503/no-lessons и mobile390. Axe0, overflow0, pageerrors0, source business writes0, HW58 requests0, relogins0 |
| SQL preflight | **PASS** только read-only SELECT actual DB `lgg_test`, restricted role `lgg_test_app`, engine/media guard. Не DB test suite |
| Impeccable/Premium | Последние scoped Impeccable0; Premium strict имеет **2 прежних findings** (`TeacherLessonPage:144`, `TeacherMaterials:311`) — **не PASS** |
| Документация |14 основных документов/108 локальных targets и весь пакет docs/plan69 Markdown/459 локальных targets: отсутствующих файлов0; relative links перенесённого STATUS исправлены. Это проверка путей файлов, не автоматическая проверка всех anchors |
| Git/AST | Internal root/branch/SHA сверены, `git diff --check` PASS, AST update актуален |

Локальные ignored доказательства: `frontend/.artifacts/session-handoff-gates.log`,
`session-handoff-final-checks.log`, `session-handoff-browser.log`,
`session-handoff-drag-diagnostic.log`, `session-handoff-drag-final.log`,
`session-handoff-workspace.log`, `session-handoff-python.log`,
`session-handoff-python-deps.log`, `session-handoff-db-readonly.log`;
`session-handoff-doc-links.json`, `session-handoff-all-doc-links.json`.
Browser source tests находятся в `frontend/e2e/*compact.spec.ts` и `page-back.spec.ts`;
workspace helper — ignored `teacher-workspace-verify.cjs`.

Реальные preview аккаунты использовались для GET/auth. Недостающие/мутационные
состояния — **явно обозначенные HTTP fixtures**, PATCH календаря не доходил до API.
Draft text профиля в Back-тесте отброшен без отправки. Seed/reset/миграций/учебных
записей/открытия ДЗ58 не было. Расписание может обновлять статусы по текущему времени
своим прежним серверным механизмом; тесты не откатывали данные владельца.

## Что не объявлять готовым

- Визуальная приёмка владельца конкретных экранов и прежние S2/S3/S4 остаются открыты.
- Это scoped регрессия изменений, **не полная T16**, не свежий полный PostgreSQL suite.
- Physical phones/Safari/Firefox/full200%, production backup/restore/deploy не проверялись.
- Прежние build chunk>500KB warning и2 Premium findings сохранены, не подавлялись.
- Admin/manual T15b.4 и дальнейшие gate — смотреть TASKS; ранее принятую storage
  приёмку не переоткрывать и неподтверждённые шаги автоматически не закрывать.
- D08/D09 остаются решениями перед зависимыми production шагами; D12 принят.

## Безопасное продолжение

Прочитать AGENTS → GPT → STATUS → этот файл; T15d читать по нужной секции, а не
перечитывать всю хронологию. Runtime из repo/frontend:

```sh
export PATH="$PWD/../.local-runtime/bin:$PATH"
node --version
npm --version
```

Preview5173/8019 с сохраняемыми DB/media. Если работает — не перезапускать ради
проверки. Если остановлен — [resume с прежним media](../ENVIRONMENT.md#сохранение-текущего-preview),
а не `scripts/t14e_preview.py`. Входы только в ignored login/helper files, без
копирования секретов в документы/чат. Не выполнять `npm install`, DB pytest,
`git reset/clean`, commit/push/deploy без соответствующего разрешения.

## Будущее VK — только записанные вопросы

Владелец30.10 уточнил: **пока не исследовать и не реализовывать**, сначала сверить
существующую платформу. Возможные темы отдельного обсуждения: вход/привязка VK ID,
уведомления от сообщества/бота, запись через бота с появлением занятия в платформе,
сложность/условия/правовые вопросы. Тип SSO и требования **не утверждены**, возможность
и легальность **не оценены**. Здесь нет обещания реализуемости или юридического вывода.

Следующая такая сессия начинается с короткого интервью и актуальных официальных
источников; не считать записанное разрешением на создание VK apps/сообщества,
публикацию, отправку сообщений, изменение auth/identity/schema или запуск бота.
Существующие D01/роль/привязка/изоляция остаются исходными ограничениями.
