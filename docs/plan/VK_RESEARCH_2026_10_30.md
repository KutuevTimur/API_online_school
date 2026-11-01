# VK: углублённое исследование · актуально01.11.2026

**Исследование/планирование выполнены; интеграция не реализована.** Принятые ответы
в [PRODUCT/F01](PRODUCT.md#будущий-f01--существующий-vk-бот--принято301001112026),
разделение решений — [D13](DECISIONS.md#d13), проект — [A14](ARCHITECTURE.md#a14),
исполняемые этапы — [F01](tasks/F01.md). Последовательность MVP/T16/P01/P03 не менялась.

## Актуальная сводка для следующего чата ·01.11

- Существующий бот прежде VK ID. Дни→явно открытые часы конкретной недели→карточка→
  confirm; бронь сразу без teacher approval. Регулярность назначает teacher.
- **Ответ владельца в этой сессии:** «Да, бронь сразу, аккаунт при приглашении».
  Confirmed бронь занимает время и видна teacher; новый User не создаётся от
  одного raw VK ID. При безопасно связанном аккаунте Lesson создаётся сразу;
  иначе при приглашении/связывании, без второй записи/дубля User.
- Второй ответ этой сессии: подтверждённая отмена возвращает исходное окно, если
  оно будущее, не закрыто teacher и не занято другой встречей. Revision меняется,
  старая кнопка не создаёт новую бронь; новую дату автоматически не открывать.
- Parent→child подтверждает teacher один раз; дальше запись без approval.
  Родитель не получает учебный кабинет/ДЗ/оценки. Невозможность написать ребёнку
  не блокирует бронь; родителю инструкция подключить сообщения ребёнка.
- События: ребёнку ДЗ/review/перенос/отмена/20min; teacher запись/решение;
  родителю прежняя заявка отмены/результат. Короткий текст+кабинет, доставка
  отдельно от доменного результата. Отписка/отвязка/права — разные состояния.
- Платформа — планируемый источник расписания; read-only Sheets — направление,
  дата переключения/частота экспорта ещё не приняты. Двусторонняя правка не
  входит в предлагаемый минимум. T18 не заменять экспортом.
- Выбран будущий ночной режим server stop→local→local stop→возврат прежнего bot.
  Даниил — разрешённый тестовый контекст со слов владельца, mapping/изоляция ещё
  не проверены. Настоящие пользователи Тимура/shared JSON/global reminders защищены.
- P01 открыт: оператор не определён, оформления/уведомлений РКН нет со слов
  владельца. Действующий бот уже имеет потоки ПД; synthetic разработка не даёт
  правового допуска live. Полные правила/квоты VK не подтверждены.
- **F01.0 local DONE02.11**: [контракт A14.7](ARCHITECTURE.md#a147-f010-local),
  [ревизии/external gates](#f010--ревизии-и-внешние-gates). F01.1 — первый код offline harness,
  отдельно разрешаемый. Перестановку разработки до MVP владелец не запрашивал.

История интервью и прежних источников сохранена
[отдельно](history/VK_RESEARCH_before_2026_11_01.md). Старые вопросы «нужно ли
подтверждение брони», «кто получает reminder», обязательный server pilot и ранний
приоритет VK ID заменены последними ответами, не являются открытыми вопросами.

## Фактическое состояние и метод проверки

Дата проверки01.11.2026, только локальные исходники/документы и открытые web sources.
Две Git roots платформы:

| Root | Ветка / HEAD / состояние |
|---|---|
| Внешняя `lgg платформа/` | main, **нет первого commit/HEAD**, untracked включая вложенный repo; не stage/не gitlink |
| Внутренняя `API_online_school/` | codex/t00-t01-environment,95b3560bdb429a06e7e5567a78ed6ef589886e4a; многочисленные dirty/untracked, сохраняются |
| Локальный `VK_math_bot/` | main,cae7b8f175fc4b967bb9cfacd8764e3c14494f6e; dirty + staged удаления старых web files/staged reminders; сохранены |

Ни один HEAD не воспроизводит working tree. Git status бота показывает защищённые
untracked файлы; содержимое не читалось. Локальный bot не объявляется серверной
версией. Его GPT содержит исторические сведения о размещении09.10, которые
нельзя превращать в актуальную проверку процесса/пути/службы.

Вход: AGENTS/GPT, README/STATUS/handoff30.10, актуальная сводка интервью;
relevant PRODUCT, D01/D02/D11/D12, A02/A03/A05/A07/A08/A12/A13, TASKS/WORKFLOW/
PROMPTS/PRIVACY/P01. AST symbol/outline/refs и исходники по найденным владельцам;
пустой AST result уточнялся rg. Исходники не импортировались. Перед выводами
прочитаны main.py и src бота; config — AST только имена настроек/сетка без значений
секретов/ID. requirements не закрепляет версии. Две UI skills прочитаны для
планирования повторного использования компонентов; новый UI не построен.

## Проверено кодом платформы

| Владелец | Наблюдение → следствие для F01 |
|---|---|
| `users/models.py:24`, `users/service.py:create_user` | User имеет обязательный username/password hash; inactive invitation создаёт Student/teacher link и stage invite, затем commit. Не годится как свободная bot-регистрация |
| `auth/auth_service.py`, `auth/exception.py`, `token_service.py` | active+activated+auth_version проверяются; роль бота/parent не меняет UserRole; VK не получает сессию через сырой ID |
| `auth/browser.py`, `refresh_tokens/service.py` | exact Origin/Content-Type/header, HttpOnly refresh, user→token lock, rotate/revoke family; transport credential должен быть отдельным, не refresh ученика |
| `account_invitations/service.py` | hash secret,72h invite/1h reset, one-use, user→token lock, consume активирует существующего User и отзывает сессии; teacher только invite своего до активации, reset admin |
| `teacher_students/service.py:link`, `check_permission/service.py` | существующего User к другому teacher подключает admin; link не даёт доступа к чужим курсам; child identity не отменяет это правило |
| `courses/service.py:personal_workspace`, `student_courses` | workspace/create имеет собственный commit и зависит от активной пары; публичные методы нельзя подряд вызвать и объявить одной транзакцией |
| `lessons/service.py:create_lesson/update_lesson` | schedule lock, active student, цена пары, LessonStudent, D04; update versioned, notifications в транзакции. Обычный create без универсального receipt |
| `lessons/repository.py:lock_schedule/overlapping_ids` | advisory lock(80408,teacher user ID); проверки интервалов возвращают warnings. Строгая бронь требует проверки под lock и учёта новых Booking |
| `lessons/service.py:preview_regular/confirm_regular` | operation receipt/revision и исключения серии, атомарный batch; добавить нематериализованные брони в preview conflicts, не создавать серии ботом |
| `teacher_students::lesson_price`, `lessons::lesson_price_kopecks` | D12 snapshot при создании; отсутствующая цена не0, архив исключён из итогов. Позднее связывание брони не должно переоценить её текущей ставкой |
| `notifications/models.py/service.py`, `homeworks/service.py`, `homework_submissions/service.py` | dedupe recipient+event, assigned/submitted/checked и move/cancel. Нет durable VK delivery; read_at и отправка VK различны; submitted edit не второе событие |
| `audit_events`, `homework_placements` | текущие audit/stage и recalc должны остаться в commit сценария, не в последующем bot HTTP |

Исходники подтверждают owners/границы, **не выполнение regression gate**.
Имена новых API/моделей в A14 — проект, сейчас этих возможностей нет.

## Проверено локальным кодом бота

| Файл | Реальный поток / риск перехода |
|---|---|
| main.py | Bot Long Poll; message_new только личный peer==sender; message_event отдельно. Startup сообщает в team chat и запускает scheduler. Ошибки могут пересылать пользовательский текст/trace в общий чат |
| handlers.py:first contact / smart_send | Первый контакт смотрит history; часть dedupe только в памяти. smart_send удаляет прежнее сообщение, не доказывает domain result. Результат HTTP нельзя выводить из наличия профиля |
| handlers.py:parent | forward или URL→users.get→link_parent без проверки teacher. Это candidate, не право читать/менять платформу; старые parent links требуют подтверждения |
| handlers.py:show_days/time/confirm | Свободно только латинская C; weekday/time из config, без даты. save_user **до** проверки ячейки, затем read/check/update не атомарно; дата следующей недели может попасть под старую кнопку |
| handlers.py:my bookings/cancel | Читает формулы всех teacher, поиск child ID; cancel payload teacher/day/time; approve пишет C, явной backend проверки владельца решения нет. Перевести в versioned CancelRequest, не отдавать эти payload в новые writes |
| database.py | Совместим со строковым legacy name; JSON read/modify/write целиком, без транзакций/lock; один child_id/parent_id. Не мигрировать и не подменять общий файл в тесте |
| google_sheets.py | credentials/Google authorization **на импорте**, широкие Sheets+Drive scopes; .sheet1. Name-search helper с пустой датой не равен my-bookings ID search |
| reminders.py | Каждую минуту now+20, все TEACHERS, regex child ID из формулы, отправка с новым random_id; нет durable delivered registry. Ночью/после restart возможны пропуски; таблица Даниила не изолирует весь scheduler |
| keyboards.py | Знакомое меню/назад/информация/связь; есть ссылка таблицы edit. Callback-кнопки отмены и текстовый confirm без stable dated ID. Сохранять путь, менять backend handles |
| config.py / chern.py / requirements.txt | Настройки токена/group/chat/JSON/teacher mapping, сетка Пн–Вс/11–20 по часам; вспомогательный файл содержит повтор teacher mapping. Значения не переносятся в документы. Зависимости vk_api/gspread/oauth2client/gspread-formatting/python-dotenv без pins |

Объём прочитанного executable кода main/src —1328 строк. Формат данных и markers —
source evidence, не факт живой таблицы. Слова владельца про «S/зелёное» не
переопределяют local parser C. Ни конфиг сервера, ни права Google/VK не проверены.

## Официальные VK-источники · проверка01.11

Только материалы владельца VKCOM; изменяемая master не замена release pin.
Схемы объявляют version5.199, это не доказательство текущей API-версии LGG.

| ID / открытый первичный материал | Подтверждено / граница |
|---|---|
| V1 [messages methods](https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/messages/methods.json) | send допускает group token; random_id для защиты от повторной отправки; peer_ids max100, message max9000; isMessagesFromGroupAllowed. Срок dedupe/квоты не установлены |
| V2 [errors](https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/errors.json) |900 blacklist,901 no permission,902 privacy;6 rate,9 flood,5 auth,7 denied. Это разные классы, не все «пользователь отписался» |
| V3 [callback objects](https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/callback/objects.json) | base group_id/event_id/v/secret, повтор event_id игнорировать; allow/deny и message_event с actor/peer. Не подтверждает SLA retries/хранение событий |
| V4 [groups methods](https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/groups/methods.json) | Есть Long Poll settings/server и Callback settings; message_new/message_event/allow/deny. Наличие schema не доказывает включённые permissions сообщества |
| V5 [message objects](https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/messages/objects.json) | from_id/peer_id/conversation_message_id и keyboard. Conversation ID относится к peer; forwarded author не доказывает полномочия parent |
| V6 [VK ID SDK](https://github.com/VKCOM/vkid-web-sdk/blob/master/README.md), [auth source](https://raw.githubusercontent.com/VKCOM/vkid-web-sdk/master/src/auth/auth.ts) | SDK содержит state/PKCE S256 и проверку window origin. Не подтверждены возможность подключения LGG/текущие договоры/равенство ID с message recipient |

**Вывод инженера:** сохранить Long Poll, заменить процессную память на inbox/
receipts, отдельный restricted API и delivery worker. Callback требует публичного
HTTPS/secret/ACK, поэтому сейчас не даёт нужного выигрыша. Протокол transport
не отменяет проверок actor/прав; permission ребёнка отдельно от parent grant.
Подписка на сообщество/parent link/VK ID login не объявляются разрешением сообщений.

**Не подтверждено:** точные RPS/суточные/месячные лимиты, действующие бизнес-квоты/
верификация, anti-spam/service-message правила, message_event ACK deadline,
Long Poll replay/retention, период random_id dedupe, полный permission scope токена,
условия приложения VK ID/возраста/ссылок. Популярное число20req/s и сведения из
неофициальных обзоров не использовать как установленный лимит LGG.
Предложенные1req/s/TTL/retry в A14 — conservative budget для fixtures, не квота.
В F01.0 оформить dated evidence и зафиксировать проверенную API-version/SDK pin
до live. Не запрашивать phone/email/photos/docs ради простой связи сообщений.

[Terms](https://vk.com/terms) и [developer rules](https://vk.com/dev/rules)01.11
не открылись: non-retryable error. Ранее dev.vk.ru заблокирован browser site-safety;
в этой сессии через браузер/другой host блокировка не обходилась. Доступный GitHub
API schema — разрешённый первичный источник, **не способ подтвердить эти правила**.
Кабинет/приложение/permissions/сообщество не создавались и не менялись.

<a id="проверка31102026-можно-ли-vk-id-и-что-оформлять-в-рф"></a>
## РФ: результат правовой проверки и открытый P01

[Ведомственный текст152-ФЗ](https://mintrud.gov.ru/docs/laws/130) повторно открыт01.11;
в заголовке перечислены поправки до24.06.2025. Он поддерживает базовые положения
о целях/основаниях, операторе-физлице, уведомлении, самостоятельном согласии,
локализации и отдельной процедуре трансграничной передачи. **Полнота действующей
редакции на01.11.2026 не подтверждена.** Нельзя назвать копию2025 актуальным
полным законом2026. Процедуры/основания/возрастные случаи и сроки — [PRIVACY](PRIVACY.md),
закрываются [P01](tasks/P01.md), не этой исследовательской записью.

Повторно01.11 [форма РКН](https://pd.rkn.gov.ru/operators-registry/notification/) и
[официальная публикация156-ФЗ](https://publication.pravo.gov.ru/document/0001202506240021)
дали timeout. Поиск по официальным доменам не дал достаточного подтверждения
актуальной процедуры/всех последующих поправок. Это открытая проверка, не отсутствие
обязанностей. Сведения предыдущего исследования о более новой редакции из
КонсультантПлюс сохранены в истории, в этой сессии не подтверждены первичным текстом.

Инженерный вывод по коду: VK subject+имя/класс/parent link/расписание относятся
к идентифицируемым людям; отсутствие паспортов или ООО не исключает вопрос ПД.
Нельзя назначить оператора по домену/серверу. Teacher confirmation parent relation
— правило продукта, а не юридическое доказательство полномочий/согласия.
Рекомендация до реального расширения: определить фактические цели/оператора,
юридически проверить сценарии13/14–17/18, основание по каждой цели, требуемые
уведомления/обработчиков/регионы. Не обещать автоматический допуск VK ID физлицу,
соответствие152-ФЗ либо отсутствие ответственности. Схема данных/меры — PRIVACY.

Google export остаётся внешним потоком даже из РФ backend. Перевод primary storage
в РФ сам по себе не разрешает копию в Google. Ни location Google, ни договор/
география получателей/субобработчиков не проверялись. Для F05.1 нужен отдельный
P01 разбор; до него только synthetic экспорт/фикстуры без Google credentials.

<a id="уточнение-владельца3110-два-сценария-и-пожелание-копирования"></a>
<a id="уточнение3110-первый-вход-будущая-демонстрация-и-оформление"></a>
## Отдельный backlog и оставшиеся решения

F04 copy selected lessons→next week — отдельный preview/receipt/конфликты с серией,
не копировать answers/review/цены старых встреч. Состав копии ещё согласуется.
F07 публичное synthetic student/teacher demo — пожелание после первого этапа VK,
режим edits/reset и порядок отдельно; ни retained preview, ни настоящие данные.
F03 до первого внешнего клиента: Organization/Membership/scoped admin и изоляция
DB/files/integrations/export, модель подписки/обработчиков отдельно. Не строить
SaaS в F01, не называть teacher isolation готовым tenant isolation.

Новых вопросов о закрытых ответах нет. Существенные пробелы с точками решения:

- F01.0 local DONE02.11: lock/API — A14.7; VK rules/quota/permission остаются
  external gate перед live. Контракт выбирает агент по исходникам; владельцу
  не предлагается выбирать таблицы/locks.
- P01: оператор/правовые основания/регионы/уведомления/retention; пока нет live допуска.
- F01.8: фактический target mapping Даниила/получателей/службы/версии и время окна;
  разрешение тестовых правок уже дано, новую общую авторизацию спрашивать не нужно,
  но текущий scope прямо запрещает запуск. Один процесс и гарантируемый возврат.
- F01.9/F05.1: дата/период прекращения прямых правок Sheets, первичная сверка старых
  записей и частота/состав экспортной копии. Рекомендуется один источник записи;
  неисправность платформы не основание подтверждать бронь по устаревшей таблице.

## Результат и проверки01.11

Документы обновлены по назначениям: PRODUCT/D13 — ответы; A14 — техническое
предложение; TASKS/F01 — зависимости/карточка; PROMPTS/WORKFLOW — следующий вход;
PRIVACY/P01 — допуск; STATUS/GPT/README — короткие указатели. Старые исследование/
STATUS сохранены в history с поправленными relative paths. Новый MASTER_PLAN нет.

Проверки docs: см. итоговую запись F01 (links/anchors/IDs/diff/source hashes).
**NOT RUN:** импорт/запуск бота, VK/Google API с ключами, Long Poll, DB tests,
миграции/seed/reset, preview/browser/E2E, SSH/server stop/deploy. Никаких учебных
изменений/ДЗ58, JSON правок, установок, Codex config, commit/push/PR/merge.
Правовая и VK доступность остаются частичными; research complete не означает
READY live, новый prompt не разрешает следующий код автоматически.

## F01.0 — ревизии и внешние gates

Публичные source reads выполнены в сессии01–02.11.2026 (Москва); запись завершена
02.11. Это snapshot доступных материалов, не утверждение latest на live дату.
GitHub commits API недоступен через web tool; SHA получены по доступным commit/
release страницам. Browser safety dev.vk.ru не обходилась.

| Evidence | Pin / подтверждение / влияние |
|---|---|
| E0 schema | [VKCOM commit 333481bd082ad747d4873ef4a77f9247097eeef0](https://github.com/VKCOM/vk-api-schema/commit/333481bd082ad747d4873ef4a77f9247097eeef0), [история](https://github.com/VKCOM/vk-api-schema/commits/master/) указывает14.04.2025; [package](https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/package.json) объявляет5.199.99, документы version5.199. Immutable pin для fixture shape, не доказательство действующей версии API сообщества |
| E1 messages | [Pinned methods](https://raw.githubusercontent.com/VKCOM/vk-api-schema/333481bd082ad747d4873ef4a77f9247097eeef0/messages/methods.json): group-token send, random_id, проверка разрешения сообщений. Размеры/типы параметров — schema, не throughput quota. Полного dedupe периода/числового ACK deadline материал не подтверждает |
| E2 events | [Pinned callback objects](https://raw.githubusercontent.com/VKCOM/vk-api-schema/333481bd082ad747d4873ef4a77f9247097eeef0/callback/objects.json): event_id и требование игнорировать повтор. Это не гарантия, что legacy Long Poll SDK всегда отдаёт ID или восстанавливает все события после restart |
| E3 permissions/errors | [Pinned errors](https://raw.githubusercontent.com/VKCOM/vk-api-schema/333481bd082ad747d4873ef4a77f9247097eeef0/errors.json), [groups](https://raw.githubusercontent.com/VKCOM/vk-api-schema/333481bd082ad747d4873ef4a77f9247097eeef0/groups/methods.json), [messages objects](https://raw.githubusercontent.com/VKCOM/vk-api-schema/333481bd082ad747d4873ef4a77f9247097eeef0/messages/objects.json). Формат/error taxonomy не доказывает выданные права токена/включённые события; кабинет не читался |
| E4 VK ID SDK, отдельный backlog | [release v2.6.1](https://github.com/VKCOM/vkid-web-sdk/releases/tag/v2.6.1) → [8ff76cfe59ea72e370c4c6c3b40712ecfd43aadd](https://github.com/VKCOM/vkid-web-sdk/commit/8ff76cfe59ea72e370c4c6c3b40712ecfd43aadd); [tag package](https://raw.githubusercontent.com/VKCOM/vkid-web-sdk/v2.6.1/package.json) version2.6.1, [pinned auth source](https://raw.githubusercontent.com/VKCOM/vkid-web-sdk/8ff76cfe59ea72e370c4c6c3b40712ecfd43aadd/src/auth/auth.ts) содержит state/S256/origin checks. Pin исследования F01.ID, не установка/выбор SDK бота |
| E5 local bot SDK | `requirements.txt` содержит `vk_api` без версии; `main.py` не задаёт api_version явно. Фактический installed SDK/server version и upstream defaults **UNVERIFIED**; код/пакеты не импортировались. Перед .5 нужен reproducible SDK/API transport pin; .1 использует fakes без SDK |
| E6 rules/quota | [Terms](https://vk.com/terms), [developer rules](https://vk.com/dev/rules) повторно non-retryable error. Полный актуальный текст, service-message eligibility, RPS/day/month, token scopes, ACK/retry/replay/retention, random_id dedupe window **UNVERIFIED**. Поиск не дал доступного первичного текста с числовыми квотами; сторонние цифры не evidence |

**Перед .5:** подтвердить поведение выбранного SDK/API в разрешённых публичных
sources и fixtures, без установки зависимостей в документационном этапе.
**Перед .8/.9:** актуализировать E0–E6, правила/квоты/разрешения и применимый P01.
Если текст доступен лишь владельцу — перед зависимым live этапом запросить
безопасную публичную ссылку/текст с датой без ключей, ID и входа в кабинет.
Сейчас решений владельца для local .0 не требуется. Даже1req/s не доказывает допуск;
не обещать exactly-once VK delivery, replay completeness или deadline ACK.

Локальный контракт завершён в [A14.7](ARCHITECTURE.md#a147-f010-local): порядок
locks, scoped DTO/errors/receipts, no nested commits, challenge/parent rights,
NULL price и past review. .0 local DONE не снимает external gates и не закрывает
P01/ручную приёмку интеграции. Правовая актуализация в этой сессии не выполнялась;
прежняя неполная проверка152-ФЗ/РКН не стала PASS.
