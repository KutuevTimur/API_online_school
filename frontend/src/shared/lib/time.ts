import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
dayjs.extend(utc);
dayjs.extend(timezone);
export function moscowToUtc(date: string, time: string): string | null {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
    !/^([01]\d|2[0-3]):[0-5]\d$/.test(time)
  )
    return null;
  const value = dayjs.tz(`${date} ${time}`, 'Europe/Moscow');
  return value.isValid() &&
    value.format('YYYY-MM-DD HH:mm') === `${date} ${time}`
    ? value.toISOString()
    : null;
}
export function utcToMoscow(value: string) {
  const date = dayjs(value).tz('Europe/Moscow');
  return { date: date.format('YYYY-MM-DD'), time: date.format('HH:mm') };
}
