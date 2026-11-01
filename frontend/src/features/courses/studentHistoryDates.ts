import { moscow } from '../../shared/lib/datetime';

export function historyMonth(value: string | null, fallback: string) {
  return value &&
    /^\d{4}-(0[1-9]|1[0-2])$/.test(value) &&
    Number(value.slice(0, 4)) >= 1900 &&
    Number(value.slice(0, 4)) <= 9998
    ? value
    : fallback;
}

// API ranges are inclusive; don't include the next month's Moscow midnight.
export function historyMonthWindow(month: string) {
  const start = moscow(`${month}-01T00:00:00+03:00`);
  return {
    from_date: start.toISOString(),
    to_date: start
      .add(1, 'month')
      .subtract(1, 'millisecond')
      .toISOString()
      .replace('.999Z', '.999999Z'),
  };
}
