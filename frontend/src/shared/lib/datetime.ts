import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import 'dayjs/locale/ru';
dayjs.extend(utc);
dayjs.extend(timezone);
export const moscow = (value?: string) =>
  dayjs(value).tz('Europe/Moscow').locale('ru');
export function dateLabel(value: string | null | undefined) {
  return value && dayjs(value).isValid()
    ? `${moscow(value).format('D MMMM, HH:mm')} МСК`
    : 'Дата не назначена';
}
export const deadlineLabel = (value?: string | null) =>
  value ? `До ${dateLabel(value)}` : 'До следующего занятия';
export function safeCallUrl(value?: string | null) {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
export function weekStart(value?: string | null) {
  const valid =
    value &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    dayjs(value).isValid() &&
    dayjs(value).format('YYYY-MM-DD') === value;
  const date = valid ? dayjs.tz(value, 'Europe/Moscow').locale('ru') : moscow();
  return date.startOf('day').subtract((date.day() + 6) % 7, 'day');
}
export const lessonStatus = (value: string) =>
  ({
    scheduled: 'Запланировано',
    completed: 'Завершено',
    cancelled: 'Отменено',
  })[value] || value;
export const readOnlyReason = (value?: string | null) =>
  ({
    course_archived: 'Курс в архиве',
    lesson_archived: 'Занятие в архиве',
    enrollment_ended: 'Участие в курсе завершено',
    access_expired: 'Срок доступа закончился',
    teacher_link_ended: 'Обучение у преподавателя завершено',
    history_only: 'Доступна история обучения',
    role_read_only: 'Доступно только чтение',
  })[value || ''] || 'Доступно только чтение';

// The API uses inclusive to_date with PostgreSQL microsecond precision.
export function weekWindow(value?: string | null) {
  const start = weekStart(value);
  return {
    from_date: start.toISOString(),
    to_date: start
      .add(7, 'day')
      .subtract(1, 'millisecond')
      .toISOString()
      .replace('.999Z', '.999999Z'),
  };
}
