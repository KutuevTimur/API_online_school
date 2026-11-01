import { it, expect } from 'vitest';
import { normalizeProfile, validateProfile, type PublicProfile } from './api';
it('normalizes public account IDs without mistaking internal profile keys for user IDs', () => {
  const profile = normalizeProfile({
    id: 71,
    username: 'synthetic',
    role: 'student',
    created_at: '2026-10-16',
    email: null,
    student: {
      user_id: 71,
      first_name: 'Тест',
      last_name: 'Ученик',
      middle_name: null,
      avatar_path: null,
      created_at: '2026-10-16',
      updated_at: '2026-10-16',
    },
  } satisfies PublicProfile);
  expect(profile.id).toBe(71);
  expect(profile.editable).toBe(true);
  expect(profile.email).toBeNull();
  const minimal = normalizeProfile({
    user_id: 82,
    username: 'readonly',
    first_name: 'Тест',
    last_name: 'Просмотр',
  });
  expect(minimal.id).toBe(82);
  expect(minimal.editable).toBe(false);
  expect(
    normalizeProfile({
      id: 1,
      role: 'admin',
      username: 'admin',
      created_at: '2026-10-16',
    }).editable,
  ).toBe(false);
});
it('allows absent optional names/email but requires a usable username and validates email', () => {
  expect(
    validateProfile({
      username: 'test',
      email: '',
      first_name: '',
      last_name: '',
      middle_name: '',
    }),
  ).toEqual({});
  expect(
    validateProfile({
      username: ' ',
      email: 'broken',
      first_name: '',
      last_name: '',
      middle_name: '',
    }),
  ).toHaveProperty('username');
  expect(
    validateProfile({
      username: 'test',
      email: 'broken',
      first_name: '',
      last_name: '',
      middle_name: '',
    }),
  ).toHaveProperty('email');
});
