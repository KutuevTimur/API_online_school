# Повторная приёмка T00–T07 перед T08

> Историческое доказательство своего этапа. Актуальные требования — PRODUCT/DECISIONS,
> состояние — STATUS. Сохранённые failures/NOT RUN относятся к указанному снимку.

15.10.2026. Поручение владельца: отдельное локальное dev-окружение, автоматические
тесты и реальные HTTP-сценарии; исправить дефекты; неизвестную БД не трогать.
Ветка `codex/t00-t01-environment`, HEAD `662a992`. Commit/push/merge/deploy нет.
T08 не реализовывался; D03 принят. Предыдущие локальные изменения сохранены.

## Изоляция и запуск

- До старта Compose подтвердил существующий `lgg-test-postgres-1` на 55432 и
  отсутствие контейнеров lgg-dev. Созданы новые `lgg-dev_postgres_data`,
  `lgg-dev_media`, сеть lgg-dev и контейнеры PostgreSQL/backend.
- Перед миграциями SQL внутри нового контейнера: база lgg_dev, 0 public tables;
  lgg_dev_app без SUPERUSER/CREATEDB/CREATEROLE. На хосте проверен точный контракт
  127.0.0.1:55431/lgg_dev/lgg_dev_app. `.env` использует MODE=LOCAL (dev path);
  HTTP runner запускается с явным MODE=DEV. Секреты не выводились.
- `docker compose --env-file .env -f docker-compose.yaml up -d --build`: PASS,
  backend Python 3.13.7, PostgreSQL 15. Миграции через
  `docker compose --env-file .env -f docker-compose.yaml exec -T backend alembic upgrade head`:
  PASS от пустой базы до 811d7911d0b4. README уточнён: при первом старте нужны
  миграции до входа; startup приложения сам схему не создаёт.
- Backend доступен только на `http://127.0.0.1:8018`, Swagger `/docs`.
  Приложение подключается к PostgreSQL внутри отдельной Compose-сети.
- Pytest использовал только guarded lgg-test 127.0.0.1:55432; destructive fixtures
  не запускались на dev. Внешние адреса БД/данные не исследовались и не затрагивались.

## Найдено и исправлено

1. `PATCH /courses/{id}` с `avatar_type=mathematics` возвращал 500:
   сервис присваивал `avatar_path` входной публичной DTO, где такого поля нет.
   Теперь очищаем avatar_path в словаре DB update. HTTP воспроизведение до правки:
   500; после правки: 200, выбран стандартный avatar, avatar_path=null.
2. Legacy PATCH с `is_deleted=true` возвращал 200 с deleted_at=null.
   Теперь записывает время архива, как DELETE. Тест проверяет непустую дату,
   стабильность при повторном DELETE, запрет teacher restore и admin restore.

Правки только в сервисе курсов и двух регрессионных тестах; новой миграции нет.
Добавлен `src/tools/smoke_t00_t07.py`: воспроизводимый HTTP runner с точным
локальным DB guard, уникальными synthetic именами и purge только ID своего
курса, созданного текущим запуском. Начальный admin создаётся через штатный
bootstrap service; остальные пользователи — HTTP register + consume invite.

## Выполненные проверки

| Проверка | Результат |
|---|---|
| Исходный полный `MODE=TEST .venv/bin/python -m pytest -q --tb=short` | 290 passed, 137.32s |
| `MODE=TEST .venv/bin/python -m pytest tests_unit -q` | 14 passed, 0.44s |
| `MODE=TEST .venv/bin/python -m pytest tests/migrations -q --tb=short` | 11 passed, 17.82s; финальный повтор после полного pytest: 11 passed, 16.82s |
| `MODE=TEST .venv/bin/alembic upgrade head` + `alembic check` | PASS, schema diff пустой |
| `MODE=TEST .venv/bin/python -m pytest tests/modules/auth/test_t07_lifecycle.py -q --tb=short` после правок | 26 passed, 26.46s |
| Итоговый полный pytest после правок | 292 passed, 142.58s (0 failed/0 skipped) |
| HTTP до дополнительных проверок PATCH/files | 56 запросов PASS |
| Итоговый `MODE=DEV .venv/bin/python -m src.tools.smoke_t00_t07` | 68 запросов PASS |
| Restart PostgreSQL/backend + `--verify-retained` | 3 HTTP-запроса PASS: login, курс, PDF с прежним SHA-256 |
| Swagger `/docs` и `/openapi.json` | 200 / 200 |
| Dev `alembic check` после restart | PASS, schema diff пустой |
| AST src + tests / git diff --check | 230 Python files PASS / PASS |

Полный pytest включает проверки конкурентной ротации/отзыва токенов, rollback,
cutoff/истории, object/file permissions, admin purge/retry, clean/prior-state и
round-trip миграций. HTTP runner отдельно идёт через реальный TCP/Uvicorn/Docker,
без DI overrides и подмены авторизации.

HTTP покрывает: создание двух teacher администратором и student преподавателем,
запрет входа pending, одноразовую активацию и запрет replay, username login,
refresh rotation/replay/revocation семейства, запрет создания teacher преподавателем,
создание курса и зачисление, скрытие чужих объектов и SQL-списки, второго teacher
для общего student без доступа к курсу первого, создание урока и отдельного
LessonStudent по текущему API, ДЗ, PNG → PDF, student download/direct-file denial,
архив/read-only/сохранение скачивания, запрет teacher restore, admin restore,
отдельный архив урока при восстановлении курса, оба исправления PATCH,
запрет teacher purge, неверное подтверждение, purge своей synthetic цепочки,
сохранность второго курса, logout/revoked refresh.

## Что не прошло при разработке проверки

- Первый Docker вызов в sandbox: permission denied на docker socket. Повтор
  с разрешённым доступом к локальному Docker прошёл; отказа auto-review не было.
- Первый guard проверки dev ожидал MODE=DEV; локальный файл имел MODE=LOCAL.
  Проверены явные имя/роль/host/port; это тот же выделенный dev target.
- Два первых HTTP runner запуска остановились на неверных ожиданиях runner:
  invitation replay возвращает 401, чужой объект — 404, как в текущем контракте.
  Ожидания исправлены после чтения exception/policy; защита приложения работала.
- Отдельный probe после HTTP 500 попытался переиспользовать закрытое соединение
  и получил RemoteProtocolError; второй probe новым соединением подтвердил
  дефект missing deleted_at. После исправлений полный HTTP runner зелёный.
- Оба подтверждённых дефекта приложения исправлены и покрыты regression tests.
  Непройденных итоговых HTTP-проверок нет.

## Состояние и пределы проверки

Оба dev контейнера оставлены запущенными, PostgreSQL healthy, head 811d7911d0b4.
В dev только искусственные записи текущей проверки; после прерванных запусков
остались synthetic аккаунты/курсы, схема не очищалась. Безвозвратно удалён только
курс, созданный текущим HTTP-прогоном. После финального purge failed cleanup=0;
в media остались только retained.png и retained.pdf второго synthetic курса.
После restart БД и файл сохранены. Файлы находятся в Docker volume lgg-dev_media;
способ просмотра/копирования/остановки без удаления описан в README.

Учётные данные — локальный ignored `.env.audit-access`, mode 0600; не добавлять
в Git и не пересылать в чат. В нём есть admin, два teacher, student и ID оставленного
курса последнего успешного прогона. Конкретные пароли/токены в отчёт не включены.

Финальный lgg-test после повторных migrations и upgrade: head 811d7911d0b4,
users=0, courses=0; schema diff пустой. Dev данные при этом сохранены.

Не проверялись и не объявляются готовыми: браузерный UI (frontend отсутствует),
T08 расписание/status/call links, T09–T13 lifecycle/дедлайны/полный storage pipeline,
SMTP, production bundle, нагрузка, внешний сервер/реальная БД и backup restore T18.
Новый интерактивный ввод CLI admin отдельно не повторялся: bootstrap проверен
автоматическими тестами и фактическим вызовом штатного service в dev.

## Необязательная ручная проверка владельцем

Автоматическая приёмка не требует ручного подтверждения для закрытия этой проверки.
Для знакомства с API открыть `http://127.0.0.1:8018/docs`. Учётные данные взять
локально из `.env.audit-access` в редакторе; не отправлять файл/пароли в чат.

1. Swagger Authorize: войти synthetic student по username/password.
2. GET `/users/me`: свой аккаунт, без password hash.
3. GET `/courses`: виден оставленный synthetic курс второго teacher.
4. GET `/lessons` с course_id из локального файла: виден урок Restart check.
5. GET `/lectures/my`: synthetic материал; download по его ID и своим lesson/user_id
   возвращает PDF. URL конкретного файла также сохранён в локальном файле.

Это API, пользовательского кабинета ещё нет. Следующий этап — T08 по отдельному
поручению; согласование D03 повторять не нужно.
