import type { Answer } from '../api/files';

// Presentation only: an id=0 placeholder is never a persisted draft.
export function studentAnswerState(
  answer?: Answer | null,
  { dirty = false, uncertain = false, readOnly = false } = {},
) {
  if (readOnly) return 'readonly';
  if (uncertain) return 'unknown';
  if (!answer?.id) return dirty ? 'local' : 'empty';
  if (answer.status === 'checked') return 'checked';
  if (answer.status === 'submitted') return 'submitted';
  if (answer.status === 'draft') return 'draft';
  return 'unknown';
}
export type StudentAnswerState = ReturnType<typeof studentAnswerState>;
export const studentAnswerLabels: Record<StudentAnswerState, string> = {
  empty: 'Решение ещё не отправлено',
  local: 'Локальное решение · не сохранено',
  draft: 'Черновик сохранён · не отправлен',
  submitted: 'На проверке',
  checked: 'Проверено',
  unknown: 'Состояние решения не подтверждено',
  readonly: 'Только просмотр',
};
