import { describe, it, expect, vi, afterEach } from 'vitest';
import { safeReturn, session } from './session';
afterEach(() => vi.unstubAllGlobals());
describe('session boundaries', () => {
  const user = { id: 1, username: 'synthetic', role: 'student' as const };
  it('rejects open redirects and foreign roles', () => {
    for (const path of [
      '//evil.test',
      'https://evil.test',
      '/teacher/schedule',
      '/student/../admin',
      '/student%2fadmin',
      '/student?token=x',
    ])
      expect(safeReturn(path, user)).toBe('/student');
    expect(safeReturn('/student/courses/123', user)).toBe(
      '/student/courses/123',
    );
  });
  it('does not rotate without Web Locks', async () => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    await expect(session.refresh()).rejects.toThrow('современном браузере');
    expect(fetch).not.toHaveBeenCalled();
  });
});

it('serializes cookie mutations, single flight, and scopes cleanup by identity', async () => {
  vi.stubGlobal('navigator', {
    locks: { request: vi.fn(async (_name, fn) => fn()) },
  });
  let id = 11;
  let rotations = 0;
  const fetch = vi.fn(async (path: string) => {
    if (path.endsWith('/refresh')) rotations++;
    return new Response(
      JSON.stringify(
        path === '/api/users/me'
          ? { id, username: 'synthetic', role: 'student' }
          : { access_token: 'memory-only-synthetic', token_type: 'bearer' },
      ),
    );
  });
  vi.stubGlobal('fetch', fetch);
  const clean = vi.fn();
  const unsubscribe = session.cleanup(clean);
  await session.login('synthetic', 'synthetic-password');
  await Promise.all([session.refresh(), session.refresh(), session.refresh()]);
  expect(rotations).toBe(1);
  session.expire();
  await session.login('synthetic', 'synthetic-password');
  expect(clean).not.toHaveBeenCalled();
  id = 12;
  await session.login('other-synthetic', 'synthetic-password');
  expect(clean).toHaveBeenCalledTimes(1);
  expect(localStorage.getItem('access_token')).toBeNull();
  await session.logout();
  expect(session.accessToken()).toBeUndefined();
  expect(clean).toHaveBeenCalledTimes(2);
  unsubscribe();
});
