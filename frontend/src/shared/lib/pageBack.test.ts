import { expect, it } from 'vitest';
import {
  backPlan,
  localBackUrl,
  parentBackUrl,
  readBackEntries,
} from './pageBack';

it('rejects external, cross-role and malformed return routes', () => {
  for (const value of [
    '//evil.test',
    '/\\evil.test',
    '/teacher/students',
    'https://evil.test',
    '/login',
    null,
  ])
    expect(localBackUrl(value, 'student')).toBeUndefined();
  expect(
    localBackUrl(
      '/student/materials?history-month=2026-09&history-lesson=9',
      'student',
    ),
  ).toContain('history-month=2026-09');
});
it('skips same-page query changes while retaining native history distance', () => {
  const plan = backPlan('student', '/student/lessons/7?file=4', 5, [
    { index: 2, key: 'a', url: '/student/materials?history-month=2026-09' },
    { index: 3, key: 'b', url: '/student/lessons/7' },
    { index: 4, key: 'c', url: '/student/lessons/7?condition-file=4' },
  ]);
  expect(plan).toEqual({
    delta: 3,
    to: '/student/materials?history-month=2026-09',
  });
});
it('prefers actual previous page and ignores future entries after a browser Back', () => {
  expect(
    backPlan(
      'teacher',
      '/teacher/review/5',
      4,
      [
        { index: 3, key: 'a', url: '/teacher' },
        { index: 5, key: 'b', url: '/teacher/students' },
      ],
      { returnTo: '/teacher/review' },
    ),
  ).toEqual({ delta: 1, to: '/teacher' });
});
it('uses validated explicit origins after direct entry, and preserves student-list filters', () => {
  expect(
    backPlan('student', '/student/homeworks/7', undefined, [], {
      studentHistoryReturnTo: '/student/materials?history-month=2026-09',
    }).to,
  ).toContain('history-month=2026-09');
  expect(
    backPlan('teacher', '/teacher/students/3', 0, [], {
      returnTo: '//evil.test',
      studentListSearch: 'q=Иван&school_grade=7',
    }).to,
  ).toBe('/teacher/students?q=%D0%98%D0%B2%D0%B0%D0%BD&school_grade=7');
});
it('has predictable direct-link parents for both roles', () => {
  expect(parentBackUrl('/teacher/review/5', 'teacher')).toBe('/teacher/review');
  expect(parentBackUrl('/student/lessons/5', 'student')).toBe(
    '/student/schedule',
  );
  expect(parentBackUrl('/student/homeworks/5', 'student')).toBe(
    '/student/homeworks',
  );
  expect(parentBackUrl('/profile', 'teacher')).toBe('/teacher');
});
it('ignores unavailable, corrupt and wrong-role storage', () => {
  expect(
    readBackEntries(
      {
        getItem: () => {
          throw Error('blocked');
        },
      },
      'teacher',
    ),
  ).toEqual([]);
  expect(readBackEntries({ getItem: () => '{broken' }, 'teacher')).toEqual([]);
  expect(
    readBackEntries(
      {
        getItem: () =>
          JSON.stringify({
            role: 'student',
            entries: [{ index: 1, key: 'a', url: '/student' }],
          }),
      },
      'teacher',
    ),
  ).toEqual([]);
});
