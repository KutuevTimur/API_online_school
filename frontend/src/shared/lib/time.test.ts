import { expect, it } from 'vitest';
import { moscowToUtc, utcToMoscow } from './time';
it('roundtrips Moscow time independently of device zone', () => {
  expect(moscowToUtc('2026-10-16', '17:00')).toBe('2026-10-16T14:00:00.000Z');
  expect(utcToMoscow('2026-10-16T14:00:00Z')).toEqual({
    date: '2026-10-16',
    time: '17:00',
  });
});
it('rejects impossible date and malformed time', () => {
  expect(moscowToUtc('2026-02-31', '17:00')).toBeNull();
  expect(moscowToUtc('2026-10-16', '24:00')).toBeNull();
  expect(moscowToUtc('2026-10-16', '1:00')).toBeNull();
});
