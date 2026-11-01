# Повторная проверка кода и веток

> Историческое доказательство своего этапа. Актуальные требования — PRODUCT/DECISIONS,
> состояние — STATUS. Сохранённые failures/NOT RUN относятся к указанному снимку.

15.10.2026. Проверка чтением исходников и AST, без изменения кода, подключения к БД, запуска сервера и миграций.

## Ветки и происхождение

`git ls-remote origin refs/heads/dev refs/heads/main` выполнен успешно после сетевого ограничения песочницы. Удалённые SHA совпали с локальными:

| Ветка | SHA | Python-файлы | Определения тестов | Вывод |
|---|---|---:|---:|---|
| dev | 71fdcfaa2b14f00ca515d2d98529c9657eb36951 | 184 | 127 | Существующая предметная область, база дальнейшей работы |
| main | 86dd21cd99621976c428b55ab75a7c4c31e695a9 | 60 | 5 | Ранний шаблон, не выпуск текущего продукта |

AST всех Python-файлов обеих веток разобран без синтаксических ошибок. Это не запуск приложения и не прохождение тестов. Код main читался через `git show`, без переключения рабочей директории. Main auth service прочитан: login/текущий пользователь через UsersService и TokenService, учебной предметной области нет; initial migration создаёт users/refresh_tokens и имеет другой revision. В main `src/models/users/models.py` ссылается на `Websites`, отсутствующий в регистрации моделей; requirements пуст. Старый аудит подтверждал ошибку ORM запуском; в этой сессии повторно проверено статически. Переносить main поверх dev не нужно.

Origin — форк KutuevTimur, upstream — IvanShankin. Локальная `codex/course-access-and-deletion` указывает на тот же коммит dev. Начальный status: GPT.md, AGENTS.md, docs/ и гпт.md — untracked. Это существовавшие документы пользователя, не мусор для удаления. Коммитов и push в этой сессии нет.

## Сохраняем существующее

FastAPI, async SQLAlchemy/PostgreSQL, Pydantic DTO, Alembic, доменные modules, Depends, фабрики тестов, PathBuilder. Модели User/Teacher/Student, Course/StudentCourse, Lesson/LessonStudent, Lecture/Homework, HomeworkSubmission/File, RefreshToken дают достаточную основу. Не вводить другой backend, микросервисы, универсальный repository framework или переписывание всего auth ради стиля.

Зависимости зафиксированы requirements.txt: FastAPI 0.141.1, SQLAlchemy 2.0.51, Alembic 1.18.5, Pillow 12.3.0, pillow_heif 1.5.0. Dockerfile использует Python 3.13.7, старый локальный аудит — 3.14; унифицировать проверяемую версию, не обновлять весь стек автоматически. PostgreSQL в compose — 15. Redis встречается в конфиге, но прикладных вызовов в src не найдено.

## Подтверждённые текущим чтением проблемы

| ID | Факт и место | Следствие / задача |
|---|---|---|
| C01 | `check_permission/service.py:check_role_and_id` сразу разрешает любого teacher | Чужой профиль/пароль; T05–T06 |
| C02 | `courses/views.py:get_courses` допускает teacher-фильтр None; чтение курса не ограничено своим владельцем | Чужие курсы; T06 |
| C03 | `auth/views.py` использует UserDTO для регистрации и смены пароля; `users/models_dto.py` содержит hash | Утечка внутреннего поля; T03 |
| C04 | `refresh_tokens/repository.py:validate_refresh_token` фильтрует срок, но не revoked; token_service коммитит операции через разные вызовы | Повторная/конкурентная ротация; T04 |
| C05 | `auth/auth_service.py` не проверяет is_active; refresh тоже | Блокировка не действует; T03–T04 |
| C06 | `auth/token_service.py:decode_access_token` verify_exp без require_exp; int(sub) вне обработки TypeError/ValueError | Неполный JWT и 500; T03 |
| C07 | `users/models.py` только teacher/student; `/register_by_admin` — мастер-пароль; teacher выбирает роль | Нет admin и ограничений выдачи ролей; T05 |
| C08 | `d98c55d6402c_.py:76` autcrement; courses/student_courses имеют is_active вместо ORM soft-delete полей | Чистая миграция сломана; T02 |
| C09 | `lessons/repository.py` bulk delete; Lesson без is_deleted | Удаление зависимостей и архив не соответствуют требованиям; T07 |
| C10 | `courses/repository.py:get_courses_by_student_id` не исключает удалённое зачисление; доступ по LessonStudent отдельно от зачисления | Разные ответы на список/ID/файл; T06–T07 |
| C11 | `homework_submissions/service.py:240` удаляет старые файлы при обновлении; DRAFT получает submitted_at; timezone удаляется | Потери вложений, неверный lifecycle; T09–T10 |
| C12 | `homeworks/models.py:deadline` NOT NULL, значения задаются вручную контрактом | Не выражает неизвестное следующее занятие; T11 |
| C13 | `lessons/service.py:create_lesson` создаёт только Lesson, не участника | Для персонального курса нужна атомарная композиция; T08 |
| C14 | `handlers_files/handler_documents.py:save_document` читает весь upload; PDF копируется дважды, фото превращается в PDF | Лишний объём и неограниченные ресурсы; T12 |
| C15 | `converter_images.py` поддерживает HEIC и EXIF transpose; CompressionImages сжимает WebP, но отдельного безопасного конвейера ДЗ нет | Переиспользовать алгоритмы, не писать новый кодек; T12 |
| C16 | `tests/conftest.py` autouse очищает все учебные таблицы; MODE=TEST — единственная явная защита | Сначала T00–T01, потом любые DB-тесты |
| C17 | `api/app.py` создаёт config повторно, lifespan не dispose engine; compose reload, пароль-заглушка, порт БД, нет media volume у backend | T01, T17 |

Пути в таблице относительно `src/modules/`, кроме явно указанных. В старом аудите дополнительно описаны max+1 попытки, уникальность зачисления, пагинация total за концом, exception→500 и коллизии username/email; включены в T06/T09/T16. Эти проверки не объявлены повторно воспроизведёнными на PostgreSQL.

## Есть ли действующая БД

Проверено дерево проекта, включая скрытые имена конфигурации, исключая внутренности .git/.venv: `.env*`, SQL-дампы, `.dump`, SQLite/DB-файлы не найдены. Каталогов media нет. В tracked-файлах не обнаружена конфигурация внешнего production host; compose описывает локальную PostgreSQL. Docker CLI в текущем PATH отсутствует; контейнеры и volumes проверить через него нельзя. `.venv/bin/python` существует.

**Вывод: состояние внешней БД неизвестно.** Отсутствие файлов не доказывает отсутствие БД у друга или на Timeweb. Сервер, SSH-профили и личные облачные аккаунты не исследованы; адреса и доступ не предоставлены. Не сканировать чужие серверы. T00 может установить отдельную чистую тестовую БД без решения судьбы внешней. Обновление неизвестной БД и изменение её истории миграций запрещено до read-only inventory и проверенной резервной копии.

## Что не запускалось

Полный pytest, сборка Docker, миграции на PostgreSQL, E2E, конвертация изображений и нагрузка. Старые успешные `collect-only` и SQLite-проверки остаются результатами старого аудита, не результатами этой сессии. Наличие 127 тестов не свидетельствует об их соответствии новым требованиям.
