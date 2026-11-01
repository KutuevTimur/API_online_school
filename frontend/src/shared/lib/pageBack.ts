export type BackRole = 'student' | 'teacher';
export type BackEntry = { index: number; key: string; url: string };
export const backStorageKey = 'lgg.page-back.v1';

// Accept only local routes owned by the current role or shared account pages.
export function localBackUrl(value: unknown, role: BackRole) {
  if (
    typeof value !== 'string' ||
    !value.startsWith('/') ||
    /^\/\//.test(value) ||
    /[\\\r\n]/.test(value)
  )
    return undefined;
  const url = new URL(value, 'https://lgg.invalid');
  if (!(
    url.pathname === `/${role}` ||
    url.pathname.startsWith(`/${role}/`) ||
    ['/profile', '/notifications'].includes(url.pathname)
  ))
    return undefined;
  return url.pathname + url.search + url.hash;
}

export function parentBackUrl(
  path: string,
  role: BackRole,
  state: Record<string, unknown> = {},
) {
  if (/^\/teacher\/students\//.test(path)) {
    const params =
      typeof state.studentListSearch === 'string'
        ? new URLSearchParams(state.studentListSearch).toString()
        : '';
    return '/teacher/students' + (params ? `?${params}` : '');
  }
  if (/^\/teacher\/review\//.test(path)) return '/teacher/review';
  if (/^\/teacher\/lessons\//.test(path)) return '/teacher/schedule';
  if (/^\/teacher\/(courses|archive)\//.test(path)) return '/teacher/students';
  if (/^\/student\/homeworks\//.test(path)) return '/student/homeworks';
  if (/^\/student\/lessons\//.test(path)) return '/student/schedule';
  if (/^\/student\/courses\//.test(path)) return '/student/courses';
  return `/${role}`;
}

export function backPlan(
  role: BackRole,
  url: string,
  index: number | undefined,
  entries: BackEntry[],
  state: Record<string, unknown> = {},
) {
  const path = url.split(/[?#]/)[0];
  const previous =
    index === undefined
      ? undefined
      : entries
          .filter(
            (e) =>
              e.index < index &&
              localBackUrl(e.url, role) &&
              e.url.split(/[?#]/)[0] !== path,
          )
          .sort((a, b) => b.index - a.index)[0];
  if (previous) return { delta: index! - previous.index, to: previous.url };
  const origin = [state.studentHistoryReturnTo, state.returnTo]
    .map((value) => localBackUrl(value, role))
    .find((value) => value && value.split(/[?#]/)[0] !== path);
  return { to: origin || parentBackUrl(path, role, state), delta: undefined };
}

export function readBackEntries(
  storage: Pick<Storage, 'getItem'>,
  role: BackRole,
): BackEntry[] {
  try {
    const saved = JSON.parse(storage.getItem(backStorageKey) || 'null');
    if (saved?.role !== role || !Array.isArray(saved.entries)) return [];
    return saved.entries
      .filter(
        (e: BackEntry) =>
          e &&
          Number.isSafeInteger(e.index) &&
          e.index >= 0 &&
          typeof e.key === 'string' &&
          localBackUrl(e.url, role),
      )
      .slice(-80);
  } catch {
    return [];
  }
}
