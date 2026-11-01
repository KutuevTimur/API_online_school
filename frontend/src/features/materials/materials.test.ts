import { it, expect } from 'vitest';
import { dateBoundary } from './MaterialsPage';
it('uses Moscow dates and inclusive microsecond end bounds, rejects malformed URL dates', () => {
  expect(dateBoundary('2026-10-16')).toBe('2026-10-15T21:00:00.000Z');
  expect(dateBoundary('2026-10-16', true)).toBe('2026-10-16T20:59:59.999999Z');
  expect(dateBoundary('2026-02-31')).toBeUndefined();
  expect(dateBoundary(null)).toBeUndefined();
});
