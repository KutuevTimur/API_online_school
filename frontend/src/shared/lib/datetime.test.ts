import { describe, expect, it } from 'vitest';
import {
  dateLabel,
  deadlineLabel,
  weekStart,
  weekWindow,
  safeCallUrl,
  lessonStatus,
  readOnlyReason,
} from './datetime';
import { readKey } from '../../features/courses/queries';
describe('student read contracts', () => {
  it('covers every microsecond of a Moscow week without including next Monday', () => {
    expect(weekWindow('2026-10-16')).toEqual({
      from_date: '2026-10-11T21:00:00.000Z',
      to_date: '2026-10-18T20:59:59.999999Z',
    });
  });
  it('does not invent a deadline or epoch for nullable dates', () => {
    expect(dateLabel(null)).toBe('Дата не назначена');
    expect(deadlineLabel(null)).toBe('До следующего занятия');
    expect(dateLabel('invalid')).toBe('Дата не назначена');
  });
  it('uses Moscow across UTC day and year boundaries', () => {
    expect(dateLabel('2026-12-31T22:30:00Z')).toBe('1 января, 01:30 МСК');
    expect(weekStart('2027-01-03').format('YYYY-MM-DD')).toBe('2026-12-28');
  });
  it('allows only explicit http or https calls', () => {
    for (const raw of [
      'javascript:alert(1)',
      '//example.test',
      'data:text/plain,test',
      'garbage',
    ])
      expect(safeCallUrl(raw)).toBeUndefined();
    expect(safeCallUrl('https://example.test/')).toBe('https://example.test/');
  });
  it('labels cancellation and archive separately', () => {
    expect(lessonStatus('cancelled')).toBe('Отменено');
    expect(readOnlyReason('enrollment_ended')).toBe(
      'Участие в курсе завершено',
    );
  });
  it('partitions query keys by route and all filters', () => {
    expect(readKey('/lessons', { view: 'active' })).not.toEqual(
      readKey('/lessons', { view: 'archive' }),
    );
    expect(readKey('/lectures', { student_user_id: 1 })).not.toEqual(
      readKey('/lectures', { student_user_id: 2 }),
    );
  });
});
