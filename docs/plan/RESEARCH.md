# Исследование платформ и технических практик

Фактическая установленная версия/lock/runtime на30.10 — [сводка](tasks/T15d_UI_HANDOFF_2026_10_30.md).
Даты и внешние источники ниже — даты прежнего исследования; они не переобъявлены
свежими проверками. Новое исследование VK здесь не проводилось.

Актуальный технический выбор оставшегося MVP — раздел «Фронтенд: повторное исследование»
ниже. Ранние рекомендации в остальных разделах — контекст, не другой план реализации.

Проверено 15.10.2026 по открытым справкам. Демонстрационные аккаунты не создавались, приватные кабинеты не исследованы. «Успешные» здесь означает зрелые действующие продукты с документированными сценариями, а не доказанный рейтинг выручки/удержания. Наша цель — выбрать полезные паттерны для персональных занятий LGG.

## Учебные платформы

| Платформа и официальный источник | Документированный факт | Наш вывод для MVP | Что не переносить |
|---|---|---|---|
| [Moodle 5.2 Assignment settings](https://docs.moodle.org/502/en/Assignment_settings) | Разделяет due date и cut-off; поддерживает текст, файлы, комментарии и ограничения вложений | Просрочка отдельно от возможности сдать; текст+фото; явные ограничения до загрузки | Рубрики, peer review, сложные группы, многочисленные настройки попыток |
| [Google Classroom: Turn in](https://support.google.com/edu/classroom/answer/6020285?hl=en) | Есть прикрепление материалов, отправка, возврат к редактированию через unsubmit | Видимая кнопка «Отправить», список уже прикреплённых файлов и понятный статус | Не копировать блокировку сразу после отправки: у LGG правки разрешены до проверки |
| [Google Classroom: Grade & return](https://support.google.com/edu/classroom/answer/6020294?hl=en) | Проверка связана со списком работ, оценкой и выдачей результата | Очередь «На проверку», ответ+оценка+комментарий на одном экране | Возврат на доработку и настраиваемые шкалы отложены |
| [Stepik: настройки курса](https://help.stepik.org/article/54807) | Раздел «Проверка решений» собирает ожидающие проверки решения | Учитель начинает с очереди, а не ищет ДЗ по каждому занятию | Каталог продаж, сертификаты, экзамены, платные ограничения |
| [Stepik: практические задания](https://help.stepik.org/article/54796) | Документирует разные типы заданий и внешнюю проверку | Будущий банк заданий проектировать отдельно от персональной выдачи | Автопроверка и external grader не нужны для фото рукописных решений MVP |

Эти продукты не подтверждают конкретную политику срока «до следующего занятия» или LGG-долгов. Это собственные требования, проектное решение описано в A05, а не приписано Moodle/Stepik.

## Минимальные пользовательские маршруты

- Ученик: вход → ближайшие занятия/ДЗ → страница занятия → PDF → текст/фото решения → отправка → результат проверки. На телефоне добавление нескольких фото без потери предыдущих файлов.
- Преподаватель: ученики → персональный курс → создать занятие → материал и ДЗ → очередь решений → проверить. Существующего чужого ученика не искать по открытому каталогу.
- Admin: пользователи с фильтрами → выдать teacher/student → назначить второго преподавателя → общий просмотр курсов → редкое отдельное purge. Вход admin не подменяет обычный учебный workflow.
- Архив: отдельный фильтр, read-only, скачивание доступно. Отмена встречи имеет своё название и не выглядит как удаление материалов.

Рекомендация: показать срок, статус и следующую доступную операцию рядом с работой. Не делать ленту соцсети, чат, CRM и маркетинговые дашборды. Пользу измерять пилотом: ученик самостоятельно отправил 3 фото, преподаватель нашёл и проверил, второй teacher не увидел чужое.

## Технические источники и решения

| Источник, прочитан 15.10.2026 | Подтверждает | Применение / предел |
|---|---|---|
| [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html) | Явные границы transaction/commit/rollback | Одно учебное действие — одна транзакция; файловая система в неё не входит |
| [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) | Генерация даёт кандидат миграции, требует ручной проверки и имеет ограничения | Не принимать autogenerate как доказательство безопасного переноса; проверять на PostgreSQL. Сайт latest уже 1.20, проект 1.18.5 — API сверять с установленной версией |
| [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Allowlist, ограничения, проверка содержимого, безопасные имена и размещение, многоуровневая защита | Приватные файлы, лимиты до декодирования, запрет public media; MIME клиента недостаточно |
| [Pillow 12.3: форматы](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) | Чтение по содержимому; настройки WebP и metadata | Доработать уже установленный Pillow; параметры качества — наша гипотеза, не гарантия читаемости |
| [Vite guide](https://vite.dev/guide/) | SPA-шаблоны, TypeScript, dev/build | Предлагается React/TS SPA; версии Node/Vite закрепить при T14, не брать latest без lockfile |
| [Playwright Test](https://playwright.dev/docs/intro) | Автоматизация браузерных сценариев и тестовый runner | E2E именно приложения; не путать с CLI-навыком Playwright, который по умолчанию не пишет test specs |
| [Timeweb S3](https://timeweb.cloud/docs/s3-storage/manage-storage) | Приватные/публичные бакеты и управление хранилищем | Только приватный режим; регион и договор проверяются отдельно, наличие продукта не означает юридическое соответствие LGG |
| [Timeweb backup](https://timeweb.cloud/docs/cloud-servers/manage-servers/backup) | Бэкапы и снапшоты отличаются, доступны сценарии восстановления | Дополнение к согласованной копии БД+файлов; возможности конкретного сервера неизвестны |

Правовые выводы и ограничения источников — [PRIVACY.md](PRIVACY.md). Модели Codex и навыки — отдельные WORKFLOW/SKILLS, чтобы не перечитывать их при каждом backend-исправлении.

## Фронтенд: повторное исследование 15.10.2026

Официальные документы и package metadata проверены чтением, пакеты не установлены.
Подходит обычный HTTP/JSON/multipart клиент любого из вариантов; FastAPI не требует React.
Оценки удобства для одного разработчика — инженерный вывод, не сравнительный benchmark.

| Вариант | Разработка одним человеком, компоненты и тестирование | Эксплуатация / развитие | Решение для LGG |
|---|---|---|---|
| React + Vite + Mantine | Единые forms/hooks/date/select/dialog; TypeScript, Query; официальный Vitest guide. CSS Modules и theme позволяют воспроизвести выбранный дизайн | Статические файлы + существующий API; нужно поддерживать собственные auth/permissions/drafts, проверять доступность собранных экранов | **Выбран**: меньше ручной инфраструктуры компонентов, достаточно свободы для «Учебной ленты» |
| React + Vite + shadcn/ui | Компоненты входят в исходники приложения, высокая свобода; Radix/составные controls, styling и обновление скопированных компонентов становятся нашей ответственностью | Тот же простой static hosting; больше собственного UI-кода и интеграции форм/дат | Подходит, но при одном разработчике дополнительное сопровождение сейчас не окупается |
| Vue 3 + Vite + PrimeVue | Официальный Vite/TS tooling, большой набор форм/таблиц/дат, Vitest/Playwright возможны; хороший полноценный вариант | Статика + тот же FastAPI; свои Vue adapters и другая экосистема компонентов | Технически равноправен, но не даёт достаточной выгоды для отказа от уже исследованной React основы; не объявляется хуже по качеству |
| Next.js + React | Routing/data/server features, можно работать как SPA; зрелые инструменты React | Server mode добавляет Node runtime рядом с FastAPI. Static export ограничен для динамических неизвестных при сборке маршрутов и server features | Личный кабинет не использует эти преимущества; не выбираем второй серверный слой или обход static export |

Прочитанные первичные источники:
- [Mantine Vite](https://mantine.dev/guides/vite/), [Vitest setup](https://mantine.dev/guides/vitest/),
  [React 19.2+ requirement](https://mantine.dev/guides/8x-to-9x/).
- [shadcn Vite](https://ui.shadcn.com/docs/installation/vite), [подход к компонентам](https://ui.shadcn.com/docs).
- [Vue tooling](https://vuejs.org/guide/scaling-up/tooling.html), [PrimeVue](https://primevue.dev/).
- [Next SPA](https://nextjs.org/docs/app/guides/single-page-applications),
  [ограничения static export](https://nextjs.org/docs/app/guides/static-exports).

### Выбранные версии и лицензии

Источник точных patch-версий/engines/peerDependencies: официальные JSON
`https://registry.npmjs.org/<package>/<version>`; запросы `latest` выполнены 15.10,
ниже сохранён результат, а не плавающая инструкция установки. Node —
[официальный release index](https://nodejs.org/dist/index.json),
[политика releases](https://nodejs.org/en/about/previous-releases).

| Пакет | Зафиксированная версия | Назначение / совместимость |
|---|---|---|
| Node / npm | 24.22.0 LTS / 11.19.1 | Node24 удовлетворяет Vite, Router, Vitest, jsdom; не использовать Node26 Current без нужды |
| react / react-dom | 19.3.1 / 19.3.1 | Совпадающая пара; Mantine ^19.2, Query ^18 или ^19 |
| typescript | **5.9.3** | openapi-typescript требует ^5.x, typescript-eslint <6.1; latest 7.0.2 не подходит |
| vite / @vitejs/plugin-react | 8.3.4 / 6.1.2 | plugin peer Vite ^8; Node ≥22.12; compiler/experimental bundle не включать |
| react-router | 8.4.0 | Node ≥22.22, React ≥19.2.7; Data mode, без @react-router/dev/server |
| @tanstack/react-query | 5.104.3 | Серверные данные, cancellation/invalidation; не хранить копию всей БД в Redux |
| @mantine/core, hooks, form, dates | **9.7.2 каждый** | Равные версии обязательны; dates также dayjs ≥1 |
| dayjs | 1.11.23 | ru calendar locale; UTC/timezone plugins из пакета; Intl для отображения |
| lucide-react | 1.57.0 | ISC; общий набор пиктограмм без второго icon pack |
| @fontsource-variable/manrope | 5.3.0 | OFL-1.1; локальный WOFF2/кириллица, лицензия в assets, без Google CDN в production |
| openapi-typescript | 7.13.0 | Dev-only генерация типов OpenAPI 3.1; не runtime validator |
| vitest / jsdom | 5.0.5 / 30.1.3 | jsdom требует Node24 ≥24.15; Vite8 удовлетворяет Vitest peer |
| @testing-library/react / dom / user-event / jest-dom | 16.3.3 / 10.4.2 / 14.6.8 / 7.0.1 | React19 поддержан; dom10 удовлетворяет peers |
| @playwright/test / @axe-core/playwright | 1.64.1 / 4.14.0 | E2E и a11y; engines браузеров установить только при разрешённой реализации; axe MPL-2.0 |
| pdfjs-dist | 6.4.299 | Apache-2.0; lazy display/viewer + worker той же версии, локально, без публичного PDF сервиса |
| @types/react / @types/react-dom / @types/node | 19.3.0 / 19.3.0 / 24.10.1 | Typings соответствуют выбранным major; не latest @types/node26 |
| eslint / typescript-eslint / react-hooks / react-refresh | 10.12.0 / 8.71.2 / 7.1.1 / 0.5.7 | Последние два — eslint-plugin-*; все поддерживают ESLint10, TS5.9 |
| prettier | 3.9.10 | Единый format:check, не отдельный форматтер для каждой подсистемы |

Если не указано отдельно, библиотеки MIT, TypeScript и Playwright — Apache-2.0.
Лицензии транзитивных пакетов всё равно проверяются при lockfile/release. Mantine
не означает автоматическую WCAG-сертификацию экрана. Таблица — проверка metadata,
**не** успешный install/build. T14d создаёт точный package-lock, `npm ls` без peer errors,
typecheck/build/tests. При upstream security fix допускается совместимый patch с
записью причины; major/пересборка архитектуры требует отдельного обоснования.

### Точечные технические источники

| Источник | Вывод для нашего решения |
|---|---|
| [Vite8](https://vite.dev/blog/announcing-vite8), [Vite8.1](https://vite.dev/blog/announcing-vite8-1) | Поддерживаемая линия 8 и Node engines; экспериментальные режимы для большого приложения нам не нужны |
| [React versions](https://react.dev/versions) | React19 актуален; выбираем совместимую patch-пару из registry, не canary |
| [Router modes](https://reactrouter.com/start/modes) | Data mode даёт route errors и useBlocker; Query владеет данными, router не создаёт второй cache |
| [Query installation](https://tanstack.com/query/latest/docs/framework/react/installation) | React18+; browser support сверить с более строгим Mantine/PDF.js, а не по одной Query |
| [Vitest](https://vitest.dev/guide/), [Mantine Vitest](https://mantine.dev/guides/vitest/) | Provider/test setup, resize/matchMedia test shims; jsdom не доказывает работу layout/focus в браузере |
| [PDF.js](https://mozilla.github.io/pdf.js/getting_started/) | Display layer/worker; PDF preview не доверяет встроенному iframe и не раскрывает bearer в URL |
| [Web Locks](https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API) | Serial refresh между вкладками на secure context; localhost — отдельная проверка T14e |
| [OpenAPI TypeScript](https://openapi-ts.dev/introduction) | Типы из серверной схемы; schema drift проверяется в CI, runtime ошибки всё равно обрабатываются |

Нет Tailwind, Redux/Zustand, второго form framework, сложного календаря, rich editor,
Storybook или S3 SDK без задачи. Компонентные состояния сначала в Vitest/E2E и
dev-only UI gallery; Storybook можно добавить позднее при реальной потребности.


Browser bridge дополнительно сверяется с [FastAPI response cookies](https://fastapi.tiangolo.com/advanced/response-cookies/)
и [OWASP CSRF custom headers / Origin](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
Выбран custom header + exact Origin для browser cookie endpoints; SameSite только
дополнительная мера. CSRF не отменяет защиты от XSS/чужих API paths. Сценарии
missing/foreign/null Origin и cross-tab lifecycle закреплены в T14e.
