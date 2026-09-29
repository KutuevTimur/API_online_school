# Правила разработки и структура проекта 

Это проект онлайн-школы (только backend). Стек: **Python 3.12+ / 3.14, FastAPI, SQLAlchemy 2.0 (asyncpg), Pydantic v2, Alembic, Pytest (pytest-asyncio)**.

---

## 1. Архитектура и структура модулей

Код разделен на изолированные доменные модули в `src/modules`.  
Каждый модуль обязан следовать строгой структуре файлов:

| Файл | Назначение и ответственность |
| :--- | :--- |
| `models.py` | SQLAlchemy ORM модели таблицы |
| `models_dto.py` | Pydantic схемы (запросы, ответы, внутренние DTO) |
| `repository.py` | Слой доступа к данным (SQL-запросы через SQLAlchemy) |
| `service.py` | Бизнес-логика, транзакции (`commit`/`rollback`), вызов репозитория |
| `depends.py` | FastAPI Depends фабрики внедрения зависимостей |
| `views.py` | FastAPI роутеры эндпоинтов (`APIRouter`) |
| `exception.py` | Кастомные исключения доменной области |

Дополнительные слои:
- `src/core/` — Конфигурация (`config/`), подключение к БД (`database/`), DI-контейнер (`container.py`).
- `src/modules/base/` — Базовые классы: `BaseRepository`, `ORMDTO`, `ServiceException`, `RepositoryException`.
- `src/modules/api/` — Фабрика приложения `init_fastapi_app()` (`app.py`) и глобальные обработчики ошибок (`exception_handler.py`).

---

## 2. Правила написания слоев

### 2.1. ORM Модели (`models.py`)
- Наследуются от `Base` (из `src.core.database.database`).
- Использовать современный синтаксис SQLAlchemy 2.0: `Mapped[...] = mapped_column(...)`.
- Поля дат: `DateTime(timezone=True)` со значениями `server_default=func.now()`.
- Связи: `relationship("TargetModel", back_populates="...")`.
- **Обязательно**: зарегистрировать новую модель в `src/modules/db_models/__init__.py` и добавить имя её класса в `__all__`, чтобы Alembic мог подхватить изменения.

### 2.2. DTO и схемы Pydantic (`models_dto.py`)
- DTO, маппящиеся из ORM-моделей, наследуются от `ORMDTO` (из `src.modules.base.orm_dto`) или используют `model_config = ConfigDict(from_attributes=True)`.
- DTO для входных запросов наследуются от `BaseModel`.
- Именование: `<Entity>DTO` (полная модель), `<Action><Entity>RequestDTO` (входные данные), `<Entity>ResponseDTO` (ответ клиенту).
- Маппинг ORM -> DTO производить через `ModelDTO.model_validate(orm_obj)`.

### 2.3. Репозитории (`repository.py`)
- Наследуются от `BaseRepository` (из `src.modules.base.database_model`), в `__init__` вызывается `super().__init__(session=session, model=ModelClass)`.
- Содержат только методы формирования и исполнения запросов (`select`, `update`, `delete`, `self.add()`).
- Возвращают ORM-объекты, списки ORM-объектов или `None`.
- **Запрещено**: коммитить транзакции (`session.commit()`) внутри репозитория — это ответственность сервиса.
- Должно быть минимум бизнес логики, только запросы к БД. Основная логика будет в `service.py`.

### 2.4. Сервисы (`service.py`)
- Принимают зависимости (`repository`, `session_db: AsyncSession`, `config: Config`, `cr_context: CryptContext`) через `__init__`.
- Управляют транзакциями БД: `await self.session_db.commit()`, `await self.session_db.refresh(...)`, `await self.session_db.rollback()`.
- Возвращают Pydantic DTO (или `None`), преобразуя ORM-объекты через `.model_validate()`.
- При ошибках выбрасывают кастомные исключения профильного `exception.py` модуля или `ServiceException`.

### 2.5. Внедрение зависимостей (`depends.py`)
- Фабричные функции с префиксом `get_...`:
  - `get_<domain>_service(request: Request, session = Depends(get_db)) -> <Domain>Service`.
  - Зависимости пользователя/авторизации: `get_current_user(token = Depends(oauth2_scheme), ...) -> UserDTO`.
- Сборка графа зависимостей (ручное DI) происходит внутри этих фабричных функций. Экземпляры репозиториев и вложенных сервисов инициализируются напрямую и передаются в целевой сервис. Конфиг инжектится через `Depends(get_config)`.

### 2.6. Контроллеры и роутеры (`views.py`)
- Создавать `router = APIRouter(prefix="/<domain>")`.
- Все эндпоинты — `async def`. Внедрение сервисов строго через `Depends(get_<domain>_service)`.
- Обязательно указывать `response_model` и `status_code` в декораторах маршрутов.
- Внутри эндпоинтов нет прямой работы с базой или ORM — только вызовы методов сервиса.
- Внимательно следить за правами доступа к эндпойнту. Для ограничения прав использовать зависимости из `src/modules/check_permission/depends.py`.
- **Обязательно**: подключить созданный роутер в `src/modules/api/app.py` внутри функции `_include_routers()`.

### 2.7. Исключения (`exception.py` и `exception_handler.py`)
- Доменные исключения сервисов наследуются от `ServiceException`.
- Исключения БД/репозиториев наследуются от `RepositoryException`.
- При необходимости нового статус-кода — зарегистрировать `@app.exception_handler` в `src/modules/api/exception_handler.py`.

### 2.8. Работа с файлами (Медиа)
- Взаимодействие с медиафайлами и путями осуществляется строго через `PathsConfig` (доступен в `config.paths`). 
- Использование хардкода путей запрещено.
- Бизнес-логика обработки файлов (сжатие, конвертация изображений и документов) должна использовать инструменты из `src/modules/handlers_files`.

### 2.9. Миграции БД (Alembic)
- Регистрация моделей происходит в `src/modules/db_models/__init__.py`.
- Создание новой миграции выполняется командой: `alembic revision --autogenerate -m "описание_миграции"`.
- Применение миграций: `alembic upgrade head`.

### 2.10 Полечные файлы
- В `src/tools` находятся файлы для работы с БД: дроп схем, создание

---

## 3. Общий кодстайл и соглашения

1. **Типизация**: Строгая аннотация типов во всех аргументах и возвращаемых значениях (`def func(...) -> Type:`).
2. **Асинхронность**: Весь I/O код (БД, внешние вызовы, эндпоинты) строго `async/await`.
3. **Pydantic v2**: Использовать `model_validate()` вместо `from_orm()` и `model_dump()` вместо `dict()`.
4. **Конфигурация**: Настройки инициализируются в `src.core.config`, переменные окружения автоматически парсятся методом `build()`. В слоях доступа (например, сервисах) обращаться к ним нужно через внедренный объект `config: Config`.
5. **Пароли и токены**: Хеширование паролей через `CryptContext` (`passlib`), токены через `jose.jwt` с таймзоной `UTC` (`datetime.now(UTC)`).

---

## 4. Правила написания тестов (`tests/`)

- Фреймворк: `pytest`, `pytest-asyncio` (маркер `@pytest.mark.asyncio`).
- Структура тестов зеркалит модуль `src/modules` (в `tests/modules`):
  - `fixtures/models_dto.py` — DTO для генерации фикстур (`Create<Entity>FixtureDTO`) со всеми опциональными полями (`= None`).
  - `fixtures/factory.py` — функция создания сущности в БД `create_<entity>_factory(session_db, crypto_context, new_entity)`. Для незаданных полей генерируются случайные значения через `random_string()`.
  - `fixtures/fixtures.py` — pytest-фикстура фабрики `create_<entity>_fixture`, возвращающая замыкание-фабрику.
  - `test_views_<domain>.py` — тесты эндпоинтов с использованием `client_for_tests` (httpx AsyncClient).
- **Сравнение данных**: Для валидации ответов и ORM-моделей использовать `comparison_models(Expected, Actual, keys_not_checked=[...])` из `tests.helpers.functions`.
- **Изоляция**: Автоматическая очистка БД перед каждым тестом (`clearing_db` в `conftest.py`). При добавлении новых таблиц — добавлять их удаление в `clearing_db` в правильном порядке внешних ключей (FK).

## 5. Бизнес правила проекта

- Клиент не должен знать о существовании `teacher_id` и `student_id`, вместо этого он только имеет представление об `user_id`.
- Дополнительные бизнес-правила будут добавляться по мере развития проекта.
