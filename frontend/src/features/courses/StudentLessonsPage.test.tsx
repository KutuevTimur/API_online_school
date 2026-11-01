import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { StudentLessonsPage } from './StudentLessonsPage';
import {
  StudentHistoryReturn,
  studentHistoryOrigin,
} from './studentHistoryOrigin';
import { historyMonth, historyMonthWindow } from './studentHistoryDates';
import { moscow } from '../../shared/lib/datetime';

const { read, infinite, api, auth } = vi.hoisted(() => ({
  read: vi.fn(),
  infinite: vi.fn(),
  api: vi.fn(),
  auth: { user: { id: 31, role: 'student' } },
}));
vi.mock('./queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
vi.mock('@tanstack/react-query', async (original) => ({
  ...(await original<object>()),
  useInfiniteQuery: infinite,
}));
vi.mock('../../shared/api/client', async (original) => ({
  ...(await original<object>()),
  request: api,
}));
vi.mock('../auth/session', async (original) => ({
  ...(await original<object>()),
  useSession: () => auth,
}));
const course = {
  id: 18,
  name: 'Подготовка ЕГЭ',
  teacher_name: 'Анна Иванова',
  access_mode: 'active',
};
const lesson = (id = 9, overrides = {}) => ({
  id,
  title: `Занятие ${id}`,
  topic: `Тема ${id}`,
  course_id: 18,
  scheduled_at: '2026-09-30T20:59:59Z',
  status: 'completed',
  access_mode: 'active',
  is_deleted: false,
  ...overrides,
});
const success = (data: unknown) => ({
  data,
  isPending: false,
  isError: false,
  isFetching: false,
  refetch: vi.fn(),
});
beforeEach(() => {
  infinite.mockReset().mockReturnValue({
    ...success({ pages: [{ items: [course], total: 1 }] }),
    hasNextPage: false,
  });
  api.mockReset();
  read.mockReset().mockImplementation((path, params, enabled = true) => {
    if (!enabled) return { isPending: true };
    if (path.startsWith('/courses/')) return success(course);
    if (path === '/lessons')
      return success(
        params.limit === 1
          ? { items: [lesson(99)], total: 1 }
          : { items: [lesson()], total: 1 },
      );
    if (path === '/lectures') return success({ items: [], total: 0 });
    if (path === '/homeworks')
      return success([{ id: 42, title: 'Домашнее задание' }]);
    return success([]);
  });
  window.scrollTo = vi.fn();
});
function show(search = '?history-month=2026-09', state = {}) {
  const router = createMemoryRouter(
    [
      { path: '/student/materials', element: <StudentLessonsPage /> },
      { path: '/student/lessons/:id', element: <StudentHistoryReturn /> },
      { path: '/student/homeworks/:id', element: <StudentHistoryReturn /> },
    ],
    { initialEntries: [{ pathname: '/student/materials', search, state }] },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { router, user: userEvent.setup() };
}

it('uses bounded server lessons with completed latest by scheduled_at, never PDF creation or elapsed date', () => {
  show();
  expect(read).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({
      status: 'completed',
      sort_date: 'desc',
      limit: 1,
      offset: 0,
      view: 'all',
      course_id: 18,
    }),
  );
  const latestParams = read.mock.calls.find(
    ([path, p]) => path === '/lessons' && p.limit === 1,
  )![1];
  expect(latestParams).not.toHaveProperty('to_date');
  expect(read).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({
      from_date: '2026-08-31T21:00:00.000Z',
      to_date: '2026-09-30T20:59:59.999999Z',
      sort_date: 'desc',
      limit: 20,
      offset: 0,
      view: 'all',
    }),
  );
  expect(screen.getByText('Анна Иванова')).toBeVisible();
  expect(
    screen.queryByRole('combobox', { name: 'Курс' }),
  ).not.toBeInTheDocument();
  expect(
    read.mock.calls
      .filter(([path]) => path === '/lectures')
      .every(([, p]) => p.lesson_id === 99 && p.student_user_id === 31),
  ).toBe(true);
});

it('loads files only for latest and explicitly expanded row, carries full URL/scroll and restores explicit return', async () => {
  const search =
    '?course_id=18&history-month=2026-09&history-strip=2026-08&history-offset=20';
  const { router, user } = show(search);
  expect(
    read.mock.calls.some(
      ([path, p]) => path === '/lectures' && p.lesson_id === 9,
    ),
  ).toBe(false);
  await user.click(screen.getByRole('button', { name: /Тема 9/ }));
  expect(read).toHaveBeenCalledWith(
    '/lectures',
    { lesson_id: 9, student_user_id: 31, limit: 20, offset: 0 },
    true,
  );
  const expanded = router.state.location.search;
  Object.defineProperty(window, 'scrollY', { value: 432, configurable: true });
  await user.click(screen.getAllByRole('link', { name: 'Открыть занятие' })[1]);
  expect(router.state.location.state).toMatchObject({
    studentHistoryReturnTo: '/student/materials' + expanded,
    studentHistoryScroll: 432,
  });
  await user.click(screen.getByRole('link', { name: 'К моим занятиям' }));
  expect(router.state.location.search).toBe(expanded);
  expect(screen.getByRole('button', { name: /Тема 9/ })).toHaveAttribute(
    'aria-expanded',
    'true',
  );
  expect(window.scrollTo).toHaveBeenCalledWith(0, 432);
  await user.click(
    screen.getByRole('link', { name: 'Открыть домашнее задание' }),
  );
  expect(router.state.location.pathname).toBe('/student/homeworks/42');
  await router.navigate(-1);
  expect(router.state.location.search).toBe(expanded);
});

it('pages a >20 month on the server and resets disclosure on page/filter changes', async () => {
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lessons' && p.limit !== 1
      ? success({ items: [lesson()], total: 23 })
      : fallback(path, p, e),
  );
  const { router, user } = show('?history-month=2026-09&history-lesson=9');
  await user.click(
    within(
      screen.getByRole('navigation', { name: 'Страницы истории занятий' }),
    ).getByRole('button', { name: 'Далее' }),
  );
  expect(router.state.location.search).toContain('history-offset=20');
  expect(router.state.location.search).not.toContain('history-lesson');
  expect(read).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({ offset: 20, limit: 20 }),
  );
  await user.click(screen.getByRole('button', { name: 'август 2026' }));
  expect(router.state.location.search).toContain('history-offset=0');
});

it('keeps the selected month independent of strip arrows across December and January and Back', async () => {
  const { router, user } = show('?history-month=2026-12&history-strip=2026-12');
  await user.click(screen.getByRole('button', { name: 'Следующие месяцы' }));
  expect(router.state.location.search).toContain('history-month=2026-12');
  expect(router.state.location.search).toContain('history-strip=2027-05');
  await router.navigate(-1);
  await user.click(await screen.findByRole('button', { name: 'январь 2027' }));
  expect(router.state.location.search).toContain('history-strip=2026-12');
  expect(router.state.location.search).toContain('history-month=2027-01');
  expect(read).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({
      from_date: '2026-12-31T21:00:00.000Z',
      to_date: '2027-01-31T20:59:59.999999Z',
      sort_date: 'asc',
    }),
  );
});

it('splits current month with exact non-overlapping Moscow/UTC boundaries, retaining cancelled and archived labels', () => {
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lessons' && p.limit !== 1
      ? success({
          items: [
            lesson(9, {
              status: 'cancelled',
              is_deleted: true,
              access_mode: 'read_only',
            }),
            lesson(10, { status: 'scheduled' }),
          ],
          total: 2,
        })
      : fallback(path, p, e),
  );
  show();
  expect(screen.getByText('В архиве · Отменено')).toBeVisible();
  expect(screen.getByText('Запланировано')).toBeVisible();
  expect(historyMonthWindow('2024-02').to_date).toBe(
    '2024-02-29T20:59:59.999999Z',
  );
  expect(historyMonth('2026-13', '2026-10')).toBe('2026-10');
});

it('shows neutral loading/error and retry instead of claiming attachments are absent', async () => {
  const retry = vi.fn();
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lectures'
      ? {
          isPending: false,
          isError: true,
          error: new Error('network'),
          refetch: retry,
        }
      : fallback(path, p, e),
  );
  const { user } = show();
  expect(
    screen.queryByText('Конспект пока не добавлен.'),
  ).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /Повторить/ }));
  expect(retry).toHaveBeenCalledOnce();
});

it('has honest empty month and no completed lesson without falling back to scheduled', () => {
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lessons'
      ? success({ items: [], total: 0 })
      : fallback(path, p, e),
  );
  show('?history-month=2027-01');
  expect(screen.getByText('Проведённых занятий пока нет.')).toBeVisible();
  expect(screen.getByText(/Занятий в этом месяце пока нет/)).toBeVisible();
  expect(read.mock.calls.some(([path]) => path === '/lectures')).toBe(false);
});

it('rejects malformed/inaccessible course queries before lessons, with an explicit reset', async () => {
  const { router, user } = show(
    '?course_id=broken&history-offset=20&history-lesson=9',
  );
  expect(screen.getByRole('alert')).toHaveTextContent('Некорректный курс');
  expect(read.mock.calls.some(([path]) => path === '/lessons')).toBe(false);
  await user.click(screen.getByRole('button', { name: 'Все курсы' }));
  expect(router.state.location.search).not.toContain('course_id');
  expect(router.state.location.search).not.toContain('history-lesson');
});

it('paginates course metadata, labels multiple teachers and scopes selection', async () => {
  infinite.mockReturnValue({
    ...success({
      pages: [
        {
          items: [
            course,
            {
              ...course,
              id: 19,
              name: 'Русский',
              teacher_name: 'Борис Петров',
            },
          ],
          total: 21,
        },
      ],
    }),
    hasNextPage: true,
    fetchNextPage: vi.fn(),
  });
  const { router, user } = show();
  await user.click(screen.getByRole('combobox', { name: 'Курс' }));
  await user.keyboard('{ArrowDown}{Enter}');
  expect(router.state.location.search).toContain('course_id=18');
  expect(read).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({ course_id: 18, status: 'completed' }),
  );
  const options = infinite.mock.calls[0][0];
  await options.queryFn({ pageParam: 20 });
  expect(api).toHaveBeenCalledWith('/courses', {
    params: { view: 'all', limit: 20, offset: 20 },
    signal: undefined,
  });
});

it('accepts only a local history origin', () => {
  for (const value of [
    'https://example.com',
    '//example.com',
    '/student/materials/9',
    '/teacher/materials',
    '/student/materials?x=\\evil',
  ])
    expect(studentHistoryOrigin(value)).toBeUndefined();
  expect(studentHistoryOrigin('/student/materials?history-month=2026-09')).toBe(
    '/student/materials?history-month=2026-09',
  );
});

it('queries current month as two disjoint paginated server windows with upcoming ascending', () => {
  const before = Math.floor(Date.now() / 1000) * 1000;
  show('');
  const rawCalls = read.mock.calls.filter(
    ([path, p, e]) => path === '/lessons' && p.limit !== 1 && e !== false,
  );
  const calls = [
    ...new Map(rawCalls.map((c) => [JSON.stringify(c[1]), c])).values(),
  ];
  expect(calls).toHaveLength(2);
  const past = calls[0][1],
    next = calls[1][1];
  expect(past.from_date).toBe(
    historyMonthWindow(moscow().format('YYYY-MM')).from_date,
  );
  expect(next.to_date).toBe(
    historyMonthWindow(moscow().format('YYYY-MM')).to_date,
  );
  expect(past.sort_date).toBe('desc');
  expect(next.sort_date).toBe('asc');
  expect(Date.parse(past.to_date)).toBe(Date.parse(next.from_date) - 1);
  expect(Date.parse(next.from_date)).toBeGreaterThanOrEqual(before);
  expect(screen.getByRole('heading', { name: /^Предстоящие/ })).toBeVisible();
});

it('does not turn course loading/error into no courses or request any lessons', () => {
  infinite.mockReturnValue({ isPending: true });
  show();
  expect(screen.getByRole('status')).toHaveTextContent('Загружаем');
  expect(screen.queryByText('Курсов пока нет')).not.toBeInTheDocument();
  expect(read.mock.calls.some(([path]) => path === '/lessons')).toBe(false);
});

it('keeps inaccessible selected course as an error without falling back to all lessons', () => {
  read.mockReturnValue({
    isPending: false,
    isError: true,
    error: new Error('denied'),
    refetch: vi.fn(),
  });
  show('?course_id=999');
  expect(screen.getByRole('alert')).toBeVisible();
  expect(read.mock.calls.some(([path]) => path === '/lessons')).toBe(false);
  expect(screen.getByRole('button', { name: 'Все курсы' })).toBeVisible();
});

it('latest has concise material actions, keeps generic title out and sends homework to its exact route', async () => {
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lessons' && p.limit === 1
      ? success({
          items: [lesson(99, { title: 'Занятие', topic: null })],
          total: 1,
        })
      : path === '/lectures'
        ? success({
            items: [
              { file: { id: 11, display_name: 'Длинное_имя_конспекта.pdf' } },
            ],
            total: 1,
          })
        : fallback(path, p, e),
  );
  const { user, router } = show();
  const card = within(
    screen.getByRole('region', { name: 'Последнее проведённое занятие' }),
  );
  expect(card.queryByRole('heading', { level: 3 })).not.toBeInTheDocument();
  expect(card.getByRole('button', { name: 'Конспект' })).toBeVisible();
  expect(
    card.queryByRole('button', { name: /Длинное_имя/ }),
  ).not.toBeInTheDocument();
  expect(card.getByRole('link', { name: 'Открыть занятие' })).toHaveAttribute(
    'href',
    '/student/lessons/99',
  );
  await user.click(card.getByRole('link', { name: 'Д/з' }));
  expect(router.state.location.pathname).toBe('/student/homeworks/42');
  expect(router.state.location.state.studentHistoryReturnTo).toContain(
    'history-month=2026-09',
  );
});
it('latest lists every available lecture and homework only after explicit disclosure', async () => {
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lectures'
      ? success({
          items: [
            { file: { id: 11, display_name: 'Первый.pdf' } },
            { file: { id: 12, display_name: 'Второй.pdf' } },
          ],
          total: 2,
        })
      : path === '/homeworks'
        ? success([
            { id: 42, title: 'Первое задание' },
            { id: 43, title: 'Второе задание' },
          ])
        : fallback(path, p, e),
  );
  const { user, router } = show();
  const card = within(
    screen.getByRole('region', { name: 'Последнее проведённое занятие' }),
  );
  expect(
    card.queryByRole('button', { name: 'Открыть Первый.pdf' }),
  ).not.toBeInTheDocument();
  expect(
    card.queryByRole('link', { name: 'Второе задание' }),
  ).not.toBeInTheDocument();
  await user.click(card.getByRole('button', { name: 'Конспекты · 2' }));
  expect(
    card.getByRole('button', { name: 'Открыть Первый.pdf' }),
  ).toBeVisible();
  expect(
    card.getByRole('button', { name: 'Открыть Второй.pdf' }),
  ).toBeVisible();
  await user.click(card.getByRole('button', { name: 'Д/з · 2' }));
  await user.click(card.getByRole('link', { name: 'Второе задание' }));
  expect(router.state.location.pathname).toBe('/student/homeworks/43');
});

it('history groups keep exact totals, omit redundant full-page ranges and retain generic fallback only when needed', () => {
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lessons' && p.limit !== 1
      ? success({
          items: [lesson(9, { title: 'Занятие', topic: 'Параметры' })],
          total: 1,
        })
      : fallback(path, p, e),
  );
  show();
  const history = within(
    screen.getByRole('region', { name: 'История занятий' }),
  );
  expect(history.getByRole('heading', { name: 'Занятия · 1' })).toBeVisible();
  expect(history.queryByText(/Показано/)).not.toBeInTheDocument();
  expect(
    history.getByRole('button', { name: /Параметры.*Материалы/ }),
  ).toBeVisible();
  expect(
    history.queryByText('Занятие', { exact: true }),
  ).not.toBeInTheDocument();
  expect(history.getByRole('combobox', { name: 'Год' })).toHaveValue('2026');
  expect(history.getByRole('button', { name: 'Текущий месяц' })).toBeVisible();
});
it('history displays a range only for partial pages without dropping total count', () => {
  const fallback = read.getMockImplementation()!;
  read.mockImplementation((path, p, e) =>
    path === '/lessons' && p.limit !== 1
      ? success({ items: [lesson()], total: 23 })
      : fallback(path, p, e),
  );
  show();
  const history = within(
    screen.getByRole('region', { name: 'История занятий' }),
  );
  expect(history.getByRole('heading', { name: 'Занятия · 23' })).toBeVisible();
  expect(history.getByText('Показано 1–1')).toBeVisible();
});
