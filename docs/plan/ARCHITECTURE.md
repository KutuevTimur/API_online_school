# Архитектура: развивать dev точечно

Актуальная архитектура и контракт интерфейса, 15.10.2026. A02–A07 описывают
инварианты реализованного backend T00–T13; будущее время раннего текста не означает,
что эти задачи TODO. Frontend/runtime — A09–A13; T14d создала локальный каркас, T14e подключила browser auth. T15a.1–3 и T15b.1–3/T08b реализованы локально; приёмка/ограничения — STATUS. Денежная .4 и admin UI остаются в TASKS.
Требования — [PRODUCT](PRODUCT.md), решения — [DECISIONS](DECISIONS.md).

## A01. Модульный монолит и локальный запуск

Один backend FastAPI, PostgreSQL, локальный приватный каталог файлов; один SPA frontend в `frontend/`. Существующие доменные слои остаются: views → service → repository → ORM. Транзакцию завершает верхний сервис сценария. Вложенные сервисы не должны независимо коммитить составной сценарий. Сохранять существующие сигнатуры где возможно; менять контракт только вместе с тестами и потребителем.

На сервере: браузер → HTTPS reverse proxy → статический frontend и `/api` backend → PostgreSQL/приватное хранилище. Один origin упрощает cookies/CORS. Секреты только в окружении. S3 адаптер — позже по тому же интерфейсу. Redis/Celery не нужны для первой локальной версии: конфигурацию Redis сделать необязательной после проверки всех ссылок. Для обслуживания очереди удаления файлов достаточно отдельной команды по расписанию, без брокера.

Frontend выбран: React/TypeScript/Vite + Mantine + React Router Data mode + TanStack Query.
Точные версии, peerDependencies и сравнение альтернатив — RESEARCH, решение D07.
Статическая SPA, без SSR/второго Node backend. Teacher desktop schedule — календарная
сетка недели с часами; student — компактная неделя с занятиями по дням без часовой
сетки. Mobile обеих ролей — переключение дней недели и занятия выбранного дня.
Форма даты/времени — общая. Базовый календарь без DnD; последующее
перетаскивание возможно только с подтверждением по PRODUCT §5 и отдельным scope. Redux не нужен.

## A02. Границы идентичности и доступа

User — общий аккаунт; Teacher/Student — существующие профили. Добавить UserRole.ADMIN и `teacher_students` с уникальностью `(teacher_id, student_id)`, active/ended timestamps. Связь даёт право преподавателю видеть минимальную карточку ученика; не даёт доступ к курсам другого преподавателя. Course.teacher_id остаётся владельцем. StudentCourse — право участия в конкретном курсе, не замена связи teacher_students. LessonStudent остаётся персональным получателем материалов.

Не добавлять organization_id во все таблицы «на всякий случай». До внешних независимых преподавателей — F03: Organization/Membership, права администратора организации, перенос LGG в одну организацию, tenant-изоляция всех запросов/файлов/интеграций. Глобальный администратор MVP не становится администратором каждого будущего клиента автоматически.

| Действие | Ученик | Свой преподаватель | Чужой преподаватель | Admin |
|---|---|---|---|---|
| Общий профиль | Свой | Минимальное чтение при активной связи | Нет | Да |
| Изменить общий профиль/пароль | Себе по auth-политике | Нет; запрос admin | Нет | Управляемый reset/редактирование с журналом |
| Создать student | Нет | Да, с автоматической связью к себе | — | Да |
| Подключить существующего student к учителю | Нет | Нет | Нет | Да |
| Создать teacher/admin | Нет | Нет | Нет | Teacher — admin; новый admin — отдельная CLI-процедура MVP |
| Учебные записи и файлы | Свои | Только собственных курсов | Нет | Да |
| Архив | Свои записи, чтение | Свои курсы, чтение | Нет | Чтение |
| Проверка / расписание | Нет | Собственный активный курс | Нет | Не отдельный учебный workflow в MVP |
| Purge курса | Нет | Нет | Нет | Явное действие и подтверждение |

Общий профиль учителя/ученика не должен открываться всем авторизованным. Списки сразу фильтруются в SQL по субъекту; проверка объекта повторяется в service для действий. Отсутствующий teacher/student профиль → отказ, никогда не `filter=None`. Любой file_id разрешается через его доменного владельца, а не только «вошёл в систему». Публичные DTO используют user_id; внутренние PK остаются в БД. Не менять ID на UUID во всём проекте ради obscurity; авторизация обязательна при любом ID.

Чужой объект возвращает согласованный 404, запрет операции на своём видимом объекте — 403, конфликт версии/состояния — 409; пустые списки — 200. Ответы не содержат hash, refresh digest, локальные пути, секреты и чужие контакты.

## A03. Auth и выдача доступа

Сначала исправить действующий bearer auth, затем в T14 согласованно подключить браузер. Предложение: одноразовое приглашение со случайным токеном, хранимым только как hash, срок 72 часа (D01 принят 15.10.2026); ссылку вручную передаёт создавший преподаватель/admin по существующему каналу. До активации login закрыт. SMTP и email-confirmation не обязательны для такого пилота; email сделать необязательным только отдельной миграцией, логин — username. Не подставлять фиктивные адреса. Не хранить пароль, выбранный учеником, в документах/логах.

Первый admin: локальная CLI-команда с интерактивным вводом, idempotent и отказом при повторной инициализации без специального режима. Мастер-пароль HTTP-регистрации закрыть. Reset: admin после внешней проверки личности выпускает одноразовую ссылку; обычный teacher чужой пароль не меняет. Политика приглашений — принятый D01 в DECISIONS.md.

Access JWT короткий (предложение 15 минут), обязательные exp/sub, проверка активности пользователя на каждом запросе. Refresh: случайный секрет, в БД digest, expires/revoked/session family; ротация под row-lock или conditional update в одной транзакции. Два конкурентных refresh не могут оба пройти. Logout сопоставляет пользователя/сессию. При смене/сбросе пароля отозвать refresh и повысить auth_version в User, проверяемую access-token dependency; блокировка немедленно запрещает login, refresh и запросы.

Login/reset/invite activation ограничивать по IP и идентификатору аккаунта с ограниченным временем задержки, generic errors и аудитом аномалий; не блокировать аккаунт навечно по одному внешнему IP. Пароль меняется самим пользователем после проверки текущего пароля либо одноразового reset. Общие изменения `is_active` доступны только admin, обычный UpdateUserData не должен принимать административные поля.

Для SPA: `/auth/browser/login|refresh|logout` POST сохраняют bearer endpoints;
JSON login/refresh содержит только access/token_type, refresh — только HttpOnly
`lgg_refresh`, SameSite=Lax, без Domain, внешний Path `/api/auth/browser`.
Max-Age ограничен фактическим expires_at строки, Secure обязателен production;
DEV/TEST HTTP допускается явной конфигурацией. Production без точного HTTPS
BROWSER_ORIGIN или с insecure cookie отказывает при старте. Все cookie POST
требуют exact Origin, `X-LGG-Request: browser` и allowlisted Content-Type
(login form-urlencoded, refresh/logout application/json); CORS wildcard отсутствует.
SPA хранит access только в памяти; boot → refresh → users/me → server role guard.
Single-flight вкладки и Web Locks `lgg-session` сериализуют все cookie mutations;
после lock проверяется несекретная logout generation. Без Web Locks — инструкция
обновить браузер, без unsafe rotation. BroadcastChannel передаёт только logout/
смену identity, без токенов. Один refresh на401; repeated401 требует reauth.
Автоповтор uncertain mutations запрещён; memory draft сохраняется только для
повторного входа того же user_id. Logout очищает текущую family по cookie без
требования access и удаляет cookie тем же Path; чужие families не затрагивает.
Смена/reset пароля сохраняют глобальный revoke/auth_version существующего backend.
Для будущего VK не отдавать пользовательские refresh-токены.

## A04. Курс, участники, архив

Персональный курс — один активный ученик в UI MVP; существующую групповую схему не удалять. Course.owner неизменяем в обычном редактировании. Создание Lesson + LessonStudent для единственного активного участника атомарно; отсутствие участника и несколько участников требуют явного ответа, не молчаливого выбора первого. Зачисление в курс не раздаёт задним числом материалы всех занятий: политика добавления в существующие занятия остаётся явной.

Добавить Lesson.is_deleted/deleted_at; обычный DELETE/archive курса и занятия только выставляет флаг. Не копировать флаг архивирования курса на все уроки: доступ вычисляется по предкам, чтобы восстановление курса не оживляло отдельно архивированные уроки. Никакой записи в архив: материалы, ДЗ, отправка, проверка и расписание read-only. Восстановление — только admin по принятому D02; откреплённых учеников автоматически не зачислять.

D02 принят 15.10.2026: открепление или истечение срока доступа к курсу переводит членство в read-only историю, записи бывшего участника остаются доступны в разделе архива, но новые занятия и материалы после cutoff не выдаются. `access_ended_at` фиксирует границу; при повторном зачислении право будущего участия восстанавливается, историческая граница не должна расширить доступ к чужим персональным LessonStudent. Teacher сохраняет чтение своей истории. Окончание teacher_students не отключает User и не затрагивает второго учителя. `expires_at` применяется одинаково к list/detail/download/write. Отдельный отзыв права чтения — admin по основанию, не побочный эффект архива.

T07: cutoff включителен по created_at персонального grant и опубликованного объекта,
не scheduled_at; наиболее ранний из expires_at/access_ended_at/deleted_at. Закрытые
перерывы повторного зачисления/восстановления teacher_students сохраняются в
EnrollmentGap, поздняя публикация в старый урок не открывается. Те же predicates
применяются к nested submission files, my-materials и lesson flags. Завершённое
участие запрещает учебные writes; отдельно прекращённый LessonStudent не
восстанавливается автоматически при re-enroll курса.

Purge курса — отдельная admin-команда API, подтверждение названием/ID, аудит. В транзакции удалить зависимости и записать задания на очистку объектов; после commit очистить файлы с повтором. Нельзя удалять файл до commit. При общей ссылке на объект не удалять используемый объект; повторная очистка безопасна. Самостоятельный purge занятия исключён из MVP по принятому D02.

## A05. Занятия и дедлайны без неоднозначности

Время — timezone-aware UTC в БД/API; ввод и отображение Europe/Moscow с явной подписью зоны. Длительность по умолчанию 55 мин. Lesson.status — scheduled/completed/cancelled (архив отдельно); public effective_status автоматически даёт completed после scheduled_at+duration по времени SQL statement; cancelled исключён, сохранённое ручное completed поддерживается. GET не меняет строку; это не подтверждение явки/оплаты. Правило21.10 в PRODUCT§5. По принятому D03 пересечения учителя показываются как предупреждение с разрешённым сохранением; учитывать длительность, исключать отменённые/архивные занятия и смежные интервалы без общего времени. Лимиты дат — предупреждение.

Постоянный call_url — Course; Lesson.call_url_override nullable; эффективная ссылка override либо Course. Только https/http по allowlist схем, не javascript/data; внешнюю ссылку backend не скачивает. Изменение курса меняет fallback, но не explicit override.

D11 принят16.10.2026: T08b создаёт обычные Lesson + LessonStudent на1–12 недель
(default4), с preview/подтверждением и ручным продлением, без scheduler.
Полные правила — PRODUCT §5 и DECISIONS D11. Нужна стабильная идентичность серии
и исходного вхождения, защищённая от конкурентного создания/продления: перенос
и отмена не воссоздаются. Граница продления — исходная граница серии.
Остановка запрещает продление и сохраняет встречи; отдельная подтверждённая отмена
затрагивает только будущие scheduled серии, включая перенесённые. Массовая смена
времени отложена. Batch атомарен вместе с D04/уведомлениями; timeout требует read
recovery. Backend gate T08b пройден19.10.2026: series/operation receipts + nullable поля
Lesson, миграция bc4873ad378e. Контракт preview/confirm/extend/stop/cancel и recovery
описан в tasks/T08b.md; UI — T15b.2, ручная сквозная проверка пока NOT RUN.

Новый UX-контракт teacher schedule — PRODUCT §5 «Уточнение MVP преподавателя»:
свободный слот → поиск своих учеников с недельной нормой/счётчиком → выбор курса
при неоднозначности → подтверждение создания; перенос в контексте недели с
подтверждением старой/новой даты. Нажатие/клавиатура являются базовыми; DnD —
отложенное улучшение с тем же серверным условным PATCH и подтверждением.

D11/T08b/T15b.2 реализуют оперативные нормы и календарь. Недельное окно —
[понедельник00:00, следующий понедельник00:00) Europe/Moscow; оперативный недобор
сохраняет active-only scheduled/completed без cancelled/архива. Не вычислять
денежную сумму по первой странице/отрисованным событиям календаря.

T15b.4/D12: nullable Integer `teacher_students.lesson_price_kopecks` — текущая цена
пары, `lessons.lesson_price_kopecks` — неизменяемый снимок одной индивидуальной
встречи. Копейки целые, >=0; NULL — неизвестно,0 — явно бесплатно. Миграция
`e738d7c0dec3` additive без backfill; downgrade отказывается терять любую цену,
включая0. Прежние записи остаются без цены. Snapshot не входит в общий lesson DTO.
Обычное создание/confirm регулярной пачки/extend читают цену под тем же schedule
advisory lock и active pair lock; все встречи пачки получают текущую цену в момент
создания. Preview ещё не создаёт встреч; повтор receipt не меняет снимки.
Перенос/длительность/ставка не переписывают снимок уже созданной встречи.
Teacher-only GET/PUT `/teacher-planning/students/{student_user_id}/price` проверяют
свою активную пару. PUT compare-and-set `expected_price_kopecks` с409 и rollback;
сериализуется с обычным/регулярным созданием. Teacher POST `/auth/register`
принимает optional `lesson_price_kopecks`, сохраняет пару/цену в одной транзакции;
admin не получает права задавать цену, public/student/admin response не расширены.
GET `/teacher-planning/weekly-earnings?week=Monday` — один SQL aggregate всей недели
с owner teacher scope, без paging/student/view filters. `total_kopecks` суммирует
только `effective_status=completed`, `completed_count` и `unpriced_count` описывают
полноту. `lesson_count` считает scheduled+completed без cancelled. По последнему
уточнению владельца21.10 общий `lesson_active_scope` teacher-календаря исключает
архив занятия/курса из суммы, количества и unpriced. Снимки остаются в данных;
завершение связи отдельно не меняет снимки. Один lesson считается
один раз без join к получателям. GET не пишет. UI показывает неполную известную
сумму и число completed без цены, не подставляет текущую ставку.

Дедлайн ДЗ **не вычисляется от текущего now**: иначе просрочка бесконечно уезжает вперёд. D04 принят владельцем 15.10.2026:

1. У Homework остаётся origin LessonStudent. Ввести `homework_placements` (homework_id, lesson_student_id, kind original/debt, created_at) с unique парой. Одна строка original; debt указывает только на Homework, никогда на другую placement, поэтому циклических ссылок нет.
2. Для каждой placement хранить `due_lesson_id` nullable и `due_at` nullable плюс журнал изменений причины. Кандидат — самое раннее неотменённое/неархивное занятие **того же курса и того же ученика** после занятия placement; tie-break `(scheduled_at,id)`. Не искать среди других курсов. Debt разрешён только для более позднего занятия этого курса, если Homework ещё не checked; для submitted показать «ожидает проверки», не дублировать в очередь проверяющего.
3. Пока кандидата нет, оба поля null, UI «До следующего занятия». Создание/перенос/отмена/архив уроков переоценивают затронутые непроверенные placements этого курса в той же бизнес-транзакции. Вставленный более ранний следующий урок становится сроком; журнал сохраняет прежнее значение.
4. Перенос связанного due-урока переносит срок. Его отмена/архив выбирает следующего допустимого кандидата; если нет — null. Состоявшийся урок остаётся историческим сроком и не исчезает из кандидатов только потому, что стал прошлым. Дальнейший ход времени сам ничего не меняет.
5. Новый долг добавляет placement и новый срок; основной список показывает одну работу с текущей последней placement, её сроком и отметкой «долг». Страница урока показывает placement своего урока; история прежних сроков видна. Это не новая попытка и не копия ответа.
6. Проверенная работа замораживает effective due_at/placement на момент проверки; дальнейшие перестановки расписания не переписывают историю оценки. Переход проверено→доработка отсутствует. Просрочка информирует, отправку не запрещает.

Тесты: нет следующего; новый следующий; перенос раньше/позже; отмена; архив; несколько курсов/учителей; равные timestamps; прошедшее непроверенное ДЗ; несколько долгов; checked; гонка переноса и проверки. Имена колонок и migration/backfill — [T11](tasks/T11.md). Кандидаты также проходят history scope: скрытые grants из разрыва участия не становятся сроком. Legacy checked и read-only работы сохраняют импортированный ручной срок без выдуманной due_lesson_id.

## A06. Решение и проверка

Использовать существующие draft/submitted/checked. В MVP одна рабочая попытка на ДЗ; существующие исторические номера/попытки сохраняются. Черновик имеет submitted_at=null. «Отправить» требует текст или готовый файл и ставит submitted. Правка submitted до проверки разрешена, версия увеличивается, очередь показывает актуальную версию; кнопка уведомляет «Изменения сохранены, преподаватель увидит обновлённый ответ». Повторная отправка идемпотентна.

Добавление файла = append; удаление отдельного file_id = явное действие; замена = upload нового + swap в одной операции. `checked` запрещает изменение текста, добавление/удаление файлов и удаление попытки. Проверка — только submitted, integer grade 0..5 и необязательный комментарий (D05 принят 15.10.2026, оценка обязательна). Перед проверкой teacher передаёт version; если student успел изменить ответ, 409 и предложение перечитать. Сервис блокирует строку/проверяет version атомарно. Итог не должен относиться к старому ответу.

Не вводить проверено/не проверено вместо оценки, новую шкалу или workflow пересдачи. Поправка ошибочной оценки преподавателем — отдельное решение после MVP, до него checked immutable.

## A07. Уведомления и эксплуатационные записи

Минимальные Notification: recipient_user_id, event_type, object_type/id, created_at, read_at, dedupe_key. События: назначена ДЗ, перенесён/отменён урок, отправлено решение (учителю), проверено (ученику). Обновление submitted не создаёт десятки уведомлений. REST список/счётчик/mark-read, polling при открытии и раз в 60 секунд активной вкладки. WebSocket, email, push, чат — вне MVP.

Создавать событие в транзакции доменного действия. Для VK позже добавить outbox/delivery с retries/idempotency, внешнюю identity-link и адаптер. Не вызывать VK из views и не позволять боту читать таблицы напрямую. В события не помещать фото/контакты/полный текст ответа; получатель заново проверяет доступ к объекту.

AuditEvent для admin: actor, action, target, timestamp, result, correlation_id; без паролей/токенов/содержимого решения. Минимальный аудит нужен до пилота, не произвольный полный event sourcing.

## A08. Будущее без обещаний «без миграций»

Банк заданий: отдельные TaskTemplate и TaskVersion (условие, предмет/тема, автор, эталонное решение отдельно и закрыто), Homework ссылается на закреплённую версию/снимок. Изменение шаблона не изменяет уже выданные ДЗ. Доступ к решению задаётся явным правилом публикации, не общим DTO. Владение и лицензии материалов проверяются до обмена между преподавателями.

ВК: linked external identity по подтверждённой привязке, минимальные permissions, дедупликация событий, отписка, отзыв доступа, повторная доставка. Нельзя привязать аккаунт только по введённому чужому user_id.

Сторонние школы: F03 до первого внешнего tenant, а не после утечки; индексы/unique с organization_id, scoped admin, перенос пользователей с одной identity и несколькими memberships, отдельный тест двух организаций. Новые сущности через обычные Alembic-миграции, не EAV-таблицу «на все будущие фичи». Расширяемость означает ясные границы и безопасные миграции, а не отсутствие будущих изменений.

## A09. Полная карта страниц MVP

Это единый UX-контракт проекта, поддерживаемый эквивалент UX-CONTRACT.md.
Отдельный документ с тем же содержанием не создавать. Визуальные значения — DESIGN.md,
политика — PRODUCT/D01–D06; здесь последствия для экранов и навигации.
Маршруты — проектное решение в рамках поручения, не существующие страницы.

| Роль / route | Содержание и главное действие | Контракт API / карточка |
|---|---|---|
| Все: `/login` | Username/пароль, показать пароль, «Войти», «Забыли пароль?» с инструкцией обратиться к admin | Browser bridge T14e; публичной регистрации/SMTP нет |
| `/activate`, `/reset-password` | Новый пароль и повтор, срок/негодная ссылка, после успеха вход | POST `/account_invitations/consume`; fragment token, T14e |
| `/` | Перенаправление после /users/me: student→/student, teacher→/teacher, admin→/admin/users | Server role; не сохранять роль как право в localStorage |
| student `/student` | «Мой день»: ближайший scheduled урок, к выполнению, последний результат; каждый блок независим | `/lessons`, новый `/homeworks/my/page`; T15a.1 |
| `/student/schedule` | Компактная неделя: только свои занятия по дням, без часовой сетки; mobile — выбор дня; Предыдущая/Текущая/Следующая неделя с выбором открытой, диапазон/МСК и отметки дней (реализовано21.10); время/курс/статус, переходы к уроку и курсу | `/lessons?from_date&to_date&view=active&status`; архив через курсы, T14a/T15a.1 |
| `/student/courses`, `/student/courses/:courseId` | Активные/архив/все; курс → занятия; в архиве причина read-only | `/courses?view`, `/courses/:id`, `/lessons?course_id`; T15a.1 |
| `/student/lessons/:lessonId` | Тема, время, effective call link, материалы и ДЗ/долг раздельно | Lesson detail + lectures/homeworks с recipient; T14b/T15a.1 |
| `/student/homeworks`, `/student/homeworks/:homeworkId` | К выполнению/на проверке/проверено, курс, долг/срок; условие, текст/фото/PDF, рабочий ответ, история, оценка | T14a/b, existing submissions/placements; T15a.2 |
| `/student/materials` | «Мои занятия»: последнее completed по scheduled_at, история по месяцам, курс/преподаватель и ленивые материалы; legacy `/student/materials/:lectureId` сохранён | Student `/lessons` с server paging/date/status; `/courses`, `/lectures`, `/homeworks`; T15d S2, browser VERIFY |
| teacher `/teacher` | «Мой день»: занятия сегодня/ближайшая встреча, работы на проверку, актуальные напоминания о ДЗ/конспекте; прямые переходы | PRODUCT§8; база T15b.2, очередь/полный обзор/стартовый route реализованы T15b.3; ручная приёмка ожидает |
| `/teacher/schedule` | Общая неделя; click свободного времени→поиск своих с нормой/счётчиком→подтверждение; регулярное время; быстрый перенос. Недельная сводка/недобор раскрываются, статистика отдельно внутри страницы; mobile — день и явная кнопка добавления | T08b/D11 и T15b.2 реализованы; статистика T15b.4/D12 реализована локально, приёмка ожидает |
| `/teacher/students`, `/teacher/students/:userId` | Свои ученики, имя/username; создать и скопировать приглашение, свои курсы выбранного ученика | `/users/students`, `/auth/register`, `/courses?student_user_id`; T14a/c/T15b.1 |
| `/teacher/courses`, `/teacher/courses/new` | Старые входы перенаправляют в `/teacher/students`; создание личного курса — из контекста ученика | POST `/courses`; T15b.1 |
| `/teacher/courses/:courseId`, прежний `/teacher/courses/:courseId/edit` | Личный курс, участник, встречи, ссылка курса, архив; редактирование во встроенных «Настройках обучения», отдельный edit URL — 404 | courses + student_courses, PATCH `/courses`; T15b.1 |
| Прежние `/teacher/lessons/new`, `/teacher/lessons/:lessonId/edit` | Отдельных маршрутов и форм нет. Создание из `/teacher/schedule`, изменение во встроенном редакторе `/teacher/lessons/:lessonId`; ученик/курс, тема, дата, время, длительность, ссылка | POST/PATCH `/lessons`; T15b.2 |
| `/teacher/lessons/:lessonId` | Материалы → выдать ДЗ → текущие ответы; добавить старую ДЗ как долг | lectures/homeworks/debts; T15b.2 |
| `/teacher/review`, `/teacher/review/:submissionId?homework_id=…` | Очередь с course/student filters; решение крупно, оценка0–5, комментарий, «Завершить проверку» | review-queue/detail/PATCH teacher; T15b.3 |
| `/admin/users`, `/admin/users/:userId` | Поиск/role/active/activated; создание teacher/student, профиль, выдача invite/reset, блокировка, квота, связи | T14c + account/status/storage/invitations; T15c.1 VERIFY локально21.10 |
| `/admin/courses`, `/admin/courses/:courseId` | Все курсы с teacher/student/archive filters; read-only занятия/материалы, restore/history access, purge | T14a/b + lifecycle; T15c |
| `/admin/lessons/:lessonId` | Чтение персональных материалов с явным получателем, restore отдельного урока | T14b + lifecycle; T15c |
| `/admin/audit` | actor/action/time/result, filters, page; без содержимого решений и секретов | `/audit-events`; T15c |
| `/notifications` | Список/непрочитанные, mark-read, проверяемый переход | notifications/unread/read/target; T15a.3 |
| `/profile` | Свой профиль, аватар, username/email optional, пароль; admin без профиля student/teacher не получает неработающую avatar форму | users/me + users/:id + password; T15a.3 |
| `/privacy`, `/help/access` | Политика после P01; инструкция восстановления/контакт из конфигурации | Запланировано P01/T17; отдельные страницы пока отсутствуют в router |
| 403 / 404 / route-error | Различимые причины, «Назад» и переход в свой кабинет | A12/T14d |

Desktop: белая верхняя навигация по роли (DESIGN); student «Мой день/Расписание/Мои курсы/
Домашние задания/Конспекты». Teacher после gate T15b.3 —
«Мой день/Ученики/Расписание/На проверку». Курсы/архив — внутри контекста ученика.
Admin «Пользователи/Курсы/Журнал действий». Уведомления и профиль — общая шапка.
Mobile student: Мой день/Расписание/Домашки/Ещё; teacher: Мой день/Расписание/
На проверку/Ещё; admin: menu drawer. «Ещё» содержит остальные разделы с текстом.
Архив — вкладка/фильтр внутри курсов, не копия кабинета. Многоролевой switch отсутствует:
сейчас UserRole один. Роль admin не превращается в учителя.

Расписание по ролям (PRODUCT §5, уточнение16.10.2026): student desktop — компактные
дни недели с карточками только фактических занятий, без часовых строк; пустой день
занимает короткое сообщение. Teacher desktop — общая календарная сетка всех его
учеников/курсов; фильтры сужают этот scope, но landing не требует заранее выбрать
одного ученика. Week/day/view сохраняются в URL, время всегда МСК. Карточка
занятия открывает lesson detail; отдельные ссылки ведут к курсу и, для teacher,
к ученику. Не вкладывать ссылки в ссылку всей карточки. В lesson/course/student
context должны быть явные переходы к связанным занятиям/материалам/ДЗ и обратно;
возврат сохраняет фильтры и выбранную неделю. Недоступные объекты не получают
ложных активных ссылок; ошибки доступа обрабатываются по A12.

Навигация: list→detail→контекстная форма; создание курса из ученика ведёт в detail
с следующим действием «Назначить занятие», создание урока из календаря — в detail
«Добавить материал/ДЗ». Редактирование курса раскрывается в detail, занятия — во
встроенном редакторе detail. Cancel сохраняет источник с прежними фильтрами.
Форма ученика/выдача приглашения — небольшой Dialog; формы курса/урока остаются
в контексте ученика, курса или расписания.
Сохранение решения/проверка остаются в контексте работы; после проверки ссылка «К очереди».
Линки на курс/урок/ДЗ работают после reload и открытия в новой вкладке, без прошлого cache.

### Уточнение T15b.1 от16.10.2026: вход через ученика

`/teacher/students` — текущий landing преподавателя до полного «Мой день» в T15b.3; server-filter класса и memory search
полного имени/логина; identity «Имя Фамилия · 10», логин вторичным текстом.
`/teacher/students/:userId` сразу показывает своё personal workspace, класс,
занятия/файлы; настройки, прежние курсы и приглашение раскрываемые.
`/teacher/courses` и `/teacher/courses/new` перенаправляют к ученикам.
`/teacher/archive` — доступ к старой истории; direct `/teacher/courses/:id`
сохраняется для прежних/архивных записей, без потери файлов.

`Student.school_grade` nullable integer1–11/check constraint; регистрация принимает
начальный класс. Узкий PATCH `/users/:userId/school-grade` (extra=forbid) проверяет
active teacher link или self/admin, сравнивает `expected_school_grade`, lock общего
профиля и audit. Общие PATCH/profile/avatar teacher прав не расширяют.
SQL class filter применяется до count/paging; full-name search остаётся scoped.
Recipient/minimal/student DTO включают класс; course DTO отдаёт safe teacher_name
через существующую selectin связь, без N+1 запросов из UI.

GET `/courses/personal/:userId` — только чтение, возвращает oldest active personal
course или null. POST того же адреса — явный start, одна transaction create+enroll;
lock уникальной teacher/student связи сериализует вкладки/повтор. Активность после
ожидания lock проверяется по clock_timestamp, не snapshot начала транзакции.
Архив/чужие/group курсы не подменяют новое личное пространство; дополнительные
legacy курсы не удаляются. После архива explicit start может открыть новое active
пространство, прежняя история остаётся архивной по D02, восстановления не происходит.
Неопределённый start → read, повтор только явно; сам POST idempotent для active space.

### План T15b.2: внимание к материалам и история ученика ·16.10.2026

PRODUCT§6 / дополнение T15b.2: student list → ученик → standard teacher lesson
с выдачей ДЗ/конспекта; обратный путь сохраняет период/фильтры. На занятии отдельные
признаки отсутствия ДЗ/конспекта, на ученике — причина внимания и server filter/
priority до paging. Признаки recipient-scoped, агрегат полный, без N+1/догадок по
неполной странице; unknown/error не равно missing. После подтверждённой mutation
обновляются lesson detail, history и student aggregate. Реализованные DTO/маршруты — `teacher_planning/models_dto.py`, `views.py`,
`teacher_students` и `lessons`; детали владельцев ниже в разделе T15b.2.
Длинная история: проработать недельные группы/выбор периода в МСК; это предложение
вида, не принятый макет. Границы напоминаний приняты19.10, уточнены21.10: PRODUCT§6.
Student week/day реализованы21.10; T16.1 проверяет полную регрессию.

## A10. Технические границы frontend

`frontend/src/app/{router,providers,theme,styles}` — каркас, locale, tokens.
`shared/api/{schema.d.ts,client,error}` — generated DTO, fetch/XHR transport,
base `/api`, 204/multipart/binary/422 parsing, timeout/AbortSignal.
`shared/ui/` — канонические controls; `shared/lib/` — время/URL/безопасные имена.
`features/{auth,schedule,courses,lessons,homeworks,materials,review,students,admin,
notifications,profile}` — use cases, страницы, queries, tests. Не вводить второй
параллельный слой entities/widgets или глобальный state manager без доказанной нужды.

React Router createBrowserRouter/Data mode: guards, useBlocker,
error boundary; TanStack Query единственный server cache. Query keys включают resource/filter/offset; notifications также actor. Общий read cache
изолируется очисткой при logout/смене пользователя вместе с memory drafts.
Никакого persist-query-cache/service worker с приватными учебными файлами в MVP.
Формы используют shared fields и локальное состояние (gallery — @mantine/form),
constraints из DTO и адаптер422; backend валидирует повторно. Асинхронные данные не перетирают dirty поля. CSS Modules поверх theme variables,
без screen-local палитры. Один loading/error/notification provider.

Локально Vite `127.0.0.1:5173`, proxy `/api` → synthetic loopback backend8019 с удалением `/api`
перед upstream. В production reverse proxy делает тот же rewrite; прямые API paths
в DTO не содержат `/api`, клиент добавляет его ровно один раз. SPA fallback только
для UI routes; `/api` никогда не возвращает index.html. Node нужен для build/tests,
не для production API. Backend и PostgreSQL версии этого исследования не меняются.

Browser baseline: текущие Chrome/Edge/Firefox и Safari/iOS Safari на дату T16,
360/390/768/1280 и 200% zoom. Поддержка старых Android/WebView/embedded VK браузеров
не заявляется; capability error даёт способ открыть обычный браузер. T16 фиксирует
фактически проверенные версии; P03 уточняет реальные устройства до расширения пилота.

## A11. Сверка UI с кодом API — 15.10.2026

Таблица ниже — сохранённый исходный snapshot перед T14, не текущий список gaps.
Актуальная сверка16.10 — в конце этого раздела; факт проверок — STATUS/карточки.

Снимок source HEAD95b3560: factory/OpenAPI54 пути/71 операция; live dev HTTP200,
54 пути. Live image после T13R не пересобран, поэтому равенство paths не доказывает
наличие исправлений в контейнере. Ни DB writes, ни pytest здесь не запускались.

| Сценарий | Что существует | Точечный остаток, владелец спецификации |
|---|---|---|
| Браузерный вход/перезагрузка | Bearer login/refresh/logout, family rotation, auth_version | Cookie bridge, Origin/CSRF, cross-tab refresh — T14e |
| Пригласить/активировать/reset | Register/issue/consume, fragment link, 72h/1h | Страницы/copy link — T14e/T15b.1/T15c |
| Активные/архив/расписание | Scoped courses/lessons lists с pagination | Q05: server view filter, student filter, deterministic sort — T14a |
| Список ДЗ | `/homeworks/my` array, placement/status, deadline | Q05: additive `/my/page`, course/status/view filters и total — T14a |
| Прямой вход в ДЗ из уведомления | Target возвращает homework_id, но GET detail нет | GET `/homeworks/:id` с безопасным context/permissions/working id — T14b |
| Урок teacher/admin: получатель | Course students есть; lesson response не содержит получателя; у исторического урока он не равен нынешнему участнику курса | GET `/lessons/:id/students` scoped recipients — T14b; не выбирать первого |
| Все конспекты | `/lectures/my` page, но LectureResponse без lesson/course/student context | Enriched DTO/detail + course filter и safe file metadata — T14b |
| Отправка/правка/проверка | Create draft, PATCH multipart, submit, version, review queue | Существующие operations использовать; UI expected_version обязателен — T15a.2/T15b.3 |
| Материалы/выдача ДЗ | POST lecture/file, POST homework title/description/один file, DELETE; edit issued homework отсутствует | Не обещать PATCH ДЗ: исправить до выдачи; удаление при ответах →409. В MVP нет произвольного редактирования выданного ДЗ |
| Долг/дедлайн | POST debts, GET placements/events | UI открывает тот же homework, выбор допустимых старых работ по T14a/b; T15b.2 |
| PDF/фото/аватары | Private bearer downloads, attachment, Range, no-store; file response не везде содержит MIME/size | File descriptors и bearer viewer — T14b/f; не использовать голый img src без авторизации |
| Admin состояния/поиск | users/students/teachers pages; PublicProfile скрывает is_active/is_activated | Admin-only list/detail DTO и search filters — T14c |
| Завершить связь teacher/student | Есть link/re-link + ended_at/gaps/scopes, HTTP end/list нет | Admin list/end endpoint по D02 — T14c; не заменять отключением общего аккаунта |
| Архив/restore/purge/history | Реализованы lifecycle endpoints и cleanup retry | UI confirmations; read_only flags/reasons — T14b/T15c |
| Уведомления/журнал | Полный recipient scope, target available, audit page | Polling/русский текст/переход — T15a.3/T15c |
| Два параллельных редактора курса/урока | Ответы version-aware, course/lesson PATCH precondition нет | Optional expected_updated_at с atomic409 — T14b; не обещать общую version систему |

Точные новые DTO/query/edge cases только в T14a/b/c/e; эта таблица — индекс.
Права не расширяются ради UI. ID в клиенте — user_id; internal PK/path/hash не выходят.
Списки считают total по тому же SQL scope/фильтру до LIMIT. Не фильтровать одну
пагинированную страницу в браузере и не обходить все уроки ради одного homework.

### Сверка текущих реализованных потоков · чекап16.10.2026

| Экран → API | Сервис → БД/файлы и текущая граница |
|---|---|
| Login/refresh/logout → `/auth/browser/*`, `/users/me` | Browser bridge → token/family services, RefreshToken/User, exact Origin/custom header; HttpOnly cookie, access в памяти. T14e реализована, WebKit остаётся NOT RUN |
| Ученики → `/users/students`, `/users/:id`, school-grade PATCH | UsersService → scoped repository/snapshot_page → User/Student/TeacherStudent. Поиск/класс/4 sort до limit, stable ties; shared grade под link/user/profile locks и expected-value409 |
| Страница ученика → `/courses/personal/:userId`, courses/lessons/recipients | CoursesService → active-link lock, personal_course, atomic create+enroll. Один основной personal, legacy сохранены; history с server paging. Lesson editor/выдача из ученика реализованы T15b.2 |
| Student день/расписание/курсы → courses/lessons/homeworks/my/page | Scoped visibility и snapshot total, status отдельно от archive; UTC API ↔ Europe/Moscow, inclusive end с microseconds. Внешняя встреча http(s), не backend fetch |
| Student ДЗ → `/homeworks/:id`, submissions/files/submit | Homeworks/SubmissionsService → recipient/placement scope, working answer и version locks; draft/submitted/checked, read-before-retry. Архив read-only, checked immutable, grade0 допустима |
| Конспекты/preview → lectures/my/detail и private download | Lectures/FilesService → LessonStudent/FileAsset, metadata DTO без storage key/path; protected bytes, MIME/Range, rollback compensation с проверкой durable refs, cleanup retry после commit |
| Уведомления/профиль → notifications/read/target, users/profile/avatar/password | Recipient-only SQL и повторная object auth; unread filter server-side. Profile self/role scope; avatar atomic, unknown-save read, password revoke. Checkbox E2E синхронизируется с завершённым URL/checked, без product workaround |

Source-generated `schema.d.ts` сверяется `api:types:check`, типы сущностей берутся из
components. Generic request не является runtime schema validator; ошибки API
обрабатывает общий client. Legacy endpoints/tools сохранены ради совместимости и
исторических smoke; отсутствие импорта из SPA не доказывает ненужность.

**T15b.4 локально реализована:** ставки/снимки стоимости — D12/.4.
Admin users T15c.1 реализована локально; оставшийся функциональный gap — admin курсы/архив/журнал, T15c.2. Regular/idempotency, нормы/агрегаты, recipient flags, teacher
lesson editor, queue/MyDay реализованы в T08b/T15b.2/.3. Не создавать их повторно. Напоминания
требуют правил актуальности по PRODUCT§6; недельные группы истории — предложение.

Сохранённые ограничения: фильтры курса в student списках загружают максимум1000
курсов (server cap); production routes пока в основном bundle, build предупреждает
о chunk>500kB. Это не потеря материалов: основные списки/прямые ссылки работают;
оценка больших объёмов и split — T16/T17, без попутного массового refactor.

## A12. Общий контракт поведения и сохранности

| Состояние | Единое поведение |
|---|---|
| Initial loading | Регион с фиксируемой минимальной геометрией, текст «Загружаем…», aria-busy; кнопка не прыгает. Skeleton только для списка/урока с совпадающей геометрией |
| Background refresh | Существующее содержимое остаётся, маленький индикатор; dirty поля не обновляются из ответа Query |
| Пусто / нет результатов | «Пока нет занятий» + доступное действие; при фильтрах — «Ничего не найдено»/«Сбросить фильтры»; student не получает teacher create |
| Ошибка GET | Inline message и «Повторить», остальные блоки работают; один automatic retry только network/5xx, не401/403/404/422 |
| Form 422/400 | Русское сообщение у поля и summary при нескольких; фокус первого неверного поля, значения сохранены; raw server trace/английский detail не показывать |
| 401 после refresh | Переавторизация поверх текущего экрана с сохранением его memory draft; только тот же user_id возвращает редактирование; другой user очищает draft. Нет бесконечного refresh loop |
| 403 / revoked access | Понятная причина, остановить mutation, перечитать capabilities; не предлагать повтор входа как исправление всех403 |
| 404 / удалённый target | «Материал больше недоступен», назад/в свой кабинет; уведомление можно прочесть, broken redirect loop нет |
| 409 version | Сохранить локальный текст/оценку, показать серверную версию отдельно; «Открыть обновлённый ответ», сравнить; не применять старую оценку к новому ответу автоматически |
| Offline / timeout | «Нет связи» либо «Не удалось подтвердить сохранение»; не объявлять успех; безопасный read/refetch перед повтором записи, не бесконечная очередь offline |
| 413/format/quota | Лимит рядом с picker, ошибка конкретного файла, остальные и текст сохранены; превышение квоты не блокирует чтение старых материалов |
| Mutation pending | Disable повторного действия, stable button, aria status; success только после server ack. Не делать optimistic send/review/purge |

Списки: default20, выбор20/50, offset/filters/sort в URL; изменение фильтра offset0;
назад восстанавливает список. Search личных имён/username хранится в памяти страницы,
не в URL/history/access logs; page/filter role/course допустимы в URL. Search300ms,
AbortSignal + stale-result guard; clear мгновенный и доступный. Даты from/to в API aware
UTC; UI Europe/Moscow, day windows без двойного включения полуночи.

Формы: label обязателен, placeholder не label; слово действия, без «ОК» и обязательных
иконок-загадок. Одна доминирующая кнопка на операцию. Поле пароля с autocomplete,
show/hide, paste/password manager разрешены. Перед уходом с dirty формы app Dialog;
реальный unload — browser lifecycle prompt, отмена не теряет форму. Длинные формы
скроллятся документом, не обрезаются ради таблицы/высоты экрана.

Ответ ученика по уточнению21.10: локальное dirty/выбор файлов → сохранение
server draft и загрузка → явное «Отправить решение». Обычной отдельной кнопки
«Сохранить черновик» нет. Отправка сохраняет содержимое и вызывает submit;
при частичном успехе точно показать draft, не «отправлено».
После submitted изменение сохраняется кнопкой «Сохранить изменения», без повторного
создания ответа/уведомления. Query invalidates homework, submissions, queue, badges.
Текст/выбранные File objects в памяти верхнего DraftProvider до подтверждения/выхода;
dirty текст не записывать бессрочно в localStorage/IndexedDB. Существующий server draft
восстанавливается после reload; ещё не сохранённый текст/неотправленные File после
reload/закрытия вкладки не гарантируются — предупреждать до ухода. Периодического
автосохранения/offline background отправки в MVP нет; это исключает скрытое создание
submissions, блокирующее удаление ДЗ Q03. При истечении сессии memory draft живёт до
повторного входа тем же человеком; при явном logout очищается после предупреждения.

Uploads: picker с multiple и необязательным drag, per-file очередь/прогресс/ошибка/
удаление/повтор; один файл в mutation для точного прогресса и сохранения остальных.
XHR измеряет upload bytes; обработка сервером — отдельный indeterminate статус,
не фиктивные100%. Исключение — итоговая teacher проверка: все выбранные review
файлы вместе с grade/comment передаются одним атомарным multipart `/review`
после confirm (PRODUCT§6). Student PATCH append с expected_version, после ack обновить version прежде
следующего файла; delete/swap тоже expected_version. При abort/timeout возможен commit:
сначала перечитать ответ/список файлов; при неясности не повторять автоматически.
Create draft восстанавливается через уникальный working answer; POST lesson/material
без idempotency key не auto-retry: показать уже созданные записи и предложить проверить,
затем осознанный повтор. Это предел MVP, не гарантия exactly-once всех create.

File preview: metadata от API, Content-Type ответа — окончательный. Bearer fetch blob,
object URL только в памяти, revoke on close/logout; PDF.js lazy worker local, страницы
по требованию, page count/zoom/клавиатура/download. Фото object-fit contain, zoom
кнопками/жестом, листание с названиями; никаких base64/PDF в URL/token query.
Не открывать внешний viewer с ученическим файлом. Повреждённый/неподдержанный PDF —
понятный fallback download; PDF.js scripting/actions отключены. На телефоне не
настаивать на встроенном browser PDF. Attachment Content-Disposition не менять глобально.

T15d B: общий `features/courses/ReadUI.tsx::ReadFiles` сохраняет все остальные
query-параметры и `location.state` (включая returnTo/studentListSearch). Открытие
добавляет entry, листание заменяет её, закрытие возвращает в исходную entry;
для прямого preview URL без локального origin — replace без preview-параметра.
Форма остаётся смонтированной; Mantine возвращает фокус на opener.

T15d E2: `ReadFiles embedded` используется только в teacher ReviewForm для решения.
При desktop≥1024 он монтирует shared `FilePreviewBody`; narrow сохраняет fullscreen.
Любой fullscreen preview key отключает inline, direct multi-key URL использует
последний key. Новое открытие заменяет только preview keys, сохраняя остальной
URL/state; paging/close/history из B прежние. Один PDF pipeline/одна активная body,
file/page/zoom живут в памяти ReadFiles без Blob storage, остальная форма не
размонтируется. `FilePreviewBody` владеет fetch/abort/destroy/objectURL и PDF pages,
ResizeObserver подгоняет лист под фактический контейнер; render/text tasks отменяются
при смене страницы/масштаба/ширины. Same ID/URL descriptor не перезапрашивается при
новой ссылке объекта. Fullscreen и embedded одинаково проверяют окончательный MIME,
лимит/ошибки/скачивание; view capabilities и API мутаций не расширены.

T15d S1 (23.10): PDF — непрерывная лента, geometry placeholders всех страниц,
canvas/text только viewport + соседние области; выделенные/сфокусированные страницы
удерживаются до освобождения. Metadata читается последовательно без raster всех страниц;
при ошибке geometry одной страницы fallback размера и локальный retry рендера.
На canvas максимум4M backing pixels (с округлением), DPR≤2; при уходе страницы
cancel render/text, обнуление canvas и PDFPageProxy.cleanup. Worker/document один
на активную body, transport/MIME/20МиБ/скачивание прежние. Code-only lazy import
PDF.js общий, после ошибки импорта retry снова доступен; PDF данные не кешируются глобально.
ReadFiles хранит page/zoom + fractional offset/горизонтальную позицию в памяти для
обеих ролей: resize/zoom/inline↔fullscreen восстанавливает anchor. Выбор файла —
из исходного списка; шапка shared viewer без file/page стрелок. Закрытие/Back/focus,
query keys condition/solution/review/material и dirty forms остаются прежними.

Архив: постоянная подпись read-only и причина; оставить открыть/скачать/историю,
убрать upload/review/schedule writes. Отмена занятия не архивирует материалы.
Удаление ДЗ с ответом →409 и объяснение; очищать/удалять ответ ради обхода запрета нельзя.
Проверка0–5: явный выбор без default оценки, 0 допустим; перед commit сообщить,
что результат неизменяем, final Dialog с оценкой/учеником. Ошибка/409 не закрывает форму.
Архив/доступ confirm с последствиями, purge typed course_id/name; cancel безопасен.
Undo только если есть честный inverse API и права; teacher не получает fake restore.

Уведомления: polling60s активной вкладки и после focus/mutation; hidden/offline pause.
Mark read при явном открытии, затем target с повторной авторизацией; available=false
остаётся на списке с сообщением. Для homework/submission direct routes не требуется
открытый ранее курс. Submitted edit не рисует второе уведомление.

T15d owner material clarity22.10: MaterialUploadQueue optional pickerTarget
перемещает только existing file picker в header через React portal, сохраняя
один input/смонтированную queue и upload contract. Материал status/action используют
один GET reminder, not-needed action теперь видим без details; PATCH flags прежние.
Цвет — presentation подтверждённых has/not-needed flags, а не локального выбора
файла; pending/unknown/read error и archive не получают success/missing заливку.

## A13. Канонические владельцы и доступность

PageBack30.10: AppShell бренд-группа включает PageBackButton; shared lib/pageBack
владеет validated local origins/parent map/planner. Bounded80 sessionStorage ledger
lgg.page-back.v1 хранит role + router index/key/local URL, без route state/drafts/
секретов/файлов. Login/public/admin сбрасывают ledger; role mismatch/invalid data/
storage errors дают fallback. Предыдущая отличающаяся pathname с меньшим browser
idx → navigate(-delta), что сохраняет canonical state/ScrollRestoration. Query-only
шаги и будущие entries не выбираются. Explicit origin studentHistoryReturnTo/returnTo
валидируется own role/shared account routes; teacher student parent переносит
studentListSearch. Fallback replace передаёт restoreHistoryScroll, без навигации
на внешний origin/чужую роль. Все переходы Router, поэтому DirtyFormGuard не
обходится. ReadFiles/FilePreview и контекстные ссылки прежние. Backend не меняется.

Teacher roster29.10: StudentsPage/studentListPage CSS owns compact layout and
missing_homework/missing_lecture presentation; DataList/SelectField/FormField owners
прежние. No query/path/rowState/search debounce300/IME/offset/sort changes. Explicit
field root classes поддерживают responsive span независимо от DOM Mantine dropdowns.

Teacher workspace29.10: StudentDetail передаёт existing header через optional heading
в StudentWorkspace, где сохранён settings ref/scroll/focus owner. StudentHistory
имеет локальный teacherWorkspaceHistory CSS scope и Lucide headings/status styles;
MaterialFiles/ReadFiles/LessonLink/SelectField/useListState remain canonical.
Latest completed/viewall/desc/cutoff, month/paging/expanded/file URL и returnTo
не меняются; новый backend owner/API/permission/сохранение данных отсутствуют.

Teacher day refinement29.10 supersedes earlier compact-row note: ReviewRows(compact)
render plain list items + independent LinkButton(reviewPath), no nested/whole-row
links; default still DataList review. Reminders collapse owns expanded=false and
useListState.update(offset0), without DB mutation. Today status styling consumes
existing status and upcoming id; no clock/status computation changes. Shared token
materialMissingBadge added with DESIGN/contrast pair; planned uses existing lgg8.

Teacher day29.10: TeacherDayPage собирает existing TeacherToday/TeacherReminders
и ReviewRows(compact); новый compact вариант сохраняет reviewPath/DataList одну
семантическую ссылку, а default full queue DOM/status/username прежние через
ReviewInfo fragment. TeacherReminders overview сохраняет limit/offset/expanded/
Pages, lesson/student query и returnTo; навигационные действия через LinkButton.
CSS локален teacherDay/dayReviewList; новые backend owner/API/permission отсутствуют.

Teacher shell29.10: AppShell остаётся единым владельцем roleNavigation/current/More/
Back; общий NavIcon содержит teacher/student пути. CSS `:is(.studentShell,
.teacherShell)` переиспользует принятую компактную геометрию и визуальные значения
ученика без копирования; admin вне этого варианта. Teacher footer использует
существующие day/schedule/review пути и короткую подпись «Проверка». NotificationCount
с existing badge/GET/poll/recovery переиспользован в teacher header; API/permissions/
backend не меняются. Native popup/keyboard/Back проверяются в Chromium, unit — role
isolation/маршруты; shared student history contract сохранён.


Teacher schedule28.10: `lessonChanges.changeLesson` — общий versioned PATCH для
LessonEditor/LessonStatusDialog/useLessonUndo; `previewRegularChange` общий для
карточки урока и календаря, RegularDialog остаётся владельцем preview/confirm/recovery.
Calendar mode LessonEditor использует existing DateField/SelectField, часы08–21;
drag передаёт только началоHH:00. Быстрый move PATCH меняет только scheduled_at,
остальные поля/цена/идентичность/исходное вхождение серии сохраняются.
Undo — компенсационный PATCH с updated_at подтверждённого результата и inverse
только изменённого поля.409/нет связи не дают автоматического повторения или
ложного успеха. Server check/lock/placements прежние; cancelled→scheduled теперь
атомарно создаёт `lesson_restored` через existing notification pipeline (также
для cancelled→completed при возврате прошлого занятия). Старые
уведомления не удаляются. Нет нового endpoint/schema/migration/audit timeline.
FeedbackProvider владеет optional async action/busy/ack/error/expiry, default toast
прежний. Возврат доступен15 секунд; нет batch restore/Undo для серии или архива.
HTTP fixtures проверяют UI mutations отдельно от настоящего read-only preview.
После истечения toast cancelled можно восстановить тем же StatusDialog через
фильтр/меню или карточку урока, с подтверждением/version guard. При разрешённом
повторе после conflict/read recovery LessonEditor отдаёт Undo именно перечитанный
before, не устаревший исходный. Menu portal target=#main сохраняет landmark и
не обрезается внутренним calendar scroller; initial focus placeholder отключён,
работают штатные Mantine item focus/keyboard/return.
Уточнение28.10: AppShell main имеет business variant teacherScheduleMain строго
role=teacher/path=/teacher/schedule и desktop≥1024. Ни другие страницы, ни общий
document scroll owner не меняются. calendarSlotHeights вычисляет единый набор14
высот по всем видимым занятиям недели: пустые08–11 по44, остальные88; axis и все
дни используют тот же набор CSS variables, не отдельные временные шкалы.
DnD по-прежнему получает целевой час от строки, не от деления pointerY на88:
тонкая строка тоже даёт HH:00. Edge scroll — один RAF цикл только при drag у края,
скорость учитывает elapsed frame; stop/drop/Escape/unmount останавливают цикл,
на границе scroll он не крутится впустую. Query/week/slot inputs memoized; RAF не
запускает React render на каждом кадре. Desktop breakpoint использует общий
Mantine useMediaQuery; mobile не предлагает native drag. Loading footprint —
calendarRegion, без фиксации высоты общего shell или замены данных прошлой недели.

Ниже владельцы: T14d создала базовые primitives; upload/preview и auth/drafts создаются T14f/e.
Следующие карточки переиспользуют, нельзя добавлять screen-local аналоги.

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Scrollbar | `app/theme.ts`, `app/styles.css` | DESIGN / A12 | DESIGN→theme→Mantine/CSS Modules; visible scrollbars, forced colors, no token drift | T14d component + browser; последующие потоки по карточкам |
| Shell/navigation | `app/router.tsx`, `shared/ui/AppShell.tsx` | DESIGN / A12 | Student/Teacher/Admin, mobile menu, focus/URL restoration | T14d component + browser; последующие потоки по карточкам |
| Form | `shared/ui/FormField.tsx`, `ErrorSummary.tsx`; @mantine/form | DESIGN / A12 | create/edit/draft, noValidate, field labels/422, autosize textarea resize:none | T14d component + browser; последующие потоки по карточкам |
| Select/Listbox | `shared/ui/SelectField.tsx` via Mantine Select | DESIGN / A12 | Authored popup, localized, searchable student/course, keyboard/clear/collision | T14d component + browser; последующие потоки по карточкам |
| Date | `shared/ui/DateTimeField.tsx` (DateField / DateTimeField) via Mantine dates + typed HH:mm | DESIGN / A12 | ru labels/dayjs, МСК→UTC roundtrip; no timezone guess from device | T14d component + browser; последующие потоки по карточкам |
| Tables/paging | `shared/ui/DataList.tsx`, `Pagination.tsx` | DESIGN / A12 | Native table desktop/list mobile; T15b student linked-row variant, server sort/total20/50. Bulk selection N/A MVP | T14d component + browser; последующие потоки по карточкам |
| Toast | `shared/ui/ConfirmDialog.tsx`, `InvitationDialog.tsx`, `FeedbackProvider.tsx` | DESIGN / A12 | normal/access/purge/review; focus trap/Escape/return, inline error + live region | T14d component + browser; последующие потоки по карточкам |
| Async/error/status | `shared/ui/AsyncState.tsx`, `StatusBadge.tsx` | DESIGN / A12 | initial/refresh/empty/no-results/error/offline/readonly; русский текст | T14d component + browser; последующие потоки по карточкам |
| Upload/preview | `shared/ui/UploadQueue.tsx`, `FilePreview.tsx`/`FilePreviewBody`, `AvatarEditor.tsx`; `shared/api/files.ts`, `shared/lib/uploadQueue.ts` | DESIGN / A12 | Per-file recovery/photo/PDF/avatar; keyboard/touch and explicit download | T14f component + browser + real API |
| Plain-text links | `shared/ui/PlainTextLinks.tsx` | T15d пакет B / A12 | HTTP(S) only, text nodes, safe new tab; teacher lesson/review/history | Renderer unit + T15d B browser |
| Auth/drafts | `features/auth/session.ts`, `ReauthOverlay.tsx`, `app/DraftProvider.tsx`; `shared/ui/DirtyFormGuard.tsx`, `ConflictCompare.tsx` | DESIGN / A12 | Single-flight, Web Locks, clean logout, reauth same user, conflict compare | T14e session/E2E; T14f memory files/dirty/reauth; учебные формы по T15 |
| CRUD semantics | `features/*/api.ts` + route links | DESIGN / A12 | Outcomes A09/A12; unit/component + meaningful real-API E2E | T15/T16 unit/component + meaningful real-API E2E |

Для вложенных страниц shell подсвечивает родительский раздел: lesson обеих ролей →
«Расписание», teacher course/архив → «Ученики»; detail ученика/работы сохраняет
свой раздел. Текущий пункт получает `aria-current=page`, вложенная страница —
`aria-current=location`; «Ещё» показывает активность скрытого раздела. «Выйти» —
в отдельной нижней области как вторичное действие с прежним подтверждением
несохранённой работы. Неизвестные student/teacher URL показывают страницу404 и
ссылку в свой кабинет. На ширине до1023px shell переключается на нижнюю навигацию,
чтобы верхнее меню не сжималось. Между самостоятельными блоками занятия сохраняется
видимый отступ. Эти уточнения не закрывают ручную приёмку T15b.

Только ru-RU/Europe-Moscow; Japan packs не применимы. Цель WCAG2.2AA: текст4.5:1,
крупный3:1, видимый focus/skip-link, semantic headings, aria labels/status, dialogs
с возвратом фокуса. Touch targets44px для основных действий, не один hover/drag.
200% zoom и экран360px не теряют действия; full filename/title можно раскрыть.
Reduced motion без потери информации. Удобство проверяется по PRODUCT §8,
а не наличию украшений или количеством кликов без контекста.


### Граница расширения F02: банк и экзаменационные материалы

После MVP источник задания (банк/его версия) отделяется от факта персональной
выдачи Homework и ответа ученика. Редактирование банка не должно менять уже
выданное условие/материалы; конкретную модель снимка/версии спроектировать перед F02.
Экзаменационный каталог и подборки конспектов/задач для повторения — отдельная
организация контента; не подменять номером задания lesson_id и не создавать
фиктивные занятия ради хранения файлов. Общий защищённый file pipeline и проверки
доступа переиспользовать; доступ к подборке не означает доступ ко всему банку или
авторскому решению. Классификатор ОГЭ/ЕГЭ и правила доступа уточнить по PRODUCT/F02
до схемы/API. В T14–T18 не добавлять пустые таблицы/роуты/пункты меню для этого этапа.

### T15b.2 — календарь и teacher planning

`teacher_planning` хранит effective-dated норму пары teacher/student и недельные
исключения (пауза/не задано), с revision пары для конфликта вкладок. Обычная норма
со следующей недели, текущая — exception; прошлые записи неизменяемы. Счётчик
недели МСК включает уникальные scheduled/completed всех своих активных курсов,
без cancelled/архива и без влияния выбранного фильтра календаря. Денег здесь нет.
`/teacher-planning/students` возвращает scoped snapshot total/page; `deficit_only`
применяется до paging. Не заданная норма/пауза не дают недобор.

Общий SQL `reminder_rows` задаёт recipient-scoped признаки; `attention_counts`
используется списком учеников до count/sort/paging, историей и напоминаниями.
Проверяется именно enrollment данного получателя. Независимые persisted отметки
«не нужно» находятся в LessonStudent; удаление материала возвращает свой сигнал,
если отметки нет. Серверное время проверяется при чтении; raw status не пишется.
С21.10 public status вычисляется через Lesson.effective_status (см. ниже).
Список внутренних напоминаний не создаёт Notification и не рассылает сообщения.
Пакетное чтение material flags списка занятий заменяет прежний N+1.

`TeacherSchedulePage` — week/hour grid desktop и выбранный день narrow;
`LessonEditor` — shared DateTime/Select/Dialog, явная запись и сравнение переноса.
Поиск/страницы компактного booking dialog локальны, чтобы URL не терял draft;
календарная неделя/день/view и списки вне dialog остаются в URL. `RegularDialog`
восстанавливает receipt/preview через GET операции перед повтором confirmation.
`TeacherLessonPage` — один маршрут для календаря/ученика/напоминания; recipient
явен, origin списка сохраняется в state, direct URL имеет безопасный fallback.
История ограничена server pages, название занятия отдельно от раскрытия файлов.

A13 upload variant: `shared/ui/MaterialUploadQueue.tsx` использует общие
`upload`, validation/FileDescriptor/ReadFiles; это отдельные lecture POST, не
модель versioned файлов ответа ученика. Per-file progress/unknown/read/explicit
retry и общий dirty guard; подтверждённый POST не превращается в failure при
последующей ошибке GET. `DirtyFormGuard` регистрирует только dirty marker в
DraftContext для общего подтверждения logout; приватные поля не сериализуются.
Материалы/нормы/календарь инвалидируются после server ack. Напоминания и обзор
сегодня обновляются раз в60s только при visible+online, а также после focus/write.
Стартовый teacher route остаётся «Ученики»; очередь/.3 и деньги/.4 не подключены.


### T15b.3 — локальные владельцы, runtime gate пройден20.10.2026
Existing submission queue DTO дополнен student first/last/username и course name
из того же scoped SQL snapshot; descriptors batch на страницу. Нового queue API,
моделей/миграций или grade lifecycle нет. `features/review/reviewDraft.ts` хранит
opened answer отдельно от teacher grade/comment и latest; safe read перед повтором
unknown, explicit open latest после409, только checked ack/read снимает dirty.
`ReadFiles condition` использует `condition-file`, решение — `file`: это разные
пространства domain file ID; DirtyFormGuard допускает только эти preview query keys.
MyDay переиспользует today/reminders/queue; после .3 gate home — `/teacher`.
Runtime evidence — T15b; ручная приёмка открыта. Текущий остаток — STATUS.


### Уточнение21.10.2026 — завершение, файлы проверки и UI
- `Lesson.effective_status`: SQL column_property, CASE scheduled + end<=statement_timestamp
  → completed, иначе raw status. `LessonResponseDTO` читает его; status filter использует
  то же выражение до paging/count. Нет фонового scheduler/GET write/изменения updated_at.
  Cancelled и ручной completed сохраняются. Время aware, отображение Europe/Moscow.
- `HomeworkSubmissionFile.purpose`: answer/review, defaultanswer/check constraint,
  additive Alembic11ffc0656a8a. Старые файлы остаются answer. Public DTO разделяет
  files/review_files; внутренние пути/purpose не выдаются клиенту.
- Existing JSON PATCH /submissions/{id}/teacher сохранён. Multipart PATCH
  /submissions/{id}/review принимает strict integer grade0–5/expected_version,
  optional teacher_comment/files. Один existing service transaction/lock order:
  permissions+exact version → files через HandlerDocuments/FileAssetsService →
  checked/notification/freeze/commit. Failures компенсируют новые UUID files;
  unknown ack требует read, checked immutable. Upload quota принадлежит получателю,
  uploader — teacher. Download URL и scope общие, чужой teacher/shared student не
  получает файлы другого teacher. Local selected teacher File objects живут в ReviewDraft.
- Материалы recipient: lock LessonStudent → count Lecture → не более4;
  LectureLimitReached409/code=lecture_limit, локализованная frontend ошибка.
  Старые записи не удаляются. UI автоматически загружает selected batch последовательно;
  confirmed item исчезает из временной очереди после refresh и остаётся в saved list.
- `WeekNavigation` — общий owner обеих ролей. `FeedbackProvider` —4500ms, pause hover/focus,
  close action. Pagination/Pages скрыты для одной страницы без потери длинных списков.
  `ReadFiles` различает file/condition-file/review-file; `ReviewResult` общий для результата
  на задании, занятии и teacher review. Подтверждение удаления — danger variant общего Dialog.
- Student lesson показывает три явных блока; submitted виден в student MyDay.
  Teacher MyDay reuse existing scoped today/queue/reminders, queue variant DataList
  складывает строки без вложенной рамки и не переполняет колонку. Полный status/проверки — T15b.

### T15c.1 · admin users · 21.10.2026
Admin users/read selector берёт AdminUser DTO через `/admin/users`, links —
`/teacher_students` с pagination. Profile PATCH без role, account-status отдельно;
приглашение/reset различаются purpose и fragment route. Shared InvitationDialog
принимает purpose/audience, null/void не сохраняет прежнюю ссылку. Admin private
search owner `features/admin/users/Search.tsx`, URL только несекретные filters/page.
DirtyFormGuard одна на странице (profile+quota); canonical Select portal имеет
именованный region вокруг listbox. Визуальные tokens/права/backend не расширены.


### T15c.2 · admin courses/lifecycle/audit · 21.10.2026
`features/admin/courses` владеет read-only course/lesson/recipient просмотром;
`Actions.tsx` использует shared ConfirmDialog, сохраняет unknown outcome выше
диалога и требует read перед повтором, даже после cancel/reopen. ConfirmDialog
смонтирован закрытым до первого открытия для canonical Mantine return-focus.
Purge typed name/course_id; committed delete и cleanup status разделены, GET404
после неизвестного purge не вызывает повторное удаление. Cleanup API общий.
Search owner прежний `admin/users/Search`, ID filters/view/page в URL; текст имён
в памяти. UserFilter использует admin DTO, включая inactive,20 результатов с
уточнением поиска. Audit owner `admin/audit`, source:id key, actor/action/page,
точное время МСК. Admin lesson подсвечивает «Курсы». Backend/schema не расширены;
read/upload/dialog/session/token owners и границы D02 прежние.


### Admin storage · 22.10.2026
Student usage/limit owner остаётся `/users/{user_id}/storage`, глобальный budget
ученика, включая все teachers/архив. Новый admin-only GET
`/admin/users/{user_id}/course-storage` — read-only teacher report, scope по
Course.teacher, distinct linked assets, all learning file kinds/архив. Report
не предоставляет teacher quota/limit; inactive target доступен admin, чужие
роли не получают отчёт. `admin/users/Storage.tsx` выбирается по роли: Storage для student /
TeacherStorage; admin не показывает блок. Unit adapter `api.ts`
переводит десятичные МБ/ГБ в точные backend bytes; прежние лимиты не пересчитываются.

### Teacher student history ·23.10.2026
`StudentWorkspace` использует `courses/StudentHistory`: independent GET latest
completed/nearest scheduled/month past/future; personal course и recipient scope
сохраняются. Месяц в МСК, inclusive UTC to_date до последней PostgreSQL µs;
текущий месяц ограничен стабильной границей past, future-month не посылает
перевёрнутый диапазон. Серверные total/offset/20–50, не группировка одной страницы.
`history-month`, `history-lesson`, `history-offset/limit` в URL; `next-*`
независимы. Старые курсы/архив открываются прежним отдельным маршрутом.
Canonical ReadFiles получил optional `owner`/`file-owner` для повторного показа
одного file ID в latest и раскрытой истории: только выбранный owner монтирует
fullscreen. Остальные callers без owner прежние; единый PDF pipeline/active key,
history/state/focus/blob cleanup и E2 сохраняются. DirtyFormGuard при разрешённом
preview допускает file-owner только вместе с остальными preview query changes.
LinkButton принимает router state для возврата. NormEditor имеет embedded variant
без собственного details, payload/версия/unknown/guard прежние. CourseDetail
showHistory=false используется в общих настройках workspace; direct course прежний.
Backend endpoints/permissions/files/storage не изменяются.

23.10 · StudentHistory: history-month хранит выбор API диапазона, history-strip —
первый видимый месяц ленты; стрелки меняют только strip. Выбор сбрасывает
прежние history pagination/expanded-file параметры, сохраняет state/будущее.

### S1 · прямые controls и touch pinch ·23.10.2026
Последнее уточнение владельца заменяет S1 zoom popover: toolbar содержит прямые
minus/plus/download и fullscreen close, без имени/процентов/дополнительного меню.
FileViewState/transport/worker прежние. `FilePreviewBody` слушает touch events только
в документном viewport: две точки → transient transform общего content без
повторного raster на каждом move → commit zoom на end. Сохраняется anchor страницы/
изображения под центром жеста; touchcancel отменяет transform, один палец остаётся
native scrolling. Локальный touch-action pan-x pan-y исключает двойное browser+
viewer масштабирование внутри документа; browser zoom вне viewport и Ctrl/Cmd
shortcuts не перехватываются. Listener/transform cleanup на unmount.
Scroll handler PDF читает актуальную geometry через useEffectEvent, чтобы события
после быстрых +/- не сохраняли anchor со старым масштабом. Границы50–300% и4M
canvas budget прежние; скрытый aria status сообщает масштаб без нового видимого UI.


### S2 · student lesson history ·23.10.2026, browser VERIFY
Owner `features/courses/StudentLessonsPage.tsx`, date helpers — существующий
`studentHistoryDates.ts`; teacher `StudentHistory` не импортируется. `/lessons`
student scope, `view=all`, limit20/50 + offset; latest status=completed, desc/limit1
без эвристик по PDF или дате. В прошлом месяце desc, будущем asc; текущий разделён
на disjoint past-desc/future-asc с независимыми страницами. Все диапазоны inclusive
UTC из Europe/Moscow; past заканчивается .999999 до начала future.
Курсы запрашиваются страницами20 (`useInfiniteQuery`), остальные страницы по
«Ещё курсы»; выбранный курс из URL отдельно авторизуется detail GET. Метаданные
преподавателя недогруженного курса — scoped detail, ошибки не подменяют пустой
историей. `has_*` backend сверены: student recipient/material access scope;
UI не делает запросов attachments каждой collapsed строки. Только last/expanded
GET `/lectures` с paging и `/homeworks` с student_user_id текущей session.
URL: course_id/history-month/history-strip/history-offset/history-limit/
history-lesson, upcoming-offset/limit и при необходимости owner-files-offset/limit.
Курс/месяц сбрасывают страницы/раскрытие, paging сбрасывает раскрытие. Preview
использует прежний ReadFiles с owner и S1 query/Back/focus, без изменения viewer.
Lesson/Homework получают проверяемый local studentHistoryReturnTo и scroll
в router state; явный возврат ждёт основных queries, Back использует canonical
ScrollRestoration. Учебные данные, file bytes и credentials в state не копируются.
Student detail подсвечивает историю только при её origin, teacher/admin ownership
прежний. Это реализация, не доказательство browser runtime: matrix в T15d S2.

### S3 · student presentation ·26.10.2026
`shared/lib/studentAnswerState.ts` классифицирует только отображение подтверждённого
ответа; API transitions/versions/UploadQueue остаются прежними. `StatusBadge.tsx`
экспортирует named `StudentAnswerBadge` без изменения teacher semantics.
`HomeworkThread` хранит условие/status/CTA каждой placement и локальный ref результата;
кнопка фокусирует/скроллит соответствующий read-only review. Ошибка GET нейтральна,
не становится empty. При stale failed GET HomeworkPage сохраняет форму, блокирует
изменения через presentation loadError; сохранённые/локальные данные не теряются.

### S4 · student overview context ·26.10.2026
`features/courses/CourseContext.tsx` — единый renderer курса/teacher для student
дня и расписания. Scoped `/courses/{lesson.course_id}` через существующий
`useRead/readKey`: query cache/dedup не зависят от первой страницы каталога.
Fallback — lesson.course_name/«Название недоступно»; loading/error/retry метаданных
не блокируют урок. Subject отсутствует и не выводится по догадкам.
`CallLink audience="student"` — named вариант текста/Video на дне; teacher default
и безопасный HTTP(S) guard прежние. `ExternalLinkButton` остаётся владельцем
external target/rel, принимает только дополнительный leftSection.
Ссылка результата дня ведёт в точный homework `#result`; AnswerForm добавляет
только presentation region/focus/scroll после checked GET. Отправка/versions/
UploadQueue/история/S1 viewer и S2 returnTo не меняются.

### Student study documents ·26.10.2026
`HomeworkPage` размещает прежний WorkingAnswer/AnswerForm рядом с документами
через CSS grid, без remount при смене breakpoint/preview/collapse. PlainTextLinks
переиспользован для student condition здесь и в HomeworkThread; HTTP(S) only,
text-node escaping/new-tab policy прежние. Отправка/UploadQueue/версии не менялись.
Named student-вариант `ReadFiles studyLabel` владеет раскрытием, выбором документа,
памятью FileViewState, fullscreen query/Back и закрытием. Desktop начально expanded,
narrow collapsed, пользовательский выбор при resize сохраняется. Collapse снимает
только тяжёлую FilePreviewBody; memory view state/форма остаются. До4 конспектов
выбираются в одном material viewer; condition namespace отдельный. При раскрытых
конспекте и ДЗ допустимы две независимые bounded body (по одному документу в каждой,
viewport≤65dvh и прежняя виртуализация); любой fullscreen приостанавливает обе.
Teacher `embedded` default сохраняет один viewer на desktop и fullscreen на narrow.
FilePreviewBody получил только optional viewportLabel: доступные имена двух inline
регионов различаются, default teacher/fullscreen прежний. PDF transport/render/
pinch/лимиты/cleanup из S1 не переписывались. Новый state backend не требуется.


Student day entry refinement26.10: `CourseContext variant="teacher-inline"`
повторно использует тот же scoped course query/cache/error/retry, скрывает только
курс/ссылку. Full default на nearest/schedule прежний. Новый блок — навигация
в `/student/materials`, не lesson detail; date completed только краткая справка.


Уточнение26.10 student lecture: `ReadFiles initiallyCollapsed` — presentation
option по умолчанию false, передаётся только конспекту в HomeworkPage.
Пользовательское раскрытие остаётся в локальном состоянии до ухода со страницы,
metadata retry не открывает viewer автоматически. LessonMaterials keyed по
homework.id сбрасывает раскрытие при переходе к другому ДЗ даже в том же уроке.
Default condition/teacher и protected transport/UploadQueue не меняются.

### Student blue shell/navigation ·26.10.2026
Согласованный вариант1: `app/theme.ts` новые studentCanvas/Header/Hover → прежний
cssVariables/Mantine mapping. AppShell role-scoped studentShell wrapper задаёт
фон/шапку без global body/theme reset; teacher/admin цвета и route ownership прежние.
Student labels короче, Lucide иконки декоративные aria-hidden, видимый текст/URL/
aria-current/исторические returnTo сохранены. Dropdown остаётся canonical Mantine
Menu с Escape/focus, mobile четыре равные minmax колонки без overflow.
`LinkButton navigation` — opt-in canonical variant: ArrowRight и общий CSS owner
`navigationButton.module.css` для геометрии/hover. `ExternalLinkButton studentAction`
даёт ту же геометрию student CallLink без стрелки, Video/HTTP(S)/target/rel прежние.
Default обоих shared adapters не меняет teacher/admin. Убраны конфликтующие
studentDay label padding/height overrides, заменены одним owner; не screen-local
сдвиги отдельных надписей. Реальные transitions/dirty/version/UploadQueue не менялись.


A13 · student mobile shell27.10: AppShell остаётся canonical owner; до1023px
основные bottom links day/materials/schedule, homework «Д/з» перенесён в «Ещё».
Origin-aware active/current, href/state/ScrollRestoration и guards не изменены.
Mobile student profile скрыт только из header, доступен через Menu. Bell виден
на всех student routes. NotificationCount named variant=badge использует прежний
useNotices/unread cache/polling/actor scope; default=text для teacher прежний.
Badge не вызывает mark-read; 0 скрыт,99+ визуально при полном aria count, query
error без data не подменяется нулём. Student Menu withinPortal=false сохраняет
landmark; withInitialFocusPlaceholder=false убирает невалидный focusable
presentation child роли menu; штатные focus trap/keyboard/Escape сохранены.
Геометрия/цвета — DESIGN; Menu/NotificationCount/UI CSS не дублируются в страницах.


A13 · student latest27.10: StudentLessonsPage/LessonFiles получает compact variant
только для latest; history rows и teacher StudentHistory не мигрируются. HistoryLink
сохраняет origin URL/scroll и modified-click, named secondary/homework меняют
только представление через canonical LinkButton. Optional title в LinkButton —
обычный anchor attribute. ReadFiles singleFileLabel действует только на одиночный
файл; owner/URL preview/close/Back/focus и S1 FilePreview/transport прежние.
Multiple раскрытия сохраняют все файлы и server paging; loading/error не означают
«нет». Latest LessonFiles keyed by lesson.id сбрасывает выбор раскрытия при смене
урока. Course lookup/detail/cache прежние; teacher-only context не считает
первую страницу справочником, при недоступности сообщает и даёт retry.
Latest/query sorting/time/status не менялись; короткие месяц/год names включены
в aria-label наряду с полными, без изменения month/strip/URL поведения.


A13 · уточнение latest27.10 по owner: HistoryLink secondary теперь обычная
подписанная кнопка с lesson-фоном под материалами; mobile full width. Icon-only
переход в header убран. Canonical LinkButton/URL/modified-click/origin/scroll
не менялись. Визуальное предпочтение принято owner и закреплено в DESIGN.


A13 · monthly student history27.10: StudentLessonsPage остаётся owner, новый
studentMonthlyHistory scope в read.module.css не мигрирует teacher/accepted latest.
SelectField/ReadState/Pagination/HistoryLink/ReadFiles прежние; year label «Год»,
button «Текущий месяц», URL/month/strip/offset/expanded/origin и queries не менялись.
Счётчики принадлежат data.total каждого успешно прочитанного временного окна;
range показывается только для непустой partial page. Whole-row button сохраняет
aria-expanded/controls и получает видимую «Материалы»; desktop/mobile меняют
раскладку presentational spans, не семантику или права. Области файлов выбранной
строки названы «Конспекты выбранного занятия»/«Домашние задания выбранного занятия»
для отличия от областей latest и уникальности landmarks. Latest JSX и прежний
CSS prefix сравнены с backup: совпадают точно. Protected viewer/transport неизменны.

<a id="a14"></a>
## A14. Проект F01: бронь и VK без обязательного VK ID ·01.11.2026

**Будущий технический контракт, код/миграции отсутствуют.** Требования —
[PRODUCT/F01](PRODUCT.md#будущий-f01--существующий-vk-бот--принято301001112026),
решения/остаток — [D13](DECISIONS.md#d13), исполнение — [F01](tasks/F01.md).
Имена новых таблиц/HTTP ниже проектные; локальный контракт F01.0 зафиксирован
в A14.7. Это спецификация будущей реализации, не действующий OpenAPI.
A02/A03/A05/A07/A12/A13 сохраняются; внедрять небольшими этапами без второго backend.

### A14.1. Почему бронь отделена от аккаунта

В текущем User обязательны username/hashed_password; `is_activated=False` запрещает
login, но create_user сразу выпускает invite и коммитит. Lesson требует Course,
StudentCourse и LessonStudent. Автоматический вызов `/auth/register` из бота дал бы
дубликаты уже существующих User, обход D01 и преждевременные grants.
По принятому ответу01.11 до связывания хранится **подтверждённая Booking**, которая
сразу занимает время и видна teacher. После связывания она материализуется в
обычные Lesson/LessonStudent, сохраняя booking_id и прежний receipt. Установленный
User/teacher link → материализация сразу при брони. Это не очередь одобрения брони.

| Проектная сущность | Поля/ограничения и смысл |
|---|---|
| IntegrationConnection | installation/group, allowlisted teacher IDs, enabled/scopes, credential digest/version; выбранный teacher из payload не расширяет scope |
| ExternalContact | connection + community subject, verified_sender_at, permission unknown/allowed/denied/unreachable, permission_version/checked_at; unique(connection, subject). Контакт не User/роль |
| BookingRecipient | opaque ID, child contact reference, минимальные заявленные имя/фамилия/grade, nullable linked_student_user_id, revision. Unique активный canonical child contact в installation; имя не ключ. Непроверенный raw ID лишь candidate |
| ExternalIdentityLink | contact→User, purpose student/teacher, verified method/actor/time, revision/revoked_at; одна активная identity на contact/purpose, конфликт не переносит связь. OAuth VK ID позже в другом namespace |
| ParentGrant | parent contact + recipient + teacher, pending/confirmed/rejected/revoked, approved_by/at, proof reference/revision; unique активной тройки. Не роль User, не доказательство юридического представительства |
| BookingWindow | teacher, конкретные start/end UTC, week Monday МСК, revision, published/closed/consumed, explicit withdrawal marker, created_by; positive duration, внутри выбранной недели, нет повторения. Published окна не накладываются друг на друга у одного teacher |
| Booking | window/teacher/recipient, actor contact и parent grant revision, confirmed/cancelled, version, start/end и price snapshot, nullable UNIQUE lesson_id; unique активная booking на window. Источник истины о результате записи |
| BotInteraction / OperationReceipt | opaque handle, actor/group/teacher/recipient/window revision, expires_at, operation UUID, normalized payload hash, pending/committed/rejected/result; unique(connection, operation UUID). Другая нагрузка с тем же UUID→409 |
| CancelRequest | booking/lesson + expected schedule version, requester, причина с ограниченным сроком хранения, pending/approved/rejected/withdrawn/stale; максимум одна pending на объект/версию, решение и receipt immutable |
| IntegrationInbox | connection + upstream event key UNIQUE, minimal normalized command/hash, received/processed/result, lease/retry. Не полная переписка/вложения |
| Delivery | domain event key + contact/channel UNIQUE, target reference/version, due/expires, status, attempt/lease, random_id, last_error category, permission/link revision; без файлов/оценок/токенов |

Новые FK/unique/check/index через additive Alembic, registry моделей/router/Depends
по правилам проекта. Не делать автоматический backfill из JSON/имён/живых Sheets.
Downgrade с бронями/identity/deliveries отказывается терять данные; operational
rollback — выключить интеграцию при сохранении строк, не разрушать схему.
TTL очистки ПД/receipts/inbox определяется P01; технический срок действия кнопки
не равен сроку хранения доказательства. Не удалять dedupe раньше возможного replay.

### A14.2. Identity, приглашение и родитель

1. Авторитет отправителя — событие, полученное доверенным адаптером VK; на обычном
   пользовательском HTTP нельзя прислать `vk_id` и стать этим человеком. Long Poll
   connector является доверенной границей: его компрометация позволяет подделать
   события внутри разрешённого scope, поэтому нет admin credentials/direct SQL.
2. Новый ребёнок через свой диалог создаёт contact/recipient; родитель подаёт
   candidate child и ждёт разового teacher confirmation **связи**. До него нельзя
   читать расписание ребёнка/записывать от его имени. Teacher подтверждает после
   внешней проверки, видит минимум данных, отказ/отзыв блокирует следующие действия.
   Нельзя выдать учебную сессию или подтвердить contact ребёнка одним parent grant.
3. При одновременном обращении ребёнка и родителя canonical recipient разрешается
   по scoped contact key под lock; повтор не создаёт второй recipient/booking.
   Непроверенные сведения не перезаписывают подтверждённый профиль. Ошибочная
   ссылка/тёзка — conflict и ручной разбор, не merge accounts. Дети без собственного
   VK и несколько детей/родителей не расширяются молча: исходный bot имеет один
   child_id/parent_id; схема grants допускает дальнейшее расширение отдельным UX.
4. Существующий активированный ученик связывает VK из своей обычной сессии LGG:
   reauth → одноразовый secret challenge (предложение TTL10min, hash в DB,
   rate-limit/попытки) → ввод в личном диалоге → подтверждение той же сессией.
   Challenge связан с User/group/purpose и ожидаемой revision, не позволяет менять
   target user. Raw URL/forward родителя/имя/класс не заменяют этот протокол.
5. Новый/неактивированный ученик: teacher обрабатывает бронь, проверяет, нет ли
   известного аккаунта, создаёт inactive User только при явном «новый ученик» либо
   выбирает **своего** уже связанного; выдаёт D01 invite отдельно. Создание User,
   link/курс/enrollment, перенос подтверждённых booking в Lesson и stage_issue
   в одной транзакции. Генерируемый неперсональный username можно предложить,
   не подставлять VK ID/email. Пароль случайный недоступный до активации.
   При активации D01 меняет пароль/activated и не создаёт никаких новых занятий.
   Без активации учебные grants есть у неактивного получателя, login закрыт A03.
6. Если известный User не связан с выбранным teacher, только admin подключает
   его по D01; до этого Booking видна этому teacher как его бронь, чужая история
   недоступна, время занято. Нельзя повторно создать User ради обхода ограничения.
   Неизвестность до доказательства identity сохраняется как unresolved recipient.
   Admin resolution не выдаёт ему права менять teacher-only цену.
7. Один User может иметь несколько teacher. Подтверждённая child identity не даёт
   parent расписание всех teacher: grant teacher-scoped, отзыв у одного не трогает
   остальные. Teacher identity также привязывается из его сессии, не выбором роли.
   Смена VK/ошибочная link: freeze доставки/команд, admin evidence, explicit rebind,
   audit; не менять UserRole/пароль другого человека. Disable User останавливает
   привязанные действия; неизвестный contact не обходит блокировку нового User.
8. Отвязка LGG, запрет VK сообщений, отзыв parent grant — независимы. Отвязка
   блокирует queued deliveries и неактуальные handles, не удаляет занятие/историю.
   Parent не получает invite/reset ребёнка автоматически. До активации короткая
   ссылка ведёт к объяснению приглашения; валидированный local returnTo, без токенов
   в query и без обхода D01. VK ID login отдельно, собственная сессия LGG после
   проверки active/activated/auth_version; VK ID subject ≠ автоматически community ID.

### A14.3. Окна, атомарная бронь и гонки

Окно — одна встреча55min по умолчанию с полной датой; публикация только явная,
без повторения следующей недели. Рекомендуемый первый UI — выбранная неделя,
перечень дат/времени, publish/close с revision. Витрина выдаёт только будущие
published окна минус пересечения с **Lesson и нематериализованными Booking**.
Точная неделя приходит от backend, не вычисляется из старой кнопки «Пн».
Нет длительного удержания слота во время чтения/ввода данных; это не успешная бронь.

Сверка фактических locks01.11 (source evidence, не DB execution):

| Current path | Порядок / ограничение нового stage |
|---|---|
| create/update/regular lesson | schedule advisory → writable_course/lesson locks → active_students (enrollment/pair/User FOR UPDATE) → homework recalc; regular operation lock после schedule в отдельном namespace |
| lifecycle restore | schedule_for_course → course → lesson → recalc; остальные revoke/enrollment paths course-first и не должны брать schedule позднее |
| teacher_students link/end | courses ID ASC → previous pair → memberships ID ASC; admin-only. Поэтому stage не должен держать pair перед ожиданием existing course |
| price write | schedule → pair, не ждёт course; брать snapshot внутри schedule, до commit менять его нельзя |
| invite/refresh/password | User → invitation/refresh; не ждут schedule/recipient. Новый resolve начинает со schedule/recipient, User ниже; существующий consume не материализует booking |
| personal_workspace(create) | pair row lock → create course/enrollment → commit; новые stage гарантируют единственность workspace для пары и не ждут существующего course после pair |

В F01.2 stage workspace и его обычный create consumer должны использовать один
per-pair creation mutex **до** pair/course создания, не только новый bot path:
иначе два потока создадут workspace параллельно. Existing permission/lifecycle
проверки сохраняются. Для нового course нет ожидания старых row locks; при уже
существующем course сначала lock course/recheck, затем pair. Новые FK/cascade и
явные SELECT FOR UPDATE не должны вводить обратное ожидание User→schedule.
Для materialize batch сначала собрать teacher IDs без блокировок → все schedule
locks ID ASC → recipient revision lock → проверить неизменность набора teacher;
если набор изменился, rollback/retry с новым списком, **не** брать дополнительный
schedule lock после recipient. Аналогично все course IDs lock ASC до пары/урока.
Это локальная спецификация устранения циклов; реализованные JOIN FOR UPDATE
не объявляются уже доказанно эквивалентными новым stage. Уточнённый порядок, включая implicit FK и purge, — A14.7. В .2/.3 нужны
реальные concurrent sessions/deadlock injection; no broad unrelated refactor.

Confirm транзакция:

1. Проверить connection/command/actor и handle, payload hash/TTL. Сериализовать
   одинаковую операцию; уже committed receipt вернуть без новой записи. Иная
   нагрузка под старым UUID —409; чужой receipt —404 без данных.
2. Единый порядок locks для новых действий: integration operation → teacher
   advisory schedule lock → window/recipient identity locks в стабильном порядке →
   existing course locks → lesson rows → teacher pair/enrollment/User → homework
   rows (ID ASC). Отдельные identity/account операции не захватывают schedule
   после user lock; stage materialization не вызывает public committing services.
   Точный graph и правила ниже; DB concurrency ещё NOT RUN.
3. Под lock повторить group/scope/parent grant/linked account state, даты окна,
   revision/состояние, отсутствие confirmed booking и пересечений. Пересечения
   считаются как полуоткрытые интервалы [start,end), по действующим A05 фильтрам
   cancelled/archive. Для **бота** конфликт блокирует запись; предупреждение
   teacher по D03 остаётся, не вводить глобальный SQL exclusion для всех Lesson.
4. Сохранить Booking, потребить окно. Если identity и активные права есть — stage
   ordinary Lesson+LessonStudent; иначе только Booking. Workspace только свой,
   архив не оживлять, ambiguous legacy courses не выбирать произвольно. Снимок
   цены на момент брони: если действующая пара известна — D12 текущая ставка,
   иначе NULL, не0. Поздняя материализация переносит этот снимок без переоценки.
5. При создании Lesson пересчитать D04 непроверенные placements, checked неизменны;
   stage audit + teacher booking event/outbox + immutable result receipt. Commit
   один; до него ни VK/Google HTTP, ни выдачи success. Failure откатывает и окно,
   и User/grants/занятия/дедлайны/события; внешняя недоставка commit не откатывает.

Учитель создаёт/переносит/восстанавливает встречу или подтверждает серию через тот
же schedule lock. Если его запись произошла первой, окно исключается при confirm.
Если бронь первая, subsequent teacher preview/confirmation обязан **видеть её**
в conflicts, даже без lesson_id. По D03 учитель может явно оставить пересечение;
это его осознанное действие, не победа второй автоматической брони. Закрытие окна
не отменяет принятую Booking. **По ответу владельца01.11** подтверждённая отмена
переоткрывает исходное окно, если оно впереди, не отозвано teacher и не перекрыто
другой встречей/бронью/новым published окном. Под тем же lock повысить revision;
старые handles недействительны, новая бронь имеет новый booking_id/operation.
Иначе окно остаётся закрытым с причиной. Отмена не публикует перенесённую дату
или следующую неделю. Сам перенос не открывает новое окно автоматически; teacher
может явно опубликовать освободившееся время новым dated окном. Старое consumed
окно сохраняется для истории, не блокирует такую публикацию само по себе.
Восстановление/Undo проверяет conflicts и version; политика не превращает старую
Booking в новую. Серия не поглощает одиночную бронь и не меняет её receipt.

Materialize нескольких booking одного recipient: **сначала** schedule locks
затронутых teacher ID ASC, затем identity/recipient, далее A14.7; unique lesson_id/
booking relation и результат операции. После нового User/своих связей создать
course/enrollment/обычные получатели; не трогать чужие memberships/materials.
Резерв больше не учитывается отдельным конфликтом после успешной материализации,
календарь заменяет строку по booking_id без двойного отображения. Сбой — все старые
брони остаются подтверждёнными; пользователь не записывается повторно.

D04 видит именно Lesson после материализации; неизвестный User/course не позволяет
заранее менять дедлайны чужого ДЗ. Для поздно связанной уже прошедшей брони нужен
явный teacher review, не скрытое изменение старых checked/snapshots. D12 SQL
считает обычные Lesson; неподключённые Booking показываются отдельно, не как
проведённые/доход. Никаких автоматических оплат50% или бесплатного первого урока
по рекламному тексту. Повтор старого receipt после отмены возвращает результат
создания плюс current status отдельным чтением, не воскресает занятие.

### A14.4. HTTP, inbox, callback и отмена

Проектный API (точные формы/ошибки — A14.7; сейчас endpoints отсутствуют):

| Группа | Команда / авторизация / ответ |
|---|---|
| `/integrations/vk/inbox` POST | Connector credential, timestamp/nonce + MAC над методом/path/body, exact connection/group; durable inbox ack, max body/rate-limit. Secret не в URL. Повтор event→тот же результат; admission rate-limit connection+actor+teacher, аудит злоупотреблений без текста/секретов |
| `/integrations/vk/windows` GET | Scoped connector + validated interaction actor; недели/teacher только allowlist, без имён других учеников |
| `/integrations/vk/bookings/confirm` POST | operation UUID, opaque handle, revision; target/window/teacher берутся с backend handle, не доверять raw ID payload |
| `/integrations/vk/operations/{id}` GET | Только operation owner/connection; pending/committed/rejected, booking/lesson ref, domain status и delivery status отдельно |
| `/integrations/vk/schedule`, `/cancel-requests` | Ограниченный календарь actor/confirmed parent grant; POST заявка/withdraw; решение только связанный teacher, versioned receipt |
| `/teacher-planning/booking-windows` | Обычный teacher bearer/session policy, dated list/publish/close CAS; scope существующего Teacher |
| `/teacher-planning/bookings` | Список своих броней, own detail, resolve/invite/materialize и parent-grant confirm/revoke; разные полномочия teacher/admin |
| `/users/me/integrations/vk` | Обычная LGG session/reauth, challenge/status/unlink; не читать чужие identities |

Connector имеет только эти capabilities, не может пользоваться `/auth/register`,
files/download, review/reset/admin или произвольным user impersonation. Credential
revocation проверяется на каждом запросе; pending workers тоже сверяют scope.
Секреты только server env/secret storage, ротация с остановкой lease/старых MAC.
Private network/HTTPS плюс auth обязательны, IP allowlist — дополнительная мера.

Transport первым этапом **оставить Bot Long Poll**: не нужен новый публичный webhook
и второе управление событиями. Persist inbox до processing; checkpoint/reconnect
и upstream gap имеют отдельную диагностику. In-memory state не доказательство
получения/commit. Если upstream event_id отсутствует, fallback допустим только с положительным
conversation_message_id: connection/type/peer_id/conversation_message_id. Нулевой/
отсутствующий ID не образует общий dedupe key; правила отказа — A14.7. Hash текста
не идентификатор события; следующий реальный click не теряется как дубль текста.
Получение события at-least-once не обещает полной replay истории Long Poll.

Callback API — только отдельная будущая замена транспорта: HTTPS, confirmation,
проверка group+secret, inbox до ack, обработка асинхронно, dedupe event_id, rate
limit. `message_event` кнопка в Long Poll **не** Callback API webhook; ответ
`sendMessageEventAnswer` завершает индикатор, а не подтверждает доменный commit.
Сроки ACK/retry/replay VK не подтверждены схемой — F01.0, без выдуманного SLA.

Cancel flow сохраняется, payload меняется на opaque request/booking ID+revision.
До решения и при reject место занято. Approve под schedule lock/version атомарно
меняет Booking и Lesson (если есть), D04, request receipt, audit и deliveries.
Перенос/отмена teacher до решения делает заявку stale, старая кнопка не отменяет
другую дату. Членство в общем чате не даёт полномочий: actor linked teacher
объекта проверяется backend. Старые weekday-only callbacks после switch не пишут
в ячейку: «Кнопка устарела, откройте Мои записи». Повтор reject/approve возвращает
прежний исход; revoke/архив/чужой teacher — отказ. Причина не идёт всем teacher,
может содержать сведения о здоровье, хранение ограничивается P01.

### A14.5. События, delivery и время

Источники: `homeworks::create_homework` (assigned), `homework_submissions::submit/`
`review` (submitted/checked), `lessons::update/regular` (move/cancel), новый booking
service (teacher booked). Stage delivery рядом с domain event в той же транзакции;
Notification read_at не означает доставку VK, а VK sent не помечает кабинет read.
Нельзя перепроиграть всю историческую notifications таблицу на включении.

| Событие | Адресат / ключ / предложенная актуальность |
|---|---|
| homework_assigned, solution_checked | linked child, key existing domain event+contact; короткий текст без условия/оценки, кабинет; expires24h |
| solution_submitted | только teacher владельца, одна отправка, edit submitted не новое событие; expires24h |
| booking_confirmed | teacher в подтверждённый личный диалог, не весь team chat; receipt booking ID; expires24h |
| lesson_rescheduled/cancelled | child; key lesson+transition version, superseded jobs отменить; expires min(24h, применимый срок встречи), окончательное текущее состояние |
| cancel request/result | child + confirmed parent по прежнему сценарию, teacher owner для решения; не родителю учебные события; expires24h/до неактуальности запроса |
| reminder20min | child по confirmed identity/contact proof, даже если кабинет ещё не активирован, если есть право сообщения; booking/lesson current schedule revision; due=start−20min, expires=start |

TTL24h — предложение инженера для первого synthetic этапа, не согласованный SLA
и не срок хранения ПД. Для неподключённого кабинета только приглашение связаться
с teacher, никаких файлов/access tokens. Permission allow не активирует User.
Нельзя доставлять claimed child ID до проверки contact/прав адресата. Это не
блокирует бронь родителя, который получает инструкцию подключения ребёнка.

Доставка: pending→leased→sent / retry_wait / permission_blocked / skipped /
expired / dead / unknown. Worker claim с lease+SKIP LOCKED, before-send revalidate connection,
identity/grant revisions, account state, предметные права/current target/version.
Контакт до активации имеет только узкое право reminder/расписания, не homework.
Историческое чтение D02 само по себе не разрешает новые сообщения об обучении:
для новых учебных событий нужны действующие link/участие, не архив. Grant
родителя проверяется только у его команд/доставок: его отзыв не отключает
самостоятельную identity ребёнка. Старый allow не повышает permission без свежей
проверки VK; порядок доставки events не считать гарантированным.
Revoke во время уже начатого HTTP нельзя атомарно отменить во VK: гарантировать
остановку следующих попыток, минимизировать текст; не обещать несуществующий
распределённый atomic revoke. Unknown outcome хранить отдельно от sent.

random_id резервируется в DB до первого HTTP, сохраняется вместе с неизменным
rendered текстом/peer для всех попыток. Уникальность распределения хотя бы на
connection, ненулевой signed32 диапазон как проектное консервативное ограничение,
без hash collision; переиспользование не раньше подтверждённого окна VK dedupe.
Срок защиты random_id официально не подтверждён, поэтому **exactly-once доставки
не обещать**; после длительного unknown — ручной разбор, без нового random_id.
Crash after send/before ack покрывается той же delivery, не повторной бронью.

Ошибки:901→permission_blocked,900/902→unreachable; не утверждать юридический отзыв
согласия из902. Timeout/5xx/1/10→bounded backoff;6/9→общая пауза и снижение темпа;
5/7→остановка connection+оператору диагностика;100/неизвестная permanent→dead,
без бесконечной рассылки. Предложение backoff5s/30s/2min/10min/30min с jitter,
не более5 повторов и только до expires. Первоначальный локальный предел1req/s
на connection, interactive commands приоритетнее backlog; это выбранный budget,
**не установленная квота VK**. При отсутствии capacity reminder истекает честно.

Deny/stop сохраняет permission/version и отменяет pending; unsubscribe LGG также
не закрывает кабинет. Allow сначала заново проверяет право, планирует только
будущие напоминания по актуальному расписанию, не рассылает старые ДЗ пачкой.
Перенос обновляет due/version, отмена убирает reminder, restart читает DB, не
создаёт новый timer каждый раз. Для брони менее чем за20min рекомендуемый вариант —
один reminder сразу, если до начала ещё есть время, никакой отправки после start.
Связывание Booking→Lesson сохраняет один reminder key по booking_id; серии имеют
свой lesson ID. Никаких параллельных reminders из Sheets и платформы на один scope.

### A14.6. Владельцы UI и расширение

UI проектируется в принятой системе DESIGN, ru-RU/Europe/Moscow. В этой сессии
нет нового макета/токенов/изменений DESIGN. Полные состояния исполнения — F01.4.
Canonical owners: `features/schedule/TeacherSchedulePage.tsx` — даты/окна/брони;
`features/students/StudentWorkspace.tsx` — свой ученик/приглашение/parent relation;
`features/auth` — activation и account linking; `shared/ui/InvitationDialog.tsx`,
`ConfirmDialog`, `AsyncState`, `DateTimeField`, `SelectField`, FeedbackProvider,
ConflictCompare/DirtyFormGuard/reauth сохраняются. Не выдавать provisional recipient
за обычный Student DTO или ссылку на несуществующий Lesson. Confirmed booking с
«Кабинет не подключён» и действием выдачи доступа — разные статусы/действия.

Новые async states: unlinked/pending verification/linked/revoked; window empty/
loading/error/stale; booking committed/delivery failed; unknown→receipt recovery;
invite expired/account already activated; доступ закрыт/архив. Ошибка не закрывает
форму; grant/revoke — явный confirm со scope, stable busy/no duplicate submit,
keyboard/Escape/focus return, targets44,360/390/768/1280+200%, error/long content.
Ни одна кнопка не сообщает success раньше server ack; offline не создаёт очередь
броней в browser storage. Полезная ручная приёмка двух ролей обязательна.

Будущий F03 добавит tenant scope к connection/recipient/grants/windows/receipts/
workers/export и файлам/запросам, составные unique и миграцию LGG. Сейчас явно
ограничить одну installation LGG и allowlisted teachers; это **не SaaS isolation**.
Не выбирать организацию из произвольного payload. Подписка — entitlement, не
identity/teacher grant; её окончание не удаляет D02 историю. F04 copy-week, F07 demo,
VK ID auth, Google export F05.1, backend backup T18 — самостоятельные границы.


<a id="a147-f010-local"></a>

### A14.7. F01.0 — локальная спецификация перед первым кодом ·02.11.2026

Каноническое уточнение A14.1–.5; не новая бизнес-политика. Внешние доказательства
и live gates — [research](VK_RESEARCH_2026_10_30.md#f010--ревизии-и-внешние-gates).
Статус02.11: .1 offline harness, .2 synthetic identity/grants/invite и .3 local booking реализованы;
[границы .2/проверки](tasks/F01.md#результат-f012-02112026). Остальные описанные
transport/delivery endpoints/helpers/constraints остаются спецификацией.
Реализованный .3 subset и фактические проверки — [результат F01.3](tasks/F01.md#результат-f013-02112026).
Local teacher window publish/list требует explicit `connection_id`; own week lists
возвращают `{items,next_cursor}`, opaque UUID cursor, limit1–100/default25. Connector
windows/interaction/confirm/receipt HTTP зарегистрированы, admission fail-closed
до .5; delivery worker .6 отсутствует. Snapshot Booking сохранён при move,
обычный календарь использует актуальный Lesson; .4 объединяет строки по booking_id.
В .3 recipient resolve-invite подхватывает свой teacher batch; booking wrapper
добавляет CAS booking/recipient и explicit past review. После existing self-link
сохранённые брони подхватывает отдельная owning teacher materialize command; новый
known confirm создаёт Lesson сразу. `stage_materialize` теперь commit-free async. Actor admission пока
внутренний synthetic port, HTTP connector claim закрыт до .5; не live contract.

**Lock graph и границы транзакции.** До первой блокировки read-only discovery
собирает полные sets teacher/course/recipient/contact/pair/User и expected revisions.
Один transaction owner; без autoflush до получения необходимых locks. Порядок:

1. Operation mutex `(connection, operation UUID)`; для обычного LGG запроса scope
   actor/action/UUID. Только одна operation в транзакции, не брать другую позднее.
2. Schedule advisory `(80408, teacher_user_id)` всех затронутых teacher ID ASC.
   Existing regular mutex берётся здесь после schedule, не наоборот. Старые
   teacher single/series/price/restore paths сохраняют этот префикс.
3. Identity-key mutex `(installation, namespace, subject)` ASC для отсутствующих
   строк; затем contact ID ASC → recipient ID ASC → identity link ID ASC →
   parent grant ID ASC → interaction/window/booking/cancel rows по типу и ID ASC.
   Все mutating resolve/claim/rebind/grant/permission paths соблюдают этот порядок;
   окна без identity начинают сразу с window. Один recipient не merge-ится с другим.
4. Workspace creation mutex `(teacher_id, student_id)` ASC, затем **все existing
   courses ID ASC**, lessons ID ASC, teacher pairs ID ASC, memberships ID ASC.
   Pair mutex обязателен также обычному `personal_workspace(create=True)`; его
   потребитель должен lock/recheck existing course до `previous_link`, а не после.
5. Users ID ASC (включая actor/target, если их строки нужны для FK/проверки),
   Student profile ID ASC, invitation/refresh/challenge rows по типу и ID ASC,
   homework/placement rows ID ASC. Затем stage DML, audit/outbox/receipt и один commit.
   Auth-only paths начинают с User→token и **не** добавляют schedule/identity/course.

Существующий `active_students` использует JOIN FOR UPDATE сразу нескольких таблиц:
порядок плана SQL не равен этому графу. В .2/.3 touched consumers раскладывают
получение course/lesson/pair/membership/User locks на явные запросы по уровням,
после чего повторяют predicates active_students. Нельзя вызвать его под заранее
взятым User lock и надеяться на отсутствие цикла. `active_recipient` остаётся
course→lesson→membership, без позднего захвата pair. Grade path pair→User→Student
совместим; новый stage не берёт Student lock раньше User. Чтение profile/actor
без FOR UPDATE не считается lock, требуемые права перепроверяются под locks.

Implicit locks тоже часть графа: INSERT/FK/ON CONFLICT/ORM flush выполняются после
prelocks existing parents; новые User/Student/course создаются после них в этой
же транзакции. Нельзя вставить identity FK на existing User до захвата course,
а потом ждать course. Unique mutex не заменяет DB unique constraint. Namespace
новых advisory locks должен отличаться от schedule/regular; не использовать
нестабильный Python hash. Multi-key mutex брать в одном canonical sorted order.

После prefix locks повторить discovery predicates. Новая бронь/teacher/course,
смена recipient revision или новый workspace вне набора → полный rollback и
повтор discovery; **не** добавлять более ранний lock в работающую транзакцию.
До 3 внутренних попыток при changed-set/40P01/40001, затем 503 RETRY_LATER с той
же operation UUID. Timeout не превращать в success/rejected domain receipt;
клиент сначала читает operations. Перезапуск процесса читает durable inbox/receipt.
Это технический budget, не SLA; целые transactions retry, не отдельный SQL.

| Path | Lock prefix и что нельзя делать |
|---|---|
| Новый child / parent candidate | identity keys→contacts→recipient→grant; без User/course; pending grant не создаёт booking. Одновременный child first contact использует тот же child key |
| Confirm unknown | operation→schedule→identity/recipient/grant→handle/window→booking; нет User/enrollment; price NULL. Revoke grant сериализован тем же recipient→grant |
| Confirm known / invite+materialize | operation→все schedules→identity/recipient→booking→pair mutex→courses→lessons→pairs→memberships→Users→tokens→HW; snapshot читается под schedule/pair, не после commit |
| Self challenge issue/claim/finalize | issue User→challenge без identity mutation; claim identity→User→challenge без materialize; finalize отдельная operation по полному batch prefix, не продолжение transaction issue. Повтор consume не меняет target |
| Grant confirm/revoke, identity unlink | identity/recipient→link/grant; при проверке LGG состояния User позже. Не обновлять booking/course inline. Команда/worker перепроверяет revision и права перед действием |
| Teacher cancel/move/restore/series | schedule(s)→identity/contact→recipient→booking locks если изменяются→courses→lessons→pairs/memberships→Users→HW; обычные teacher writes видят unmaterialized booking в conflicts |
| Account disable/password/invite consume | User→tokens, без sync callback в identity/materialize; queued commands/delivery сами обнаруживают disabled/auth_version |
| Course archive/enrollment end | course→lesson/membership/HW, без обращения назад к recipient/schedule. Visibility/rights вычисляются при чтении/команде, без обратных sync hooks |
| Purge course с VK references | До course lock discovery→schedule(s)→identity/recipient/booking locks→course; recheck sets. Пока retention/адресное удаление не определены P01, отказ PURGE_BLOCKED, не CASCADE receipts/booking/identity |

В .2 нужны commit-free `stage_create_inactive_student`, `stage_link_student`,
`stage_ensure_workspace`, `stage_enroll`, `stage_bind_recipient`, `stage_materialize`;
в .3 `stage_confirm_booking`/`stage_cancel_booking`, `stage_lesson_with_snapshot`.
Каждый принимает одну session и prelocked context, flush допустим только после
prelocks; нет commit/rollback/network/token response внутри helper. Использовать
существующий `InvitationService.stage_issue` после User lock и eligibility check;
`create_user`, `personal_workspace`, public link/create_lesson/issue/consume не
вызывать вложенно. Обычные consumers сохраняют свои public signatures, но общую
часть переносят в stages. D04/audit/outbox/receipt завершаются до единого commit.

**Проектный wire contract v1.** JSON `extra=forbid`; opaque IDs/handles — строки,
operation_id UUID, revision/expected_revision positive int, public user IDs int>0.
Timestamps RFC3339 UTC с Z; `week_start` ISO date понедельника Europe/Moscow.
Строки имени 1–100 Unicode после trim, grade int1–11 или NULL, причина 1–1000;
текст не key/HTML/formula. Limit1–100, default25, opaque cursor, bounded date range
не более31 дней. Лимиты — локальный контракт, не VK quota. Body до64KiB, только
message_new/message_event/message_allow/message_deny; attachments/forwarded payload
не сохранять и не использовать для identity. `command` — tagged union:
menu_open {}, profile_submit {first_name,last_name,grade}, parent_candidate
{child_subject,first_name,last_name,grade}, prepare_booking {window_id,revision},
confirm_booking {handle,operation_id,expected_revision}, request_cancel
{handle,operation_id,expected_revision,reason}, withdraw_cancel {request_id,revision},
permission_changed {allowed:boolean}. Candidate/profile не ищут User по имени;
processed inbox result возвращает own recipient_handle/grant status. Поля другой
ветки запрещены; unknown action→422.
Raw external ID допустим только как
candidate/атрибут доверенного inbox, не как авторизация команды.

Connector MAC: key_id, Unix timestamp (±60s), nonce с128bit randomness и HMAC-SHA256
над `method + LF + exact path/query + LF + timestamp + LF + nonce + LF + SHA256(body)`.
Nonce UNIQUE(connection,key_id,nonce) минимум120s, clock drift→401; retry использует
новый nonce, прежние event/operation IDs. Connection/group берутся из credential,
несовпадение envelope запрещено. Это separate credential, не student JWT. На
ordinary browser mutations действуют A03 Origin/CSRF/session правила без исключений.

`ActorContext` — backend-issued opaque actor_context из inbox, связан с contact,
peer/group/connection и expires_at; command требует actor_context. Parent target
разрешается из подтверждённого grant; arbitrary teacher/recipient IDs не расширяют
scope. В личном message_new peer==sender; message_event actor проверяется отдельно.
Teacher decision из group chat допустим только после linked teacher проверки;
контекст чата не даёт доступ к полному расписанию/identity ребёнка.

| Endpoint / method | Request → response (только названные поля) |
|---|---|
| POST `/integrations/vk/inbox` | `{event_key,type,group_id,api_version,actor_subject,peer_id,occurred_at,conversation_message_id?,upstream_event_id?,command}` →202 `{inbox_id,state:accepted\|duplicate,actor_context?,expires_at?}` после durable commit, не после выполнения команды |
| GET `/integrations/vk/windows` | actor_context, teacher_user_id, week_start, cursor?,limit? →200 `{week_start,timezone,items:[{window_id,start_at,end_at,revision}],next_cursor}`; нет имён учеников |
| GET `/integrations/vk/inbox/{id}` | Credential того же connection + исходный event_key →200 `{inbox_id,state:accepted\|processed\|rejected,actor_context?,expires_at?,recipient_handle?,grant_state?,error?}`; чужой inbox404 |
| POST `/integrations/vk/interactions` | `{actor_context,action:confirm_booking\|request_cancel,recipient_handle,window_id?,booking_id?,expected_revision}` →200 `{handle,operation_id,expires_at}` после проверки actor/grant/scope; GET не создаёт persisted handles |
| POST `/integrations/vk/bookings/confirm` | `{actor_context,operation_id,handle,expected_revision}` →200 OperationResult, pending→202. UUID и target фиксируются при выпуске handle; два confirm одной кнопки используют один UUID |
| GET `/integrations/vk/operations/{id}` | actor_context →200 OperationResult; только исходный actor+connection, teacher видит бронь через свой endpoint |
| GET `/integrations/vk/schedule` | actor_context, recipient_handle, from,to,cursor?,limit? →200 `{items:[{booking_id,lesson_id?,start_at,end_at,status,revision}],next_cursor}`; parent только granted teacher/child, без материалов/цен |
| POST `/integrations/vk/cancel-requests` | `{actor_context,operation_id,handle,expected_revision,reason}` →OperationResult; handle определяет booking/schedule version |
| POST `/integrations/vk/cancel-requests/{id}/withdraw` | `{actor_context,operation_id,expected_revision}` →OperationResult; только исходный requester пока pending |
| GET/POST `/teacher-planning/booking-windows` | list week_start/cursor/limit; publish `{operation_id,week_start,items:[{start_at,end_at}]}` (1–100) →OperationResult с window refs, batch all-or-nothing |
| POST `/teacher-planning/booking-windows/{id}/close` | `{operation_id,expected_revision}` →OperationResult; consumed booking не отменяет, ставит explicit withdrawal |
| GET `/teacher-planning/bookings` и `/{id}` | own week/status/cursor/limit →BookingView (ниже); чужой объект404 |
| POST `/teacher-planning/bookings/{id}/resolve-invite` | `{operation_id,expected_revision,mode:new_student\|own_student,student_user_id?,expected_recipient_revision}` → `{operation:OperationResult,invitation:InvitationResponse\|null}`. new_student запрещает student_user_id; own_student требует его и existing own pair |
| POST `/teacher-planning/bookings/{id}/materialize` | `{operation_id,expected_revision,expected_recipient_revision,review_past:boolean}` →OperationResult; past требует review_past=true и явного teacher review; без invite при активном User |
| POST `/teacher-planning/parent-grants/{id}/confirm\|reject\|revoke` | `{operation_id,expected_revision}` →OperationResult; только teacher grant, external verification перед confirm |
| POST `/teacher-planning/cancel-requests/{id}/approve\|reject` | `{operation_id,expected_revision,expected_schedule_revision}` →OperationResult; only owning linked teacher |
| GET/POST/DELETE `/users/me/integrations/vk` | GET own status; POST `{operation_id,connection_id,purpose:student\|teacher}` + reauth →`{challenge_id,secret,expires_at}` один раз; DELETE `{operation_id,expected_revision}` + reauth →OperationResult |
| POST `/integrations/vk/challenges/claim` | `{actor_context,operation_id,secret}` →OperationResult без User/profile; contact proof bind, ещё не active link |
| POST `/users/me/integrations/vk/challenges/{id}/confirm` | `{operation_id,expected_revision}` + исходная session/reauth →OperationResult; показать подтверждающему маскированный claimed contact перед confirm |

`OperationResult={operation_id,state:pending|committed|rejected,result,error,
current,delivery}`. `result` при committed immutable `{kind,booking_id?,lesson_id?,
window_ids?,grant_id?,cancel_request_id?,invitation_issued?,challenge_id?}`; kind:
booking_confirmed|cancel_requested|cancel_withdrawn|cancel_approved|cancel_rejected|
windows_published|window_closed|grant_confirmed|grant_rejected|grant_revoked|
identity_claimed|identity_linked|identity_unlinked|recipient_resolved|materialized|
challenge_issued.
`error` null либо `{code,retryable}`; pending result/error null, rejected result null.
`current` nullable `{booking_status,revision,lesson_id,access_state}` читается заново,
не изменяет result. `delivery={state:not_planned|pending|sent|blocked|unknown|expired}`
отдельно, не success бронирования. Адреса/текст/recipient secrets здесь отсутствуют.

`BookingView={booking_id,revision,start_at,end_at,status:confirmed|cancelled,
recipient:{recipient_id,first_name,last_name,grade},lesson_id:null|int,
access_state:unresolved|awaiting_admin_link|inactive|active|blocked|review_required,
lesson_price_kopecks:null|int,delivery_state}` плюс own pending cancel request ref.
Teacher видит строку сразу при confirmed и различает «Бронь подтверждена» и
«Доступ не выдан»; после связывания строка заменяется по booking_id без дубля.
Unknown price NULL не доход/0. Parent/connector не получают BookingView с ценой.

Interactions POST — выпуск технической кнопки, не domain operation: backend
генерирует operation UUID для её confirm/cancel. Повтор prepare может выдать новую
кнопку и инвалидировать предыдущую незавершённую для того же actor/action/target;
committed receipts сохраняются. В GET окна/расписание только IDs/revisions,
persisted handle создаётся отдельным POST. Preparing не занимает время.

**Errors и receipts.** Envelope ошибки HTTP `{code,retryable,operation_id?}`,
без чужих IDs/имён/причин. 401 AUTH_REQUIRED|INVALID_SIGNATURE|REAUTH_REQUIRED;
403 CONNECTION_DISABLED|SCOPE_DENIED; 404 NOT_FOUND для чужого/missing объекта,
handle/operation/challenge; 409 PAYLOAD_MISMATCH|STALE_REVISION|SLOT_UNAVAILABLE|
IDENTITY_COLLISION|ADMIN_LINK_REQUIRED|GRANT_PENDING|GRANT_REVOKED|ACCOUNT_BLOCKED|
COURSE_NOT_WRITABLE|REVIEW_REQUIRED|PURGE_BLOCKED; 410 HANDLE_EXPIRED|CHALLENGE_EXPIRED;
422 INVALID_REQUEST|UNSUPPORTED_EVENT|EVENT_KEY_UNAVAILABLE; 429 RATE_LIMITED;
503 RETRY_LATER. retryable=true только429/503, Retry-After технический backoff.
Для operation GET terminal rejection идёт200 со state=rejected и тем же code;
первичный command возвращает соответствующий4xx. Security refusal до admission
не создаёт публичного receipt и не подтверждает существование чужой operation.

Receipt UNIQUE(connection,operation_id), bound actor_contact_id/action/target/hash;
для LGG операций UNIQUE(actor_user_id,action,operation_id). Hash канонического
validated DTO, без MAC/nonce/actor_context, включает immutable target/revisions.
Подтверждённый receipt читается после текущей auth/scope проверки **до** TTL/CAS
проверки старой кнопки: HTTP timeout после commit возвращает тот же результат.
Новая operation по expired/stale handle отвергается, прежняя booking не воскресает.
Grant revoke запрещает новые действия/чтение child schedule; собственный receipt
можно прочесть в минимальном виде без актуального расписания/сведений ребёнка.
Disabled connection не получает receipt. Worker pending lease не является успехом.

Invite secret/challenge secret не сохранять в receipt/inbox/log: только digest.
Первичный response после commit содержит secret только адресному LGG caller;
повтор operation сообщает issued/claimed статус без повторной выдачи секрета.
Потерянный invite response → явная reissue D01 (старый token invalidated), не новый
User/booking. Для active existing User teacher не может заменить self-link protocol
или reset, даже при собственной паре. Новый inactive User связывается teacher по
проверенной recipient evidence; parent grant сам по себе не child contact proof.

**Additive schema constraints.** В дополнение к A14.1: UUID PK новых сущностей,
FK scoped compound `(connection_id,id)`/`(installation_id,id)` для запрета cross-
connection references; User/teacher public IDs сопоставляются с внутренними FK.
CHECK все revision>0, start<end, price NULL или >=0, статусы только перечисленные;
Booking confirmed/cancelled, Window published/closed/consumed; ParentGrant states
pending/confirmed/rejected/revoked. Grant revision/approved actor обязательны для
confirmed parent booking; child actor не требует grant. Partial UNIQUE confirmed
booking(window_id), UNIQUE Booking.lesson_id WHERE NOT NULL, active identity
(contact,purpose), canonical recipient(installation,child_contact) WHERE NOT NULL,
one pending CancelRequest(booking_id,schedule_revision).
Partial UNIQUE canonical recipient(installation,linked_student_user_id) WHERE NOT NULL;
вторая попытка связывания→IDENTITY_COLLISION, не silent recipient merge. Linked recipient User
меняется только CAS с проверенной identity, не ON CONFLICT reassignment.
Challenge digest UNIQUE; session binding/auth_version/group/purpose/claimed_contact/
expires_at/consumed_at; один claim и одна финальная consume под lock. Имя не unique.
Window non-overlap проверяется под schedule lock; SQL exclusion всех Lesson нет.
Indexes: windows(teacher,start,status), booking(teacher,start,status),
booking(recipient,status,start), grants(teacher,status), inbox(connection,state,next_at),
delivery(state,due_at), receipt(owner,operation_id), challenge(digest).
Receipt/inbox UNIQUE event key и payload hash: одинаковый key с иным payload→409
PAYLOAD_MISMATCH, не «успешный дубль». Lesson reference RESTRICT, не CASCADE:
purge с сохранённой бронью отказывает до P01 deletion protocol.

Handle random>=128bit, backend stores digest+bound actor/target/revisions/operation;
TTL10min для кнопок и challenge, ActorContext10min, пять неуспешных challenge attempts
на actor за10min (не блокировать жертву по переданному secret); single-use и CAS.
Это fixture defaults, не retention/обещания. Не логировать handle/secret. Inbox key
с upstream event_id включает connection/type/event_id; fallback message_new —
positive peer+conversation_message_id. Для message_event без надёжного event key,
allow/deny без event identity — карантин EVENT_KEY_UNAVAILABLE, без доменной мутации;
permission allow требует fresh check. Нельзя dedupe по нулю/тексту/времени локального
получения и терять повторный реальный click. Checkpoint только после durable inbox;
upstream gaps фиксировать, не заявлять replay completeness. Fixtures покрывают и
отказ для malformed legacy events. SDK-поведение не подменяет официальный SLA.

**Четыре source walkthrough / будущие concurrency assertions.** Во всех timeout
после commit → прежний receipt; timeout до commit → retry той же operation; revoke
до domain commit → запрет новой команды, после commit не отменяет бронь; teacher
series на том же schedule lock либо первая блокирует bot confirm, либо видит его
booking conflict. Это reasoning по исходникам, не выполненные DB tests.

| Последовательность | Результат и обязательный контрпример .2/.3 |
|---|---|
| Новый child | canonical recipient→confirmed booking NULL price→teacher explicit new student→inactive User/own workspace/enrollment/invite+Lesson→activation без нового Lesson. Два first contacts/resolve не создают дубль; rollback после каждого stage сохраняет исходную бронь |
| Parent до child first contact | claimed contact candidate→pending grant (ни календаря, ни брони)→teacher confirm relation→confirmed booking без доставки claimed child. Child first contact канонизирует тот же key; child contact proof/permission отдельно. Revoke гоняется с confirm под recipient→grant, не отключает child identity |
| Existing shared User | self challenge claim+session confirm→существующий User, teacher own active pair→booking+Lesson. Другой teacher без пары получает только свою booking unresolved/awaiting_admin_link, admin link отдельный; обе пары никогда не захватываются по разному порядку, grade/price/invite не вызывают cycle |
| Unknown recipient, future/past | Future связывается один раз по полному sorted batch, price snapshot неизменен. Past остаётся review_required до явного review owning teacher; inactive/archive/revoked права не оживляются. Новая booking второго teacher во время discovery требует rollback/retry sets; нельзя взять его schedule после recipient |

Future snapshot NULL остаётся NULL даже при появившейся ставке; past review не
переоценивает D12 и не трогает checked D04 placements. Неоднозначные/архивные
workspace — COURSE_NOT_WRITABLE, никакого случайного выбора/restore. Materialize
не распространяет teacher права на чужие bookings: self-link подтверждает identity
общего User, но каждый teacher scope materialization проверяется отдельно, без
принудительного admin enrollment. До .2/.3 SQL sessions/migration/failure injection
lock graph — спецификация; .1 может начинаться только отдельным поручением.
