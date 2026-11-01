import { expect, it } from 'vitest';
import { normLabel, type PlanningStudent } from './planning';
it('distinguishes an unset norm, a weekly target, and a pause without implying zero demand', () => {
  const student: PlanningStudent = {
    user_id: 1,
    first_name: 'Synthetic',
    last_name: 'Student',
    username: 'synthetic',
    scheduled_count: 1,
    target: null,
    paused: false,
    norm_revision: 0,
    missing_homework: 0,
    missing_lecture: 0,
  };
  expect(normLabel(student)).toBe('1 занятие · норма не задана');
  expect(normLabel({ ...student, target: 2 })).toBe('1 из 2 за неделю');
  expect(normLabel({ ...student, target: 2, paused: true })).toBe(
    '1 занятие · пауза без недобора',
  );
});
