import { describe, expect, it } from 'vitest';
import { cellBusy, overlaps, selectedPublished } from './AvailabilityEditor';
import type { Lesson } from '../courses/queries';
import type { Window, Booking } from './api';
const at = '2030-01-07T10:00:00+03:00';
describe('calendar availability constraints', () => {
  it('uses half-open intervals and preserves adjacent times', () => {
    expect(
      overlaps(
        at,
        '2030-01-07T10:55:00+03:00',
        '2030-01-07T10:55:00+03:00',
        '2030-01-07T11:50:00+03:00',
      ),
    ).toBe(false);
    expect(
      overlaps(
        at,
        '2030-01-07T10:55:00+03:00',
        '2030-01-07T10:54:00+03:00',
        '2030-01-07T11:49:00+03:00',
      ),
    ).toBe(true);
  });
  it('blocks partial overlaps with existing lessons without treating cancellation as busy', () => {
    const lesson = {
      scheduled_at: '2030-01-07T09:30:00+03:00',
      duration_minutes: 55,
      status: 'scheduled',
    } as Lesson;
    expect(cellBusy(at, [lesson], [])).toBe(true);
    expect(cellBusy(at, [{ ...lesson, status: 'cancelled' }], [])).toBe(false);
  });
  it('blocks provisional bookings and leaves materialized time to the actual Lesson', () => {
    const booking = {
      start_at: at,
      end_at: '2030-01-07T10:55:00+03:00',
      status: 'confirmed',
      lesson_id: null,
    } as Booking;
    expect(cellBusy(at, [], [booking])).toBe(true);
    expect(cellBusy(at, [], [{ ...booking, lesson_id: 7 }])).toBe(false);
    expect(cellBusy(at, [], [{ ...booking, status: 'cancelled' }])).toBe(false);
  });
});

it('deduplicates a non-hour window selected through two overlapping calendar cells', () => {
  const w = {
    window_id: 'one',
    start_at: '2030-01-07T10:30:00+03:00',
    end_at: '2030-01-07T11:25:00+03:00',
    status: 'published',
  } as Window;
  expect(
    selectedPublished(
      [w],
      new Set(['2030-01-07T10:00:00+03:00', '2030-01-07T11:00:00+03:00']),
    ),
  ).toEqual([w]);
  expect(
    selectedPublished([{ ...w, status: 'consumed' }], new Set([at])),
  ).toEqual([]);
});
