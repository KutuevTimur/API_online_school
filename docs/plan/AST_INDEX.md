# Локальная структурная навигация

По запросу владельца19.10.2026 установлен [AST Index](https://github.com/defendend/Claude-ast-index-search)
v3.56.0, официальный darwin-arm64 release. SHA256 архива:
`51f010c7a86f2049bd6347a0844ca6466c9b617e6962e2374f1f899e5cde23ba`.

Бинарник `.local-runtime/ast-index/ast-index` и SQLite cache рядом игнорируются
существующим `.gitignore`. Глобальная установка, Claude hooks и MCP не нужны.
Индекс локальный; `.ast-index.yaml` ограничивает его исходниками и тестами,
без окружения, credentials, media, node_modules и сгенерированных артефактов.

Из корня проекта:

```sh
./scripts/ast-index update
./scripts/ast-index symbol Lesson --in-file src/modules/lessons/models.py --limit 5
./scripts/ast-index outline src/modules/lessons/service.py
./scripts/ast-index refs Lesson --limit 10
./scripts/ast-index stats
```

После изменения конфигурации — `./scripts/ast-index rebuild`; после изменений кода
или ветки — `update`. При отсутствии бинарника скачать соответствующий официальный
release, сверить SHA256 с GitHub Release API, распаковать в указанный каталог.
На другом компьютере выбрать архив его ОС/архитектуры.

Для точных строк, документации, динамических связей и проверки полноты остаётся
`rg`. AST — навигация, не полная семантическая проверка; совпадения включают imports.
Компактные результаты уменьшают лишний контекст, но процент экономии на LGG
не измерялся; заявление автора40–50% не является нашим результатом.

Проверка19.10: version/stats, rebuild/update, поиск Python Lesson и TS Lesson,
outline/refs; индекс416 файлов,9791 символ,24700 ссылок. Код платформы и БД
не менялись; продуктовые тесты не запускались. Commit/push/deploy не выполнялись.


## Применение в T08b · 19.10.2026

Использованы update, outline lessons/service.py и test_t08b_regular.py,
symbol с --in-file для DTO/repository, refs RegularLessonSeries/lock_schedule.
Outline сервиса — 23 строки вместо 431 строки исходника: это размер навигационного
вывода, не измеренная экономия всех токенов сессии. По найденным границам читались
точные участки; SQL/миграционные fixtures/требования сверялись через rg и исходники.
Пустой symbol по имени файла test_maintenance_guard не нашёл ничего: имена файлов
не равны именам функций. Индекс не заменяет текстовый поиск, тесты и review.
Практическая польза — меньше лишнего чтения при возврате к задаче. На поведение
платформы, объём требований и обязательные проверки AST Index не влияет.
