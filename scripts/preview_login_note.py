"""Private human-readable entrances, refreshed with every guarded synthetic seed."""
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


def write_login_note(credentials: dict[str, Any], path: Path = Path('frontend/.artifacts/t15b1-login.txt'), *, review_verified: bool = False) -> None:
    origin = 'http://127.0.0.1:5173'
    lines = [f'LGG · synthetic preview · {datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m.%Y %H:%M МСК")}',
             'Только синтетические данные. Media во временном OS каталоге; это не production persistence.',
             'Старые входы после fresh seed не использовать.', '',
             f'Преподаватель: {origin}/login?returnTo=/teacher/schedule']
    for key, label in [('teacher', 'Преподаватель'), ('read_student', 'Ученик: чтение'),
                       ('answer_student', 'Ученик: ответ'),
                       ('planning_teacher', 'T15b.3: преподаватель для парного сценария'),
                       ('planning_student', 'T15b.3: его ученик'), ('profile_student', 'Ученик: профиль'),
                       ('files_student', 'Ученик: файлы'), ('admin', 'Администратор: только вход, T15c ещё не реализована')]:
        account = credentials.get(key)
        if account and 'password' in account:
            lines += ['', label, f'Логин: {account["username"]}', f'Пароль: {account["password"]}']
    fixture = credentials.get('student_read', {})
    lesson = next((item for item in fixture.get('lessons', []) if not item['archive']), None)
    if lesson:
        lines += ['', 'Актуальные маршруты преподавателя:',
                  f'Ученик: {origin}/teacher/students/{lesson["student_user_id"]}',
                  f'Занятие с материалами: {origin}/teacher/lessons/{lesson["id"]}?student={lesson["student_user_id"]}',
                  f'Курс: {origin}/teacher/courses/{lesson["course_id"]}']
    lines += ['', 'T15b.2: Расписание → Добавить занятие → ученик/курс → еженедельно4 → предпросмотр → подтверждение.',
              'У занятия: Перенести; конспект PDF/фото; Выдать задание; Добавить долг; две независимые отметки «не нужно».',
              'Недельная норма: ученик → Настройки ученика → Недельная норма.',
              ('T15b.3: обе роли, оценки0/5, конфликт, unknown outcome, фото/PDF и mobile/keyboard проверены с реальным synthetic API.'
               if review_verified else 'T15b.3: текущий runtime gate требует проверки; наличие входов не подтверждает сквозной PASS.'),
              f'Очередь: {origin}/teacher/review · Обзор: {origin}/teacher',
              'T15b.4 реализована локально: цена ученика и итог недели со счётчиком; ручная приёмка ожидает.',
              'Приёмки владельца T15a.2/.3/T15b.1/T08b/T15b.2 и исторические NOT RUN остаются открыты.']
    pair = next((item for item in credentials.get('planning_read', {}).get('lessons', []) if not item['archive']), None)
    if pair:
        lines += ['', ('Парный сценарий T15b.3 (planning teacher/student выше; вход проверен):'
                      if review_verified else 'Парный сценарий T15b.3 (planning teacher/student выше; доступность требует проверки):'),
                  f'Учитель: {origin}/teacher/lessons/{pair["id"]}?student={pair["student_user_id"]}',
                  f'Ученик: {origin}/student/lessons/{pair["id"]}',
                  'Учитель выдаёт новое synthetic ДЗ; ученик открывает его и отправляет; учитель находит в очереди и проверяет; ученик перечитывает результат.']
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as out:
        os.fchmod(out.fileno(), 0o600)
        out.write('\n'.join(lines) + '\n')
