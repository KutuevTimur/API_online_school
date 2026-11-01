import { request } from '../../shared/api/client';
import type { Lesson } from '../courses/queries';
import type { components } from '../../shared/api/schema';

type Change = Omit<
  components['schemas']['UpdateLessonRequestDTO'],
  'expected_updated_at'
>;

// All entry points use the same versioned mutation; never retry a timed-out write.
export function changeLesson(lesson: Lesson, change: Change) {
  return request<Lesson>(`/lessons/${lesson.id}`, {
    method: 'PATCH',
    body: { ...change, expected_updated_at: lesson.updated_at },
  });
}

export const calendarHours = Array.from(
  { length: 14 },
  (_, i) => `${String(i + 8).padStart(2, '0')}:00`,
);
// A morning row is shared by all seven days: any visible lesson keeps it full.
export function calendarSlotHeights(hours: Iterable<number>) {
  const occupied = new Set(hours);
  return Array.from({ length: 14 }, (_, i) =>
    i + 8 < 12 && !occupied.has(i + 8) ? 44 : 88,
  );
}
export function droppedHour(date: string, hour: number) {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
    !Number.isInteger(hour) ||
    hour < 8 ||
    hour > 21
  )
    return null;
  return `${date}T${String(hour).padStart(2, '0')}:00:00+03:00`;
}
