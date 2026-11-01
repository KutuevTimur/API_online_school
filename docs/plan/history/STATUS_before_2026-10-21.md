# Исторический снимок до сверки 21.10.2026

Не текущий статус и не инструкция запуска. Старые команды могут очищать данные;
использовать актуальные [STATUS](../STATUS.md), [TASKS](../TASKS.md) и [README](../../../README.md).
Текст сохранён для истории, включая противоречивые на дату снимка утверждения.

---

# Текущее состояние LGG

21.10: на странице отправки ДЗ сверху доступны материалы исходного занятия;
static/frontend69 PASS, browser этого дополнения NOT RUN, приёмка ожидает.

**21.10.2026 · Учебный UX по11 скринам — VERIFY локально, ручная приёмка ожидает.**
Автозавершение после конца; reminders только по закончившимся; общий выбор недель/
цветные дни; простой multiple upload; teacher files атомарно с grade0–5; student
lesson «задание → ответ → проверка»; компактный MyDay; read/unread и auto-close feedback.
Палитра/Manrope/общие owners сохранены. [Точный scope, файлы, проверки и приёмка](../tasks/T15b.md#учебный-ux-по11-скринам-владельца-21102026).
Уточнение21.10: из расписания ученика убраны «Активные / Архив / Все»;
там всегда активное обучение, архив доступен через курсы.

- PostgreSQL:232 PASS/1 FAIL(test URL) → targeted1 PASS; все owner rows/sequence/media
  восстановлены точно. Alembic11ffc0656a8a autogenerate/upgrade/check PASS.
- Real API обе роли3 PASS; отдельно feedback/auto-completed UI1 PASS. Frontend69 PASS,
  standalone46 PASS; typecheck/lint/format/API types/tokens/build/premium0/detect[] PASS.
- Preview5173→8019→lgg_test55432 восстановлен. Вход прежний, private helper0600 проверен.
  Owner3 ученика/5 занятий/3 курса сохранены; изолированные UX21 accounts убраны.
  Media временные OS. Не reset/fresh seed ради тестов. Dev не менялся.
- T15b.3 VERIFY, .4/D12/admin не начаты. Все открытые ручные приёмки и исторические
  FAIL/NOT RUN сохранены. Full legacy browser suite/physical devices/production NOT RUN;
  новый scoped gate не заменяет их. Без commit/push/deploy/установок.

<details>
<summary>Датированная история до текущего UX gate — не актуальные входы и ограничения</summary>

**Актуальный preview после запроса владельца20.10:** все прежние synthetic данные
удалены; один пустой учитель `teacher`, учеников/курсов/занятий/материалов/ответов0.
Ученика владелец создаёт сам. Новый вход — private helper0600, planning входы ниже
исторические и больше не действуют. Preview5173→8019 восстановлен; dev не тронут.

**Текущий факт20.10.2026: T15b.3 VERIFY локально, ручная приёмка ожидает.**
Сквозной teacher→student→review→result real synthetic API **3 PASS**:0/5,
3 фото/PDF,409 edit conflict, unknown outcome до/после commit,360px/keyboard/axe;
MyDay/полночь МСК/независимые ошибки/фильтры. PostgreSQL149 PASS, frontend68 PASS,
standalone46 PASS, статические checks/build/premium0 PASS. Teacher home — «Мой день»;
auth/home2 PASS. Preview5173→8019 восстановлен, private helper0600 с проверенными
planning teacher/student входами. Перед DB tests preview остановлен, guard PASS,
private snapshot восстановлен: все строки26 таблиц/sequence совпали.109 отсутствовавших
media восстановлены из прежних preview roots по SHA256, без overwrite; аккаунты,
owner занятия и материалы сохранены. [Evidence и чек-лист](../tasks/T15b.md#t15b3--сквозной-runtime-gate-пройден--20102026).
.4/D12 не начаты; без commit/push/deploy/install. Все прежние ручные приёмки,
исторические FAIL/NOT RUN, общий full browser/physical-device gate остаются открыты.

### История runtime-блокеров до успешного gate (не текущий статус)


**Предыдущий факт20.10.2026: T15b.3 IN PROGRESS / runtime BLOCKED.** Локальный код очереди,
проверки и «Моего дня» подготовлен; frontend68 PASS, standalone46 PASS, build/статические
checks PASS. Сквозной real API/DB/phone gate **NOT RUN**: actual SQL guard отказал
PermissionError, frontend listen5173 EPERM, browser connection refused. Preview сейчас
не подтверждён/не восстановлен. Учётки/уроки/media не сбрасывались, helper0600 содержит
прежние входы с явной отметкой непроверенности. Стартовый teacher вход пока «Ученики».
[Точный факт, ошибки и продолжение .3](../tasks/T15b.md#t15b3--локальный-код-и-блокер-runtime--20102026).
Все записи о работающем preview/PASS ниже — датированная история; они не заменяют
текущий runtime gate. .4/D12 не начаты, приёмки и исторические FAIL/NOT RUN сохранены.

Повторная диагностика20.10: SQL guard снова PermissionError, Vite снова listen EPERM.
Повторные frontend68/Python standalone46/typecheck PASS; runtime gate остаётся BLOCKED.
Код и данные в продолжении не изменялись; подробности в конце карточки T15b.

Повторный запрос20.10,22:47МСК: actual SQL PermissionError и Vite5173 EPERM снова подтверждены; frontend68/standalone46/typecheck PASS. Runtime и проверенный вход всё ещё BLOCKED; код/данные не менялись. Подробности — в конце T15b.

19.10.2026: по отдельному запросу установлен локальный AST Index v3.56.0;
структурный поиск через `./scripts/ast-index`, правила в AGENTS и
[проверки/восстановление](../AST_INDEX.md). Продуктовый scope не изменён.

Обновлено20.10.2026. T15b.2 реализована локально: нормы/недельные агрегаты и
напоминания → календарь/регулярная запись/материалы. Проверки и текущий preview —
в финальном разделе ниже и [карточке T15b](../tasks/T15b.md#t15b2--локальная-реализация--1920102026).
T08b остаётся VERIFY до ручного UI сценария владельца. T15b.3 начата по новому разрешению (текущий блокер выше); .4 не начиналась.
Прежний чекап и все незакрытые приёмки/исторические NOT RUN сохраняются.

20.10.2026 · Правило владельца: сначала основной сквозной MVP обеих ролей; код
расширяемый без лишних абстракций; простой UX/UI с осмысленными акцентами обязателен.
Приоритет и границы закреплены в TASKS/PRODUCT/AGENTS/DESIGN. Сейчас только документы;
T15b.3/.4 не начаты, приёмки и исторические NOT RUN без изменений.

## Что готово и что ещё открыто

| Состояние | Этапы и границы |
|---|---|
| Реализовано и проверено локально | Backend T00–T13/T13R, T14a–c; факты и команды в карточках. Это не production/restore PASS |
| Реализовано с техническими ограничениями | T14d/e/f, T15a.1: основа/вход/файлы/read-кабинет приняты владельцем, historical NOT RUN остаются |
| Реализовано, ожидает ручной приёмки | T15a.2 решение/фото; T15a.3 конспекты/уведомления/профиль; T15b.1 свои ученики/класс/основной personal course; T15b.2 календарь/материалы/нормы. Частичный положительный отзыв не закрывает чек-лист |
| Backend проверен, UI приёмка ожидает | T08b VERIFY: backend gate для T15b.2 пройден, сквозной UI сценарий ещё NOT RUN |
| Код подготовлен, runtime BLOCKED | T15b.3: очередь/review/MyDay; full real-API gate и ручная приёмка открыты |
| Только запланировано | D12/.4→T15c→T16; затем T17/T18/P01/P02/P03. Полная очередь/зависимости — TASKS |
| Отложено за MVP | F01–F06. Реальные ПД запрещены до P01 |

T15b.1: кликабельные строки учеников, имя/фамилия, числовой класс, вторичный логин;
поиск/класс/4 server sort до paging со stable ties. Страница ученика содержит один
основной personal course, занятия/раскрытие материалов и вторичные настройки;
legacy курсы и файлы сохранены. Вид после последней доработки **ожидает приёмки**.
[Последний teacher evidence](../tasks/T15b.md#t15b1--доработка-двух-экранов-по-повторному-поручению--16102026).

## Принятые требования и границы

- T15b.2: напоминания о занятиях без ДЗ/конспекта, фильтр/приоритет своих учеников,
  student→стандартный teacher lesson→выдача/upload с возвратом; recipient-scoped
  server aggregate/filter до paging. Правила актуальности и «не нужно» приняты
  владельцем19.10: PRODUCT §6; локальная реализация .2 — последний раздел карточки.
- Длинная история должна быть удобной; недельные группы — **предложение**, не
  утверждённый макет. Один основной personal course и legacy история сохраняются.
- Teacher «Мой день» согласован как будущее: занятия/напоминания в .2, очередь и
  полный обзор/стартовый вход после gate .3. Сейчас вход — «Ученики».
- Student подписи/выделение недели и отметки дней с занятиями — T16.1 после
  teacher/admin кабинетов. Не переставлять их вперёд.

Подробности только PRODUCT§5/6/8, ARCHITECTURE A09–A13 и карточки; D11 согласован16.10 (контракт ниже); D12 остаётся открыт. Чекап не расширяет backlog реализацией будущих API.

## Проверки чекапа

- Actual engine/session/SQL/temp-media guard PASS; Docker label lgg-test и loopback
  55432 подтверждены. До pytest synthetic8019 остановлен. Полный default
  `MODE=TEST .venv/bin/python -m pytest -q --tb=short`: **647 PASS/525.46s**.
- Node только .local-runtime: unit58 PASS; typecheck/lint/format/source API types/
  tokens/build/npm ls PASS; premium strict0 findings. Build warning chunk>500kB
  сохранён, threshold не менялся. Python AST325 и Markdown relative targets PASS.
- Первый общий Chromium34 PASS/2 FAIL: уведомления уже PASS, ошибки ожиданий
  post-create file/refetch и текущей недели расписания расследованы и исправлены.
  После исправлений **финальный общий Chromium36 PASS/2.1m**, workers1, fresh
  namespace. Desktop1280/mobile360, keyboard/axe/error/loading/offline/recovery
  и screenshots; notification/schedule desktop+360 визуально просмотрены.

Checkbox «Только непрочитанные» — ошибка синхронизации E2E с React transition;
проверяются завершённые URL/checked/data, keyboard360/reload, без product workaround.
[Причины и evidence](../tasks/T15a.md#чекап-t15a3-checkbox-уведомлений-16102026).
Новый полный pytest не стирает исторические NOT RUN в карточках. WebKit,
физические устройства, полная device/zoom matrix, production/restore/load и полный
будущий teacher→student→review→admin цикл этим не проверены. Ручные T15b.1,
T15a.2/.3 **ожидают**. [Обновлённый ручной маршрут](../MANUAL_ACCEPTANCE_T14_T15.md).

## Окружение и передача

Внутренний repo `API_online_school`, ветка `codex/t00-t01-environment`, HEAD95b3560.
Большой прежний local diff и уникальные untracked материалы сохранены. Без
commit/push/PR/merge/deploy/установок/reset/stash; внешний Git не менялся.
Node только `.local-runtime`. Dev8018/55431 и UNKNOWN DB не трогать.

[Synthetic preview](http://127.0.0.1:5173/login?returnTo=/teacher/students):
5173→8019→guarded lgg-test55432. После E2E оставлен fresh namespace; pytest закончен. Media временные OS каталоги, не production
persistence. Вход — ignored0600 `frontend/.artifacts/t14e-credentials.json`;
читаемый [актуальный вход](../../../frontend/.artifacts/t15b1-login.txt) обновлён после
final seed (0600); fresh browser login→ученик→PDF и360px PASS. Маршрут: teacher→Ученики→поиск/класс/sort→ученик с материалами
из helper→Открыть материалы→PDF; затем360px и возврат к списку. Student/profile
входы и ссылки там же, подробности — ручной маршрут.

Текущий следующий шаг — устранить runtime blocker .3; ручная приёмка T15b.2 и прежних экранов также открыта.
Датированные записи чекапа/D11/T08b ниже — история; актуальные проверки T15b.2
и входы указаны в последнем разделе.
Сохранение в GitHub — отдельный запрос, локальный результат ещё не сохранён туда.

Предыдущий подробный STATUS без потери истории перенесён в существующий
[SESSION_LOG](../SESSION_LOG.md#архив-status-перед-техническим-чекапом-16102026).

## D11 согласован · 16.10.2026

Владелец принял весь пакет: регулярность1–12 недель/default4 с ручным продлением,
preview/подтверждением, независимыми исключениями, остановкой/отдельной отменой,
атомарностью и защитой от дублей; недельная норма с исключениями/паузой и историей.
Контракт — [D11](../DECISIONS.md#d11--регулярное-расписание-и-недельная-норма-принято-16102026),
PRODUCT §5, [T08b](../tasks/T08b.md). Только документация; T08b TODO, реализация и её
проверки NOT RUN. T15a.2/.3/T15b.1 ожидают приёмки; исторические NOT RUN сохранены.
D12/напоминания T15b.2 остаются открыты. Commit/push/deploy/установок не было.


## Preview для владельца · 18.10.2026

По запросу «запусти платформу» подняты localhost5173→synthetic8019→guarded55432;
actual engine/session/SQL/temp-media preflight и Alembic upgrade head PASS.
Fresh synthetic seed, входы обновлены в ignored0600
[читаемом файле](../../../frontend/.artifacts/t15b1-login.txt) и
[JSON](../../../frontend/.artifacts/t14e-credentials.json). Старые логины не использовать.
Teacher/учебные student/admin login и scoped API через proxy PASS. У admin пока
только вход/сессия, рабочие формы T15c не реализованы. Media временные OS каталоги.
T08b IN PROGRESS по последующему разрешению: первый scoped20 PASS, migration31 PASS/
1 FAIL (fixture), финальные проверки NOT RUN — [карточка](../tasks/T08b.md#ход-локальной-реализации--запуск-preview-18102026).
Открытые приёмки/NOT RUN сохранены. Пока preview нужен владельцу, DB tests не запускать.

Browser smoke18.10: установленный Google Chrome, teacher→«Свои ученики» и
read_student→«Мой день» login/render PASS. Первый smoke ожидал неверный заголовок
«Ученики»; исправлено ожидание на фактическое «Свои ученики», product не менялся.


## T08b backend gate пройден · 19.10.2026

[T08b: результаты/команды/остаток](../tasks/T08b.md#финальные-проверки-backend--19102026):
полный default backend **675 PASS/582.22s**, scoped T08b/T08/T11/lifecycle112 PASS,
standalone unit44 PASS, frontend unit58/typecheck/source API types PASS.
Guard actual engine/session/SQL/temp-media PASS; clean/prior/rollback в suite,
upgrade head/check PASS, revision bc4873ad378e. Исправлены fixture is_deleted и
подтверждённый import cycle; прежние FAIL/ERROR evidence сохранены в карточке.

T08b **VERIFY**, backend gate .2 пройден; UI4 недели→перенос→продление/360/keyboard/
unknown POST recovery NOT RUN до T15b.2. Ручные T15a.2/.3/T15b.1 ожидают, все
historical NOT RUN сохраняются; production/restore/load этим не проверялись.
Правила напоминаний .2 приняты владельцем19.10: PRODUCT §6/T15b; код .2 ещё TODO.
Следующий шаг — T15b.2 backend норм/агрегатов и напоминаний → UI. D12 открыт до .4.

AST Index использован по новым AGENTS: outline23 строки против431 исходника сервиса;
это навигационный выигрыш, не измеренная экономия токенов сессии. [Разбор](../AST_INDEX.md#применение-в-t08b--19102026).
Fresh preview5173→8019→guarded55432, входы [helper](../../../frontend/.artifacts/t15b1-login.txt)
и private JSON обновлены19.10/0600. Login/scoped API PASS, media временные OS paths.
Во время preview не запускать очищающие tests. Ветка/HEAD прежние, большой dirty/
untracked diff сохранён; внешний Git/dev/UNKNOWN не менялись, commit/push/deploy/установок нет.

Финальный browser smoke19.10 teacher/student login+render PASS на fresh seed.

## T15b.2 локально реализована · 20.10.2026

**VERIFY, ожидает приёмки владельца.** [Карточка: изменения/evidence/остаток](../tasks/T15b.md#t15b2--локальная-реализация--1920102026).
Нормы с историей/паузой и weekly aggregates → recipient reminders/filter/sort →
teacher week calendar, явная/регулярная запись, перенос/version recovery,
материалы/ДЗ/долг/read-only архив. Начальный teacher вход остаётся «Ученики»;
T15b.3/денежная .4 и D12 не затронуты. Принятые UI tokens/Manrope сохранены.

Backend default **681 PASS/570.39s**, final scoped **102 PASS/112.27s**, standalone44
PASS; guard actual engine/session/SQL/temp-media, migration metadata/upgrade/check
PASS (подробная история восстановления revision без удаления data — карточка).
Frontend unit59 PASS, typecheck/lint/format/API types/tokens/build PASS, premium0.
Chromium последний общий **38 PASS/1 FAIL2.5m**; обнаруженная student first-save
refetch/blocker race исправлена, сценарий после fix1 PASS; final teacher filter/
lesson/back/norm1 PASS. Изолированный teacher4 PASS. Единый полный39 после последних
точечных исправлений **NOT RUN**; не выдавать составные результаты за общий PASS.
Chunk>500kB остаётся warning, official designmd CLI не установлен/NOT RUN.

Fresh [preview](http://127.0.0.1:5173/login?returnTo=/teacher/schedule)5173→8019→guarded
55432 восстановлен после всех DB tests, helper/JSON обновляются seed автоматически,
0600/git-ignore PASS. [Текущие входы](../../../frontend/.artifacts/t15b1-login.txt).
Fresh Chrome login→calendar→lesson→protected PDF/360px PASS. Media временные OS paths.
Не запускать очищающие pytest одновременно с preview. Приёмка — [§10](../MANUAL_ACCEPTANCE_T14_T15.md#10-преподаватель-t15b2-новая-приёмка-ожидает).
Ручные T15a.2/.3/T15b.1/T08b/.2 и исторические NOT RUN сохранены. Следующий шаг —
приёмка .2 и замечания в этом чате. Без commit/push/deploy/установок; GitHub отдельно.

20.10.2026 · Уточнение T15b.2: календарь преподавателя фиксирован08:00–22:00 МСК, без ночного расширения. Typecheck/lint и Chromium real API desktop/mobile360 PASS; ручная приёмка и ранее указанные NOT RUN без изменений.

20.10.2026 · Замечания T15b.2 по5 скринам: убраны подпись диапазона/дубли времени/
длительность карточек, добавлены мягкое выделение недели и recipient отметки отсутствия
материалов. Выбор ученика объединён с поиском; вторичные поля/управление свёрнуты;
недобор поясняет норму/паузу.10 ночных synthetic fixture уроков в архиве, owner данные
и прежние входы сохранены, preview5173/8019 восстановлен с прежним media/helper0600.
Frontend59 PASS/build PASS, Chrome smoke desktop/mobile360 PASS; teacher2 PASS/1 FAIL
(data collision)→regular scoped1 PASS/4.2s; premium0/detect[]. История и общий39 NOT RUN
сохранены. AGENTS закрепляет ограничение scope ради MVP; очередь .3/.4 не начаты.

Финальный gate уточнения20.10: typecheck/lint/format/API types/build PASS; standalone44 PASS/1.73s (без DB); frontend59 PASS, premium strict0. Preview и media сохранены; DB pytest и общий39 NOT RUN.

</details>
