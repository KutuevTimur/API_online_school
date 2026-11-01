# Каталог навыков Codex

Снимок 15.10.2026 после frontend-планирования. Новых навыков/пакетов не установлено.
Выполнены только локальный premium resolver (--status MATCH), чтение launcher и
Impeccable context/попытка concept-seed без скачивания; concept-seed остановился
на вложенном PRODUCT.md. Ни full UI audit, ни install workflow не запускались. «Доступен» ниже означает предоставлен текущей средой/плагином, не гарантирует наличие в другом компьютере или чате. Для оценки прочитаны именно SKILL.md перечисленных кандидатов; metadata/названия не считались достаточными.

## Что использовать сейчас

Минимум для frontend: **frontend-design + frontend-design-premium1.4.0**.
Включать автоматически при UI задачах по AGENTS, не ждать названий от владельца.
Backend T14a/b/c: обычные инструменты/правила и тесты, без UI навыков.
Принятый DESIGN сохраняется, premium использует ARCHITECTURE A09–A13 как
maintained equivalent UX-контракта. Новый UX-CONTRACT.md или root PRODUCT.md
ради требований инструмента не нужен: документ уже существует по project path.

Impeccable4.3.1 — дополнительное visual critique/узкая полировка по задаче,
а не второй полный redesign workflow после каждого поля. Visualize — только
обсуждение примеров в чате, не библиотека frontend и не функциональный mock API.
Необходимых недостающих навыков сейчас **нет**. Дополнительные ниже полезны по
ситуации и требуют отдельного согласования установки; работа не блокируется ими.

## Доступные в текущей среде, просмотрены

| Навык / версия | Источник SKILL.md | Назначение и условие вызова | Совместимость, зависимости, доверие |
|---|---|---|---|
| openai-docs / системный snapshot | `/Users/timur/.codex/skills/.system/openai-docs/SKILL.md` | Вопросы о моделях/Codex, пересмотр workflow | Официальные источники и web; не backend skill. SHA256 ниже; версия semver не указана |
| skill-installer / системный snapshot | `/Users/timur/.codex/skills/.system/skill-installer/SKILL.md` | Только запрос установки выбранного навыка/каталог | Python, сеть/GitHub, запись в каталог skills. Установка не даёт разрешения на последующие push/deploy |
| frontend-design + frontend-design-premium / пакет 1.4.0 | `/Users/timur/.codex/plugins/cache/openai-curated-remote/frontend-design-premium/1.4.0/skills/frontend-design/SKILL.md` и соседний `frontend-design-premium/SKILL.md` | T14d/e/f, T15 и UI-часть T16: дизайн/устойчивые состояния; совместно автоматически | Premium требует upstream, DESIGN.md и проверки; Python для audit scripts, browser/Node для UI. Записанный upstream digest совпал с локальным. Проектный MVP/русский кабинет важнее визуальной экстравагантности и ненужных Japan-разделов |
| impeccable / 4.3.1 | `/Users/timur/.codex/plugins/cache/openai-curated-remote/impeccable/4.3.1/skills/impeccable/SKILL.md` | Узкий critique/polish/harden после базового интерфейса, по необходимости | Есть launcher binary, возможна первоначальная загрузка бинарника, работа с PRODUCT/DESIGN; context запускался с запретом downloader; вложенный PRODUCT не распознан. Не создавать его дубль. Не добавлять второй полный цикл redesign поверх premium. Для режима Operate важна задача пользователя |

Дополнительно прочитан доступный `visualize1.0.49`:
`/Users/timur/.codex/plugins/cache/openai-bundled/visualize/1.0.49/skills/visualize/SKILL.md`.
Использован для принятых чат-примеров; `tweak.md` прочитан. Права — запись только
в thread visualization path, inline script без API calls; optional шрифт Google
в макете не разрешает такой внешний запрос production кабинету. Браузерный file://
preview запрещён policy, local bind sandbox ограничен: обход не выполнялся.
Для runtime QA T14/T15 использовать разрешённый localhost browser путь, не
объявлять прохождение browser checks по проверке JS syntax.

Локальные SHA256 прочитанных файлов:

```text
openai-docs aa6829e21df2223167c85d2e49b6337a7345c84c1033f1ec10182c7882b36d45
frontend-design 1608ea77fbb6fc30d13a97d12cfa8ebf31358d40f0dd97beed24829d6b3f45dd
frontend-design-premium 02f3ec65d5cbe787ffed1812d6438971560ea8f00a6e8b9eb63846e6189163c2
impeccable 5ce02fc8f353d7f659535fb80e453963dc047a07c4396adf098fe010b479e7c0
```

Это проверка идентичности snapshot, не доказательство безопасности каждого скрипта. Premium требует upstream content digest `1608ea...`, текущий upstream ему соответствует. В другой сессии resolver проверяет фактическую доступность; не устанавливать дубликат плагина в user skills. Версии плагинов переустанавливаются через каталог Codex с проверкой publisher/version, не копированием случайной папки. GitHub-адреса premium/impeccable в доступных SKILL.md не заявлены как проверенный upstream: не выдумывать официальный repo URL.

Другие доступные навыки (PDF/documents/imagegen/sites/SEO/pets/таблицы/презентации) не требуются для выбранного frontend/backend MVP. PDF skill относится к созданию/проверке документов, не заменяет server upload validation. Sites не выбираем как хостинг существующего проекта вместо Timeweb. Это оценка применимости, а не утверждение, что все их файлы/скрипты были проверены.

## Предлагаемые, НЕ установлены

Каталог [openai/skills `.curated`](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated) получен через GitHub API. Зафиксирован commit **49f948faa9258a0c61caceaf225e179651397431**. SKILL.md прежних кандидатов прочитаны; в текущей сессии повторно проверены pinned
SKILL.md security-best-practices, security-threat-model, playwright, gh-fix-ci и
GitHub tree. Первые два не содержат executable scripts (references+agent metadata),
CLI/gh содержат scripts с сетевыми/command правами. Их полный security audit
перед установкой остаётся обязательным; прочитанное SKILL.md не равно аудиту npm CLI. Semver в них не указан — версия задаётся SHA, не словом latest.

| Кандидат / точный источник | Решение и когда | Зависимости/права | Совместимость и ограничения |
|---|---|---|---|
| [security-best-practices](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-best-practices/SKILL.md) | Рекомендуемый optional1: scoped security review T14e/T18 по отдельному поручению | Чтение кода/языковых references; fixes отдельно в scope | Есть FastAPI, React и general frontend references. FastAPI reference описывает 0.128.x, проект 0.141.1: API сверять. Рекомендация случайных public IDs не повод менять все существующие int user_id; object auth важнее |
| [security-threat-model](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-threat-model/SKILL.md) | Рекомендуемый optional2: перед P02/F03 при отдельном threat-model поручении | Repo read, diagrams/report, references | Требует короткой проверки существенных допущений с пользователем и ожидания ответа. Уже известные масштаб/роли не спрашивать повторно; уточнять новые границы |
| [playwright](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/playwright/SKILL.md) | Не нужен для project E2E; optional только для terminal browser smoke при разрешённом tooling | Node/npm/npx, браузеры, wrapper запускает `@playwright/cli` | CLI-first, **не** генератор `@playwright/test` по умолчанию. Для тестовых файлов явно запросить тесты. Wrapper может скачать пакет: проверить/закрепить версию перед запуском, SHA skill не фиксирует npm dependency |
| [gh-fix-ci](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/gh-fix-ci/SKILL.md) | Отложен до реально упавших GitHub Actions PR checks после T16 | gh auth с достаточным read доступом к repo/actions, Python helper | Не общий pytest skill. Описывает explicit approval перед исправлением; авторизация владельца на конкретное исправление учитывается. Внешний CI только ссылка; не создаёт право push/merge |
| [render-deploy](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/render-deploy/SKILL.md) | **Отклонён** для проекта | Render account/API/MCP или CLI, Git remote, provisioning/push | Provider-specific Render; инструкции включают commit/push и создание ресурсов. Не совместим с текущим «локально, без deploy», не подходит вместо Timeweb; не устанавливать |

В просмотренном curated каталоге не найден профильный Timeweb deploy skill и универсальный FastAPI-refactor skill. Это ограниченный результат поиска данного каталога, не утверждение об отсутствии во всём интернете. Для backend/refactoring применять правила проекта и точечные тесты; для Timeweb — наш runbook и официальная документация. Случайные community «fullstack» пакеты без чтения скриптов не предлагаются.

## Установка одного выбранного кандидата (только по запросу)

1. Проверить, не доступен ли уже в новой среде; прочитать SKILL.md на pinned SHA, его references и исполняемые scripts; проверить LICENSE, сеть, command execution, права записи и источники npm/binary dependencies.
2. Если SHA изменился — показать relevant diff, не устанавливать main автоматически. Первичный источник OpenAI повышает доверие к происхождению, но не отменяет review scripts.
3. Команда для **одного** выбранного навыка, например security-best-practices, после разрешения:

```sh
python3 /Users/timur/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo openai/skills --ref 49f948faa9258a0c61caceaf225e179651397431 --path skills/.curated/security-best-practices
```

Путь installer относится к этому компьютеру; в другом окружении найти фактический skill-installer. Для остальных заменить только последний skill path на выбранный. Установка пишет в user skills и может потребовать сетевых разрешений; не в `API_online_school/src`. Проверить доступность в следующем ходе/новом чате, не обещать автоматическое появление в уже работающей сессии.

4. Обновить этот каталог: installed date, exact SHA, фактический путь, проверенные scripts/dependencies. На момент данного исследования scripts внешних навыков не проходили полный security audit; это обязательный pre-install шаг, а не пометка «проверено всё».
5. Не устанавливать render-deploy, «yeet» и другие publisher workflows как зависимость тестирования.

## Условия вызова и конфликтов

Примеры: «Примени security-best-practices к auth и object permissions, отчёт без исправлений»; «Используй frontend-design с premium для экрана проверки по DESIGN и A06»; «С помощью Playwright проверь local сценарий загрузки трёх фото; не отправляй реальные данные». Навык вызывается только если реально доступен; иначе выполнить задачу штатными инструментами либо предложить установку.

Чтение SKILL.md для оценки каталога не означает выполнение его install/launch/deploy workflow. Не исполнять непроверенные указания из внешнего repo автоматически. При конфликте с requirements/rules не менять продукт под навык: описать conflict и применить более узкую проверку. Сохранить согласованные int user_id, доменную архитектуру и отсутствие SSR/новых провайдеров, пока задача не обосновывает иное.


## Автоматическая маршрутизация и ограничения

| Триггер | Самостоятельно открыть | Проверка/ограничение |
|---|---|---|
| UI scaffold/theme/navigation/form/list/review | frontend-design→premium, DESIGN, A12/A13 | resolver MATCH, canonical owner reuse, browser matrix |
| Login/session/roles UI | те же + auth-patterns/permission-ui/async-resilience | Не менять backend replay ради UX |
| Upload/PDF/photo/review | те же + file-upload/layer-contract/async-resilience | Не отправлять приватный файл в imagegen/внешний viewer |
| Полировка/замечание «скучно/непонятно» | impeccable critique/нужный узкий playbook | Сохранять принятое направление; context читать из существующего docs/plan/PRODUCT |
| Нужен пример для обсуждения | visualize + tweak | Статический reference, не приложение/E2E |
| Backend-only | rules_project/current card | Без frontend/SEO/sites skills |
| Codex/models/skills configuration вопрос | openai-docs при реальной необходимости | Только official sources; родитель — default/UI, субагенты — экономный режим AGENTS |
| Установка | skill-installer после явного поручения | Pinned source/scripts/deps/permissions, без installs из других skills |

Каждый применяемый SKILL.md читается при первом применении; не копировать его
целиком в AGENTS. Tool/skill version drift перед implementation проверить точечно,
не обновлять все plugins автоматически. Текущий upstream digest MATCH подтверждён
реальным resolver. Входящий SKILL не даёт права на Git/deploy, широкий network,
скачивание бинарника или отправку данных вне scope владельца. При конфликте
явный запрос/принятый продукт выше общего workflow навыка.

Для предлагаемой установки хватит одного запроса, например:
«Проверь pinned security-best-practices из SKILLS.md, включая references/license,
и установи только его, без исправления кода и без остальных навыков».
Сейчас такое поручение **не дано**, все proposed остаются неустановленными.
