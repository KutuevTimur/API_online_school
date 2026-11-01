# Browser E2E: проверять fixture до запуска

## S2 · read-only история ученика ·23.10.2026

`student-history-s2.spec.ts`: сохранённый `.artifacts/t15d-preview.json`,
`accounts.turov`; не требует builder/seed/reset. Нормальные login/refresh разрешены,
остальные non-GET запросы блокируются и проверяются. Первый тест — реальные
student API и protected PDF,1340/768/360/keyboard/Back/scroll/geometry/axe.
Второй — явно **HTTP fixtures**, а не real API PASS:0/1/23, paging, статусы/архив,
два курса/преподавателя, Select popup,503/retry. Исходные учебные данные не меняет.
До запуска проверить наличие fixture без вывода значений, readiness5173/8019,
Chrome и прежний media root по ENVIRONMENT; resume без seed.
Команда из корня с локальным Node24 в PATH:
`LGG_T15D_PREVIEW=1 LGG_CHROMIUM='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e -- e2e/student-history-s2.spec.ts --workers=1`.
В этой сессии **NOT RUN**: sandbox запретил bind обоим сервисам (EPERM).
Spec подготовлен и просмотрен, но его assertions ещё не подтверждены выполнением.
Teacher browser regression при shared navigation change остаётся обязательной;
компонентная проверка teacher navigation её не заменяет.

## Общие ограничения остальных suites

Текущий факт — [STATUS](../../docs/plan/STATUS.md). Preview содержит сохраняемые
данные. Общий `npm run test:e2e` **не является read-only smoke**: auth consumes
invite/reset, учебные suites создают/меняют ответы, файлы, уроки и профиль.

`review.spec.ts` требует planning pair из `.artifacts/t14e-credentials.json`;
`ui21-learning.spec.ts` — отдельный `.artifacts/ui21-credentials.json` и живые
объекты именно этой fixture. Наличие JSON не доказывает существование аккаунтов.
После очистки UX21 fixtures их нельзя повторно использовать без подготовки.
Изменения UI21 также требуют сверки старых label/draft/picker ожиданий.

Перед полным запуском прочитать выбранные spec, проверить accounts/объекты и guard,
обеспечить отдельный synthetic namespace/media и сохранность owner данных.
DB pytest и E2E не запускать одновременно. Не fresh seed/reset текущего preview.
[Правила продолжения](../../docs/plan/ENVIRONMENT.md#сохранение-текущего-preview).

Использовать уже установленный Chrome, без downloads:

```sh
LGG_CHROMIUM='/absolute/path/to/installed/chromium' npm run test:e2e
```

Эта команда — только после подготовки fixture. Приватные credentials0600/ignored,
traces/video/скриншоты секретов отключены. Chromium project не проверяет WebKit
или Firefox; их matrix остаётся T16/NOT RUN до фактического запуска. Старые PASS
не переносятся на изменённый UI и не закрывают ручные приёмки.

На 21.10.2026 общий последовательный прогон 47 тестов упирается в настоящий
15-минутный лимит входа (10/account, 100/IP). `auth.spec.ts` дополнительно тратит
одноразовые invite/reset-ссылки, поэтому его нельзя повторить с тем же JSON.
Проверенная схема для **отдельной одноразовой synthetic DB**: сначала свежая
fixture и auth, затем запуск spec-файлов по одному с очисткой только тестовых
счётчиков `auth_rate_limits` между группами и новым guard перед DB-действием.
Нельзя очищать лимиты, заново seed-ить или расходовать токены в сохраняемом
preview владельца. Фактические результаты и пределы — [T15b](../../docs/plan/tasks/T15b.md).

Storage UI (22.10): `storage.spec.ts` проверяет teacher course usage/student quota,
потребляет ignored `.artifacts/storage-credentials.json`. Создание fixture —
`MODE=TEST PYTHONPATH=. .venv/bin/python frontend/e2e/fixtures/storage-fixture.py`
из repo root **только на отдельной пустой guarded disposable DB** с остановленным
сохраняемым preview, после readiness/upgrade/preflight. На текущем preview не
запускать: тест делает synthetic uploads/archive и меняет quota своего test pupil.
Fixture отказывает на непустой DB или существующем credentials файле; credentials
не перезаписывать и не копировать в логи. Backend/media root берётся из fixture;
не использовать source resume против disposable media. После тестов вернуть
source container/media/helper и проверить сохранность по ENVIRONMENT.
