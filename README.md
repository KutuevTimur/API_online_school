# LGG backend — локальная разработка

Python 3.14 (проверен локально), FastAPI / SQLAlchemy / PostgreSQL 15.
Docker Desktop для Apple Silicon или Intel по архитектуре Mac. Нужны работающий
Docker Engine и современный `docker compose` (Compose v2 или более новый).
Проверено 15.10.2026: Engine 29.8.2, Compose 5.6.0.

## Подготовка

Из корня внутреннего репозитория `API_online_school`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
docker version
docker compose version
```

Для новой машины создать `.env` из `.env.example`, `.env.test` из
`.env.test.example`. Заменить все `replace-with-*` на разные случайные значения
(например, генерировать через `secrets.token_hex(32)`), хранить только локально.
В этой сессии файлы уже созданы, повторно заменять их не нужно. Не публиковать
файлы или вывод `docker compose config` с подставленными значениями.

## Test

```sh
docker compose --env-file .env.test -f compose.test.yaml config --quiet
docker compose --env-file .env.test -f compose.test.yaml up -d --wait postgres
MODE=TEST .venv/bin/python -m pytest tests_unit -q
MODE=TEST .venv/bin/python -m pytest --collect-only -q
```

Проект `lgg-test`, loopback порт 55432, БД `lgg_test`, роль `lgg_test_app`,
volume `lgg-test_postgres_data`. Перед запуском убедиться, что порт свободен и
контейнер относится к проекту lgg-test. БД и ограниченную роль создаёт Compose;
приложение не создаёт БД через административную роль. Тестовый конфиг читает
только `.env.test`; переменные DB из окружения и `.env` не наследуются.
Guard требует точные MODE/host/port/DB/role и `ALLOW_TEST_DB_RESET=1`, проверяет
также URL engine и bind session factory. Test media создаются через pytest
`tmp_path_factory`, ручного удаления media в fixtures нет.

Guard/unit и сборка тестов проверены; collect-only не означает прохождение
полного набора. Полный DB baseline/миграции — T02. Старые функциональные тесты
создают ORM-схему через защищённую fixture; их полный запуск в T01 не выполнен.
Standalone `src.tools.creating_db`, `recreate_test_db`, `drop_schema` разрешены
только для этого test contract и используют временное media; они не заменяют
проверку миграций. Никогда не направлять их на неизвестную БД.

Остановка без удаления данных:

```sh
docker compose --env-file .env.test -f compose.test.yaml stop
```

## Dev

```sh
docker compose --env-file .env -f docker-compose.yaml config --quiet
docker compose --env-file .env -f docker-compose.yaml up -d --wait postgres
docker compose --env-file .env -f docker-compose.yaml build backend
docker compose --env-file .env -f docker-compose.yaml run --rm backend alembic upgrade head
docker compose --env-file .env -f docker-compose.yaml up -d backend
```

Проект `lgg-dev`: БД `lgg_dev`, роль `lgg_dev_app`, loopback порт 55431,
отдельные volumes `lgg-dev_postgres_data` и `lgg-dev_media`. Backend внутри сети
использует postgres:5432, API опубликован только на 127.0.0.1:8018. На хосте
конфиг использует 127.0.0.1:55431. Redis не обязателен и не подключается.
Dev build/start и HTTP-проверка T00–T07 выполнены 15.10.2026;
[результаты](docs/plan/T00_T07_ACCEPTANCE.md). Перед первым входом нужны миграции
из команд выше и первый admin через CLI. У frontend пока нет реализации. Изменение env-пароля не меняет пароль уже существующего volume.

Не применять `down -v` к чужим проектам. Внешняя БД остаётся UNKNOWN.
Commit/push/deploy выполняются только по отдельному поручению.

### Миграционный baseline T02

Только для выделенной локальной lgg-test, после проверки Compose project/порта:

```sh
docker compose --env-file .env.test -f compose.test.yaml ps
MODE=TEST .venv/bin/alembic upgrade head
MODE=TEST .venv/bin/alembic check
MODE=TEST .venv/bin/python -m pytest tests/migrations -q --confcutdir=tests/migrations
MODE=TEST .venv/bin/python -m pytest -q
```

Migration tests **сбрасывают public schema только guarded lgg-test** и строят её
через Alembic; не запускать параллельно с другими DB tests/локальным приложением.
Функциональные legacy fixtures пока используют create_all: они не заменяют
migration checks. После полного pytest схема может быть создана legacy fixtures
без alembic_version; не stamp её. Для чистого локального baseline сначала выполнить
migration tests (они оставят пустую test schema), затем upgrade head/check.

Initial dev revision d98c55d6402c сохранена; историческая коррекция —
только autcrement → autoincrement. Следующая 56c4070bf9cd согласует soft-delete
с текущими моделями. Mapping is_deleted = NOT is_active разрешён только для
synthetic baseline; deleted_at остаётся NULL. Читателей старых полей в текущем
коде нет. Downgrade теряет deleted_at и проверен только на disposable DB.
Main baseline 1c3d40e331ff не поддерживается: preflight отказывает, требуется
отдельный план, read-only inventory и backup реальных данных. Не stamp/drop.
Результаты и ограничения: [TEST_BASELINE](docs/plan/TEST_BASELINE.md).

### T04: refresh rotation and re-login

Migration `c3882e989a1e` replaces raw refresh secrets with unique SHA-256
 digests and session families, revokes every legacy refresh and adds
`users.auth_version`. Old JWTs without `ver` are rejected. Every user must log in
again after this transition. Downgrade cannot restore secrets: rows stay revoked
with invalid placeholders. For any external database, inventory and a maintenance
window are required before applying this migration; only synthetic lgg-test was used.

Refresh rotates atomically under PostgreSQL locks (user first, token second).
Confirmed reuse revokes that user's entire session family, including the active
descendant. Concurrent tabs, retries or a lost successful response can therefore
require re-login. Browser single-flight and HttpOnly cookie/CSRF integration remain
T14; current API uses bearer access and JSON refresh.

Authenticated `POST /auth/logout` returns `200 {"success": true}` for own repeated,
unknown or foreign refresh; only an owned family is revoked. Access remains valid
until expiry on logout. Password change/reset revokes all refresh of the target
user and increments `auth_version`, immediately rejecting their old access tokens.

`ACCESS_TOKEN_EXPIRE_MINUTES` (default 15, range 1–60) and
`REFRESH_TOKEN_EXPIRE_DAYS` (default 30, range 1–90) are read from the selected env
file. No raw refresh secret is stored in the database; clients must keep it private.

### T05: роли и первый администратор

Сначала применить миграции в **выбранном локальном окружении**. Для изолированного
lgg-test (на synthetic данных):

```sh
MODE=TEST .venv/bin/alembic upgrade head
MODE=TEST .venv/bin/python -m src.tools.bootstrap_admin
```

CLI запрашивает username, email и дважды пароль (ввод скрыт, минимум 12 символов).
Не передавайте пароль аргументом команды или в чат. Bootstrap создаёт только
первого ADMIN; повтор, включая одновременные запуски, не создаёт нового admin и
не меняет пароль существующего. Если admin уже есть, используйте его аккаунт;
дополнительный admin требует отдельной CLI-процедуры вне текущего bootstrap.
В lgg-test автоматические тесты очищают synthetic аккаунты; это не постоянная
учётная запись. Dev запускается с MODE=DEV и своей `.env`, отдельно от lgg-test.

`POST /auth/register` с bearer teacher создаёт только student и назначает его
этому teacher атомарно. С bearer ADMIN можно создать teacher/student.
Роль admin не создаётся HTTP. Оба старых master-password адреса требуют bearer
ADMIN; поле `password_for_admin` теперь игнорируется и не даёт доступа.
Для назначения существующего ученика второму teacher:

```json
{"teacher_user_id": 1, "student_user_id": 2}
```

Отправить этот body в `POST /teacher_students` с bearer ADMIN. Повтор безопасен;
ответ содержит эти же user IDs и `active: true`. Списки/файлы и полная матрица
объектных разрешений будут закрыты в T06; этот этап ещё не означает готовность
приложения к реальным данным. Invite/reset выполняются отдельно в T05b.
Миграция T05 заполняет только связи из действующих неархивных курсов/зачислений;
спорные архивные/истёкшие пары не активируются. SQL отчёта — в карточке T05.
Downgrade T05 при наличии admin отклоняется без удаления аккаунтов.

### T05b: приглашения и восстановление (D01)

`POST /auth/register` и оба admin aliases принимают username, role, first_name,
last_name и необязательный email. Поле password больше не входит в контракт:
если старый клиент его пришлёт, оно игнорируется и не задаёт пароль аккаунта.
Ответ содержит публичные поля пользователя, `activation_link` и `expires_at`.
Новый аккаунт ожидает активации (`is_activated=false`), независимо от `is_active`.
Существующие аккаунты при миграции остаются активированными; email сохраняются.
Вход теперь **только по username**. Коллизии username/email миграция считает
и сообщает числом без адресов; владельцы входят по своему username, совпадение
с чужим email не выбирает чужой аккаунт. Фиктивных email не создаём.

`POST /account_invitations/issue` (bearer) принимает
`{"user_id": 123, "purpose": "invite"}` либо `purpose: "reset"`.
Teacher повторно приглашает только своего ученика до активации. Admin выдаёт
приглашения и восстановление активированного аккаунта после внешней проверки
личности. Для отсутствующего, отключённого или неподходящего по состоянию
аккаунта ответ одинаков: 200 с `activation_link: null, expires_at: null`.
Приглашение живёт 72 часа, reset — 1 час; перевыдача отменяет предыдущую ссылку
того же назначения. Секрет выдаётся только при создании/перевыдаче ссылки.

Ссылка относительная: `/activate#token=…` или `/reset-password#token=…`.
Страницы ещё **не реализованы** (T14); сейчас это backend API-контракт,
а не готовый пользовательский сценарий. Будущий frontend добавит origin,
прочитает fragment, уберёт его из адресной строки и отправит секрет JSON body
в `POST /account_invitations/consume`:
`{"token": "…", "purpose": "invite", "new_password": "…"}`.
Секрет нельзя отправлять в query string, логи, аналитику или чат. Отправитель
вручную передаёт полную ссылку лично нужному человеку. До погашения ссылка
даёт её получателю возможность задать пароль.

Consume возвращает `200 {"success": true}`; expired/used/unknown/wrong-purpose
и отключённый аккаунт — одинаковый 401. User → token row locks сериализуют
потребление/перевыдачу; hash пароля, активация, погашение, audit и отзыв сессий
фиксируются одной транзакцией. В БД только digest случайного 48-byte секрета.
Пароль: минимум 8 символов, максимум 72 UTF-8 bytes (ограничение bcrypt).

Все четыре старых password aliases работают только для самого пользователя
и требуют `current_password` + `new_password`. Teacher/admin не задают чужой
пароль этим путём. Смена/reset закрывают прежние access/refresh пользователя;
self-change также отменяет ожидающие reset-ссылки. Отключение admin не снимается
приглашением или reset. Роли и is_active через consume не меняются.

Login, consume, issue и self-change имеют независимые фиксированные окна
15 минут: 10 попыток на идентификатор, 100 на IP; ответ 429 с Retry-After.
Счётчики PostgreSQL общие для workers, неуспешные попытки тоже учитываются;
истёкшие записи очищаются при следующем обращении. На границе окна возможен
двойной burst. Используется IP непосредственного соединения, forwarded headers
не считаются доверенными; proxy-конфигурация и настройка лимитов — перед T17.
Audit хранит actor/target user IDs, действие, результат, время и correlation ID,
без пароля/токена/контактов. SMTP/автоматические письма не добавлены.

Downgrade T05b отказывается до DDL, если есть email=NULL или ожидающий активации
аккаунт: не подставляет email и не активирует пользователей для отката.
Фильтрация профилей/списков/файлов реализована в T06 (см. ниже); реальные аккаунты
пока не подключать. Проверки — карточка docs/plan/tasks/T05b.md.

## Object permissions (T06)

Списки курсов/занятий/профилей фильтруются в SQL до подсчёта total и pagination.
Teacher видит свои курсы и занятия; общий student не открывает курсы второго
teacher. Student видит свои курсы и персональные LessonStudent/материалы/ответы.
Admin читает учебные данные, но не получает отдельного teacher workflow.
Чужой или отсутствующий объект — 404; запрет операции на видимом объекте — 403.
Отсутствие Teacher/Student профиля не снимает фильтр списка.

Teacher читает минимальную карточку связанного student: user_id, username,
first_name, last_name, avatar_path (относительный URL). Email/отчество/контакты
доступны самому пользователю/admin; teacher не меняет общий профиль или аватар.
Student читает минимальные карточки своих связанных teacher. Admin получает
полные профили; teacher в списке teacher видит себя. Списки учитывают active
teacher_students. Зачисление в свой курс требует этой связи; добавление в урок
дополнительно требует действующего StudentCourse. Вложенный student в зачислении
содержит только user_id/имя/фамилию/аватар; student_id заменён на student_user_id.

Обычный `PATCH /users/{user_id}` отвергает role/is_active (422).
`PATCH /users/{user_id}/account-status` с `{"is_active": false}` доступен admin;
изменение отзывает refresh и повышает auth_version. Admin-правки профиля/аватара
и статуса пишут account audit без содержимого профиля.

`GET /users/{user_id}/avatar` и `GET /courses/{course_id}/avatar` требуют Bearer
и ту же политику чтения объекта. Поле avatar_path в публичном JSON содержит
этот URL, а не путь диска. Прямой file_id ответа проверяется по цепочке
homework → submission → file; ID lecture/homework сверяется с LessonStudent.
Legacy avatar alias защищён той же проверкой.

`DELETE /courses/{id}?hard=true` закрыт для teacher; безопасный admin purge,
архив/read-only/cutoff/restore и согласование D02 относятся к T07. Пока сохраняется
существующее чтение персонального LessonStudent; новая cutoff-политика не вводится.
Истёкший/отключённый StudentCourse закрывает курс одинаково в list/detail/avatar.
Формы frontend отсутствуют; пользовательский ручной сценарий — после T14.
Полная таблица endpoint → policy и результаты проверок: docs/plan/tasks/T06.md.

### T07: архив, история доступа и очистка файлов

Обычный `DELETE /courses/{course_id}` и `DELETE /lessons/{lesson_id}` архивирует
объект; зависимости и файлы сохраняются. Повторное архивирование безопасно.
Slug курса остаётся занят для восстановления. Отдельно архивированный урок
не восстанавливается при восстановлении курса. Учебные изменения и проверка
работ в архиве запрещены; чтение и закрытые скачивания продолжают работать.

После открепления/expiry ученик читает персональную историю до cutoff включительно.
Граница проверяется по времени создания персонального grant и публикации материала,
ответа/файла, а не по дате запланированного занятия. Поздняя публикация в старый урок
не открывается. Повторное зачисление не открывает материалы, добавленные в перерыве;
оно не снимает отдельный admin-отзыв чтения или открепление от отдельного урока.
Окончание teacher_students также ограничивает историю/запись только этого teacher;
восстановление связи сохраняет перерыв доступа.

Admin API (обычный bearer ADMIN; секреты не помещать в историю команд):

- `POST /courses/{course_id}/restore`, `POST /lessons/{lesson_id}/restore`.
- `PATCH /courses/{course_id}/students/{user_id}/history-access`, JSON
  `{"revoked": true}`; `false` возвращает чтение в пределах прежних границ.
- `POST /courses/{course_id}/purge`, JSON с точными `confirm_course_id` и
  `confirm_name`. Это отдельное безвозвратное действие, не archive/restore.
- `POST /admin/file-deletions/retry?limit=100` повторяет сохранённую очередь.

Purge удаляет учебную цепочку и записывает file_deletions в одной транзакции.
Только после commit начинается физическая очистка. Ошибка/restart оставляет
задания для повторного запуска через admin endpoint; отдельный scheduler пока
не подключён. `cleanup.failed > 0` требует повторной обработки/разбора, это не
откат уже выполненного удаления курса. Падение до commit сохраняет курс и файлы;
падение после commit может дать HTTP error при уже удалённом курсе — проверять
состояние и запускать retry, не восстанавливать БД вслепую.

Worker удаляет только отдельные файлы внутри разрешённых PathsConfig каталогов,
не удаляет каталоги рекурсивно, повторно проверяет ссылки из оставшихся записей
и не трогает общий объект. Неиспользуемые пустые папки могут оставаться. Пути вне
разрешённых каталогов/конечные симлинки и используемые файлы остаются в очереди; нельзя
снимать защиту или удалять общий файл вручную ради пустой очереди. Audit не имеет
FK на удаляемый курс, поэтому запись об удалении сохраняется.

Миграция T07 отказывается от неоднозначных duplicate memberships и персональных
LessonStudent без StudentCourse до DDL: сначала нужна явная сверка таких записей.
Legacy открепления получают cutoff из deleted_at либо updated_at. Исторические
факты перерывов, не сохранённые старым кодом, задним числом не восстанавливаются.
Небезопасный downgrade при новой истории/архивах/audit/очереди запрещён.

Тестовые файлы — временные локальные каталоги pytest `lgg-test-media*`, их сроком
жизни управляет pytest. Для dev остаётся предусмотренное persistent media-хранилище
(см. Compose/ENVIRONMENT): T07 не переносит и не очищает его. Backup должен включать
БД с очередью и согласованную копию media; процедура restore с учётом удаления — T18.


### Повторная HTTP-проверка T00–T07 (только synthetic lgg-dev)

После запуска dev и миграций на этом компьютере:

```sh
MODE=DEV .venv/bin/python -m src.tools.smoke_t00_t07
# После перезапуска backend/PostgreSQL:
MODE=DEV .venv/bin/python -m src.tools.smoke_t00_t07 --verify-retained
```

Скрипт проверяет точный loopback DB contract lgg_dev/lgg_dev_app/55431 и
работает по HTTP с 127.0.0.1:8018. Создаёт искусственные аккаунты/курсы,
purge выполняет только для ID курса, созданного текущим запуском. Не очищает
схему и не удаляет другие курсы. Bootstrap создаёт только первого admin;
если admin уже существует, для входа нужен сохранённый synthetic audit admin.
Учётные данные сохраняются локально в ignored `.env.audit-access` с правами 0600;
не публиковать файл или его содержимое. При прерванном запуске synthetic записи
остаются; повтор использует новые уникальные имена.

Файлы backend находятся в Docker volume `lgg-dev_media` (`/app/media` внутри
контейнера), БД — `lgg-dev_postgres_data`. Перезапуск сохраняет оба volume.
Просмотр списка файлов без изменения:

```sh
docker compose --env-file .env -f docker-compose.yaml exec -T backend find /app/media -type f
```

Резервную копию файлов можно получить локально (для согласованной копии сначала
остановить backend):

```sh
docker cp lgg-dev-backend-1:/app/media ./media-dev-backup
```

 Это копия файлов, не полный backup БД (полный restore — T18).
Остановить окружение без удаления данных:

```sh
docker compose --env-file .env -f docker-compose.yaml stop
```

### T08 — персональное расписание и ссылки

`POST /lessons` теперь одной транзакцией создаёт Lesson и LessonStudent.
Нужен свой активный курс с действующим зачислением и связью teacher–student:
при одном подходящем ученике выбор автоматический; при нескольких передать
`student_user_id`; при отсутствии подходящего ученика — 422 без частичного урока.
Отключённые аккаунты, завершённые/истёкшие зачисления и отозванная история
не подходят. Ожидающий активации, но включённый аккаунт можно записать заранее.
Внутренние student_id/teacher_id клиент не передаёт.

```json
{
  "course_id": 123,
  "title": "Индивидуальное занятие",
  "scheduled_at": "2026-10-20T18:00:00+03:00"
}
```

Длительность по умолчанию 55 минут, явно — положительное целое. Даты создания,
переноса и фильтров требуют timezone; время урока в ответе — UTC. Ввод/отображение
Europe/Moscow с подписью зоны реализуется в будущем интерфейсе, не в backend.
Уроки не перемещаются автоматически с течением времени.

`PATCH /lessons/{id}` меняет отдельный урок: `scheduled_at` переносит время,
`duration_minutes` меняет длительность; `status` принимает `scheduled`, `completed`,
`cancelled`. Отметка completed ручная, автоматического закрытия по часам нет.
Переходы между этими статусами разрешены владельцу teacher в активной истории.
Отмена сохраняет участника/материалы/ДЗ/ответы и сама по себе не закрывает учебные
изменения. Архив — отдельный DELETE, с прежним read-only и admin restore.
Student и admin не управляют teacher расписанием. `GET /lessons?status=completed`
фильтрует до count/pagination; без фильтра выдаются все разрешённые статусы.

При создании/обновлении ответ teacher содержит `warnings`:

```json
{"warnings": [{"code": "teacher_time_overlap", "lesson_ids": [456]}]}
```

Это предупреждение о пересечении интервалов собственного teacher, сохранение
разрешено. Смежные интервалы без общего времени, сам обновляемый урок,
отменённые/архивные уроки и архивные курсы исключаются. Completed учитывается.
В detail/list warnings пустой: ответ student не раскрывает ID других занятий.
Предупреждения не являются системой бронирования; еженедельный мастер — T08b.

`call_url` в create/update курса задаёт постоянную внешнюю ссылку. Необязательный
`call_url_override` в create/update урока заменяет её; null очищает замену.
`effective_call_url` урока содержит замену либо текущую ссылку курса. Изменение
курса влияет и на старые уроки без замены. Разрешены только валидные http/https,
backend URL не скачивает. Это ссылка на сторонний сервис, не встроенная видеосвязь.

Migration `29e67248e0f3`: старые NULL duration → 55, явные положительные значения
и история сохраняются, status старых уроков scheduled (по датам не угадывается).
Старые нулевые/отрицательные duration останавливают upgrade до DDL; нужен разбор
данных. Downgrade отказывается терять completed/cancelled и meeting links.
При допустимом downgrade заполненные 55 остаются числами; бывшие NULL не угадываются.

Повторить реальный HTTP smoke на synthetic dev (после миграций/обновления образа):

```sh
MODE=DEV .venv/bin/python -m src.tools.smoke_t00_t07
MODE=DEV .venv/bin/python -m src.tools.smoke_t08
```

Первый runner адаптирован к автоматическому участнику T08: повторный add получает
409. Второй создаёт отдельный synthetic курс, сохраняет его для просмотра и пишет
`t08_course_id`/`t08_lesson_id` в локальный ignored `.env.audit-access`; пароли и
токены не печатает. БД не сбрасывает, purge не делает. Ручное знакомство со Swagger
и фактические результаты — [карточка T08](docs/plan/tasks/T08.md).

### T09: черновик, отправка и вложения

`POST /homeworks/{homework_id}/submissions` создаёт один рабочий draft
(`submitted_at=null`, `version=1`); при существующем ответе — 409. Получить его
и исторические попытки можно через GET того же маршрута. `is_working=false`
означает историческую попытку, доступную только для чтения.

`POST /submissions/{id}/submit?homework_id=...` отправляет непустой ответ;
повтор до проверки возвращает тот же результат. Поздняя отправка разрешена.
`PATCH /submissions/{id}/student?homework_id=...` принимает multipart
`text_content`, `files` и необязательный `expected_version`: файлы добавляются,
прежние сохраняются; отсутствие `text_content` сохраняет прежний текст.
Устаревшая версия даёт 409. Изменение увеличивает `version`.

Точечные операции: DELETE `/submissions/{id}/files/{file_id}?homework_id=...`
и PUT того же URL с multipart `file` (необязательный `expected_version`).
PUT возвращает новый file_id. Последнее содержимое submitted удалить нельзя.
Checked и исторические ответы нельзя изменять или удалять; новая пересдача
не создаётся. Все операции требуют прежних объектных прав и активного участия.

При rollback новые файлы удаляются; старые при успешном delete/swap попадают
в durable `file_deletions`. Существующий admin retry cleanup удаляет их после
проверки ссылок и PathsConfig. Автоматический scheduler отсутствует; полный
storage contract/лимиты и reconciliation аварийных orphan uploads — T12.

### T10: очередь и окончательная проверка ответа

`GET /submissions/review-queue` доступен только teacher. Возвращает рабочие
submitted ответы его активных курсов/занятий/участий; draft, checked и старые
попытки исключены. Фильтры `course_id`, `student_user_id`; `limit` (1–1000),
`offset`; total учитывает фильтры даже при пустой странице. Порядок — сначала
ранее отправленные, затем ID. В каждой записи текущие текст/файлы/version,
название ДЗ и course_id/lesson_id/student_user_id.

`PATCH /submissions/{id}/teacher?homework_id=...` принимает JSON:

```json
{"expected_version": 3, "grade": 0, "teacher_comment": "Комментарий необязателен"}
```

`grade` — обязательное целое 0–5, `expected_version` — обязательное целое >=1.
Дроби, строки, bool и пропущенные значения отвергаются (422). `status` можно
не передавать; единственное допустимое значение — `checked`. Неизвестные поля
запрещены. Если ученик успел изменить ответ — 409: перечитать ответ и решить,
подтвердить ли оценку новой версии. Проверка draft — 409; checked/history,
архив и завершённое участие доступны только для чтения (403). Проверяющий
повторно проверяет доступ под общими с редактированием блокировками.

Ответ содержит checked_at UTC и checked_by **как user_id преподавателя**;
внутри БД checked_by остаётся FK teachers.id. Ученик читает тот же результат
через существующие detail/list. После проверки нельзя изменить ответ,
вложения, оценку или комментарий. Возврат на доработку отсутствует (D05).
Numeric-колонка и прежние значения оценок сохранены без округления/миграции;
целочисленное ограничение применяется ко всем новым review API запросам.

Synthetic HTTP-проверка использует существующие локальные ignored credentials,
создаёт отдельный T10 курс и сохраняет его для просмотра, без reset/purge:

```bash
MODE=DEV .venv/bin/python -m src.tools.smoke_t10
MODE=DEV .venv/bin/python -m src.tools.smoke_t10 --verify-retained
```

Вторую команду запускать после restart backend для проверки сохранности.
Секреты не выводятся. Полные факты проверок — [T10](docs/plan/tasks/T10.md).

### T11 — автоматический срок и долг (локально)

`POST /homeworks` больше не принимает ручной `deadline` (422). Срок следует
следующему допустимому занятию того же курса и ученика; при отсутствии — null.
Долг: `POST /homeworks/{homework_id}/debts` с JSON `{"lesson_id": 123}` (ID своего
более позднего урока). `GET /homeworks/{homework_id}/placements` возвращает историю
размещений и сроков. Checked замораживает историю, поздняя сдача разрешена.
Контракт, migration backfill и проверки — [T11](docs/plan/tasks/T11.md).

Synthetic dev smoke (существующий локальный стенд, без reset/purge):

```bash
.venv/bin/python src/tools/smoke_t11.py
.venv/bin/python src/tools/smoke_t11.py --verify-retained
```

Скрипт читает ignored `.env.audit-access`, выводит только результаты проверок;
не отправлять этот файл в чат/Git. Retained запуск — после healthy backend.

### T12: приватные файлы (локально)

Новые upload используют immutable UUID и FileAsset metadata; auth/download URL
и file_id сохраняются. PDF хранится один раз. Лимиты: 20 MiB/file, 10 файлов и
100 MiB исходников/ответ; unsupported/повреждённые/анимированные файлы отклоняются,
Office upload в MVP выключен. D06 принят: фото → WebP ≤2560/q85 без EXIF/GPS,
с исправлением поворота/alpha, без увеличения. В synthetic dev после визуальной
приёмки новые оригиналы удаляются через очередь только после ready/link commit;
на новом окружении PHOTO_ORIGINALS_APPROVED=0 до приёмки. Старые фото не нормализуются.
Квота документов/ответов — 1 GiB/ученика, admin может увеличить; архивы учитываются,
при переполнении старые downloads остаются доступны. Owner/admin report:
GET /users/{user_id}/storage, override PATCH /admin/users/{user_id}/storage-quota
с JSON {"limit_bytes": 2147483648}. Изменения квоты аудируются.

Dev media находится в persistent volume `lgg-dev_media` (`/app/media` в backend),
pytest — только в выделенной временной папке. Перезапуск сохраняет dev файлы;
`docker compose down -v` удалит volume и для обычного завершения не используется.
Просмотр — авторизованные `/lectures/{id}/file`, `/homeworks/{id}/file` и
`/submissions/{id}/files/{file_id}?homework_id=...`, включая авторизованный Range.
Локальное содержимое можно проверить через
`docker compose --env-file .env -f docker-compose.yaml exec backend ls /app/media`.
Копирование media: `docker compose --env-file .env -f docker-compose.yaml cp backend:/app/media /private/tmp/lgg-media-backup`.
Для согласованной резервной копии нужны остановленные записи и соответствующая
копия БД; полный backup/restore runbook и проверка восстановления — T18.

После dev build + `alembic upgrade head` HTTP smoke:
`MODE=DEV .venv/bin/python -m src.tools.smoke_t12`;
после restart: та же команда с `--verify-retained`.
Credentials/IDs только в ignored `.env.audit-access`, не печатать этот файл.


T12 maintenance запускается только на проверенном local dev/test. Docker backend
имеет явный MODE=DEV. Worker: 60s retry/cleanup, 24h grace для orphan UUID,
DB/manifest refs перепроверяются. Migration CLI (внутри backend):
`python -m src.tools.storage_maintenance migrate --actor-user-id ID` — dry-run;
добавить `--apply` для копирования, `--allow-opaque-legacy` только для осознанного
synthetic импорта старых бинарных dummy fixtures как octet-stream attachment.
Reconciliation: `python -m src.tools.storage_maintenance reconcile`, применение
`--apply` ставит сироты в durable deletion queue. Старые пути не выводятся в stdout;
private manifests — /app/media/temp/migration-manifests, сохранять вместе с media.
Rollback window 7 дней; перед удалением дубликатов проверяется новая hash-копия.
Admin purge удаляет и свои migration backups с учётом shared refs.
LEGACY_FILE_READS=0 включается после нулевого dry-run остатка. Не применять этот
локальный job к неизвестной/production БД; такой target отвергается guard.
