# Передача: улучшение расписания преподавателя ·28.10.2026

## Новое разрешение владельца и реализация28.10
После макета владелец уточнил HH:00 snap, отдельный `⋯`, прямой переход карточки,
подтверждения и запрет переполнения; затем явно поручил менять рабочий продукт,
самостоятельно тестировать и показать готовый результат. Предыдущий режим
«только исследование» ниже — история входа, больше не текущий запрет реализации.
Локальная реализация/проверки — [T15d](T15d.md#teacher-schedule--рабочая-реализация28102026).
Все остальные ограничения прежние: сохранённые данные/ДЗ58/Git/установки/VK/
старые приёмки не затрагивать. Source не отправлен в GitHub.

## Исследование28.10 — обсуждение продолжается, без реализации
- Внутренний root/ветка/SHA совпали с передачей; dirty/untracked сохранены без
  stash/reset/stage. AST update: 506 файлов, изменений нет; symbol/outline/refs
  подтвердили существующих владельцев календаря, форм, серии и shared controls.
- Прочитаны контекст/PRODUCT§5/D11/D12/A12/A13/DESIGN и relevant T08b/T15b;
  применены frontend-design + premium1.4.0 + Impeccable context/shape.
  Impeccable не обнаруживает PRODUCT в docs/plan: использован существующий путь,
  новый PRODUCT/интервью общего продукта не создавались.
- Настоящий IAB teacher preview: desktop наблюдаемый viewport1353×909,
  сетка начинается≈482px, scrollHeight≈2895px при clientHeight679px;
  первые карточки155–208px. Часовая строка растёт от самой высокой карточки;
  время повторяется в каждом дне, длительность не задаёт геометрию события.
- Narrow наблюдаемый viewport433×938: сетка≈591px от верха, первая карточка≈674px,
  четыре карточки выбранного дня по226px. Это browser responsive observation,
  не physical-device/точный390px PASS; временный viewport затем сброшен.
- Открыты и закрыты без сохранения: create, regular checkbox/default4weeks,
  перенос и локальное «было→станет», cancel confirmation, управление серией.
  POST regular preview/confirm и учебные mutations не выполнялись; ДЗ58 не открывали.
- Подтверждение cancel смешивает отмену с текстом про архив. В календаре нет
  исключения cancelled; public DELETE архивирует, отдельного restore/Undo API нет.
  PATCH времени/статуса проверяет expected_updated_at; перенос/отмена пересчитывают
  placements и создают уведомления. Regular receipt/revision защищают повтор confirm,
  но не являются журналом Undo; cancel_future не останавливает продление серии.
- **Ответ владельца:** отменённое занятие убрать из обычной сетки сразу, историю
  и материалы сохранить; дополнительный шаг архивирования для скрытия не нужен.
- Предложение пока не согласовано: компактная неделя ПК с постоянной шкалой минут,
  общими часами слева, короткими карточками и панелью действий по нажатию;
  mobile — компактный день и те же действия. Drag использует existing move contract,
  Esc отменяет жест, перед записью видно старое/новое время. Надёжное серверное Undo,
  его срок/уведомления и поведение серии требуют следующих небольших раундов.
- Исследование не является функциональной приёмкой: новые DB tests/fixtures/gates
  не запускались, backend/frontend исходники не менялись; S2/S3/S4 остатки прежние.

## Режим следующей сессии
Сначала read-only исследование, интервью и один конкретный вариант. Этот handoff
не разрешает реализацию, commit/push/PR/merge/deploy/установки зависимостей либо
изменение Codex config. Разрешение на реализацию согласованного объёма получить
из нового запроса владельца. Будущую VK-интеграцию сейчас не реализовывать.

## Вход в контекст
1. Внутренний API_online_school: AGENTS.md, GPT.md, docs/plan/README.md,
   STATUS.md; проверить Git root/branch/SHA/status, сохранить весь dirty/untracked.
   Внешняя папка тоже Git. Не stash/reset/delete, не создавать gitlink.
2. docs/plan/tasks/T15d.md — актуальные разделы последних student правок и
   «Пожелания владельца к следующему расписанию»; исторические логи не читать целиком.
3. rules_project.md до кода; DESIGN.md — принятый визуал и последние уточнения;
   PRODUCT §5, DECISIONS D11/D12, ARCHITECTURE A12/A13 и schedule contracts.
   Relevant tasks/T08b.md, T15b.md (.2/.4) по существующим scheduling/series/finance.
4. При UI исследовании/правках обязательные frontend-design + premium1.4.0,
   Impeccable по AGENTS; canonical components и existing owner map.
5. AST Index update → symbol/outline/refs. Старт: TeacherSchedulePage,
   LessonEditor, RegularDialog, TeacherToday, WeeklyNeeds, WeeklyEarnings,
   OverlapWarnings/planning, shared WeekNavigation/DateTimeField/ConfirmDialog.
   Пути: frontend/src/features/schedule/TeacherSchedulePage.tsx,
   teacherCalendar.module.css; e2e/teacher-calendar.spec.ts и existing scoped tests.
   Проверить актуальные реализации/refs, не повторять уже имеющиеся возможности.

## Что хочет владелец
- Больше занятий видно сразу, меньше вертикального шума. Удобно desktop/mobile.
- По нажатию занятия — понятные действия: открыть, перенести, отменить;
  отмена с подтверждением. Не копировать существующие операции в отдельную логику.
- Перетаскивание на время с ясной обратной связью; управление без drag тоже нужно.
- Возможность отменить ошибочное действие и понять, что изменилось.
- Позже отдельное планирование VK-бота: запись ученика → занятие в платформе.

До кода уточнить: desktop/week vs mobile/day, размеры временных слотов/видимый
диапазон, поля компактной карточки, click vs drag, повторяющееся занятие или серия,
пересечения и ограничения времени, что означает Undo и как долго доступен,
какие изменения и уведомления должны сохраняться в истории. Изучить server
version/idempotency/series receipts/audit перед предложением backend изменений.
Задавать вопросы небольшими порциями и объяснять варианты простыми словами.
Предложить одну рекомендуемую композицию/сценарий, согласовать, затем реализация.

## Принятый вид и прежние результаты
Владельцу нравится общий текущий визуал; student latest блок и явная голубая
«Открыть занятие» приняты, их не перерабатывать. DESIGN фиксирует вкус:
компактные white cards, короткие semantic actions/Lucide, ясный основной переход,
заметный hover, ровные кнопки; targets≥44, читаемый текст важнее экономии строки.
Последняя student mobile шапка белая48px с border1; bottom49 + safe inset.
Эта правка role-scoped: teacher/admin не менялись. Не выдавать student geometry
за состояние teacher shell. S2/S3/S4 остаются с прежними открытыми приёмками,
S3 VERIFY до отдельного подтверждения; S5/S6/T16 не начинались.

Последняя проверка: unit198/36 (--maxWorkers=2), types/lint/format/API types/tokens/
build PASS; build прежний chunk>500KB warning. Impeccable0, Premium strict FAIL2
старых detector findings TeacherLessonPage151/TeacherMaterials311. Мобильный
Chrome360/388/768 real read-only5.1s + HTTP unread fixtures3.3s PASS отдельно.
Артефакты frontend/.artifacts/header-white49-*. Full platform regression, physical
phones/Safari/Firefox/full200% NOT RUN. Проверенные независимые группы без причины
не повторять. 28.10 handoff: diff check PASS; настоящий teacher/schedule в IAB
загрузил текущую неделю, занятия, недельные итоги. Это read-only smoke, не новая
полная функциональная приёмка scheduler.

## Preview и безопасность данных
http://127.0.0.1:5173/teacher/schedule; backend8019, retained media root/DB.
Входы приватные frontend/.artifacts/t15d-login.txt/t15d-preview.json; не печатать.
Есть разрешение на read-only вход существующими student/teacher аккаунтами.
Не отправлять ответы/оценки и не менять реальные занятия ради проверки.
ДЗ58 не открывать/не отправлять/не проверять/не редактировать/не восстанавливать.
Никаких seed/reset/очисток/миграций/DB-тестов на preview. Отсутствующие состояния —
явно подписанные HTTP fixtures, не real API PASS. Не предполагать старые counts.
Не объявлять preview остановленным по sandbox HTTP000; сначала browser/listeners.
При необходимости existing ignored t15b2-resume.py с прежним media root без seed.

Внутренний Git: codex/t00-t01-environment, HEAD95b3560bdb429a06e7e5567a78ed6ef589886e4a
на момент передачи, большой local diff сохранён; код ещё не отправлен в GitHub.
В конце будущей реализации обновить карточку/STATUS/SESSION_LOG: команды,
PASS/FAIL/NOT RUN, реальные API vs fixtures, ограничения и owner acceptance.
