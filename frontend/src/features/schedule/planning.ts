import type { components } from '../../shared/api/schema';
import { request } from '../../shared/api/client';
import type { Lesson } from '../courses/queries';
export type PlanningStudent = components['schemas']['PlanningStudentDTO'];
export type Reminder = components['schemas']['RecipientReminderDTO'];
export type RegularOperation =
  components['schemas']['RegularOperationResponseDTO'];
export function previewRegularChange(
  lesson: Lesson,
  action: 'extend' | 'stop' | 'cancel_future',
  weeks?: number,
) {
  return request<RegularOperation>('/lessons/regular/previews', {
    method: 'POST',
    body: {
      operation_id: crypto.randomUUID(),
      action,
      series_id: lesson.regular_series_id,
      ...(action === 'extend' ? { weeks } : {}),
    },
  });
}
export function normLabel(s: PlanningStudent) {
  const word = (
    {
      one: 'занятие',
      few: 'занятия',
      many: 'занятий',
      other: 'занятия',
    } as Record<string, string>
  )[new Intl.PluralRules('ru-RU').select(s.scheduled_count)];
  return s.paused
    ? `${s.scheduled_count} ${word} · пауза без недобора`
    : s.target == null
      ? `${s.scheduled_count} ${word} · норма не задана`
      : `${s.scheduled_count} из ${s.target} за неделю`;
}
export const planningRefresh = {
  predicate: (q: { queryKey: readonly unknown[] }) =>
    q.queryKey[0] === 'student-read',
};
