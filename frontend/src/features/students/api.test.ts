import { describe, it, expect } from 'vitest';
import { courseSlug, invitationURL, studentLabel } from './api';
describe('teacher invitation boundary', () => {
  it('builds a complete same-public-origin fragment link without API/query secrets', () => {
    expect(
      invitationURL(
        '/activate#token=synthetic_123',
        'https://school.example/path',
      ),
    ).toBe('https://school.example/activate#token=synthetic_123');
    for (const raw of [
      null,
      '',
      '//evil.test/activate#token=x',
      'https://evil.test/#token=x',
      '/activate?token=x',
      '/reset-password#token=x',
      '/activate#token=x&next=evil',
    ])
      expect(invitationURL(raw, 'https://school.example')).toBeNull();
    expect(
      invitationURL('/activate#token=x', 'ftp://school.example'),
    ).toBeNull();
  });
  it('creates nonempty editable slug candidates and avoids accidental duplicates', () => {
    const a = courseSlug('Алгебра для Synthetic');
    const b = courseSlug('Алгебра для Synthetic');
    expect(a).toMatch(/^алгебра-для-synthetic-[a-f0-9]{8}$/);
    expect(a).not.toBe(b);
    expect(courseSlug('!!!')).toMatch(/^course-/);
  });
});

it('renders a pupil identity with a bare grade and never invents a missing one', () => {
  expect(
    studentLabel({ first_name: 'Иван', last_name: 'Петров', school_grade: 10 }),
  ).toBe('Иван Петров · 10');
  expect(
    studentLabel({
      first_name: 'Иван',
      last_name: 'Петров',
      school_grade: null,
    }),
  ).toBe('Иван Петров');
});
