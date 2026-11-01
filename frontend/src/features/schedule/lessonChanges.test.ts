import { expect, it, vi } from 'vitest';
import {
  droppedHour,
  calendarHours,
  calendarSlotHeights,
  changeLesson,
} from './lessonChanges';
import type { Lesson } from '../courses/queries';
const { send } = vi.hoisted(() => ({ send: vi.fn() }));
vi.mock('../../shared/api/client', () => ({ request: send }));
it('accepts only whole hour slots in the agreed range, retaining Moscow offset', () => {
  expect(calendarHours).toHaveLength(14);
  expect(droppedHour('2026-10-29', 15)).toBe('2026-10-29T15:00:00+03:00');
  for (const hour of [7, 22, 15.25, NaN])
    expect(droppedHour('2026-10-29', hour)).toBeNull();
});
it('compresses only empty morning hours, with a full shared row for any lesson', () => {
  expect(calendarSlotHeights([])).toEqual([
    44,
    44,
    44,
    44,
    ...Array(10).fill(88),
  ]);
  expect(calendarSlotHeights([8, 11, 16])).toEqual([
    88,
    44,
    44,
    88,
    ...Array(10).fill(88),
  ]);
});
it('uses the acknowledged version when reversing a change and never retries', async () => {
  send.mockRejectedValueOnce(new Error('timeout'));
  await expect(
    changeLesson({ id: 9, updated_at: 'latest' } as Lesson, {
      scheduled_at: 'original',
    }),
  ).rejects.toThrow('timeout');
  expect(send).toHaveBeenCalledExactlyOnceWith('/lessons/9', {
    method: 'PATCH',
    body: { scheduled_at: 'original', expected_updated_at: 'latest' },
  });
});
