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
docker compose --env-file .env -f docker-compose.yaml up -d --build
```

Проект `lgg-dev`: БД `lgg_dev`, роль `lgg_dev_app`, loopback порт 55431,
отдельные volumes `lgg-dev_postgres_data` и `lgg-dev_media`. Backend внутри сети
использует postgres:5432, API опубликован только на 127.0.0.1:8018. На хосте
конфиг использует 127.0.0.1:55431. Redis не обязателен и не подключается.
Dev build/start в T01 не запускался; схема ещё требует T02. У frontend пока
нет реализации. Изменение env-пароля не меняет пароль уже существующего volume.

Не применять `down -v` к чужим проектам. Внешняя БД остаётся UNKNOWN.
Commit/push/deploy выполняются только по отдельному поручению.
