import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { StudentLessonsPage } from './StudentLessonsPage';

const { api } = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock('../../shared/api/client', async (original) => ({
  ...(await original<object>()),
  request: api,
}));
vi.mock('../auth/session', async (original) => ({
  ...(await original<object>()),
  useSession: () => ({ user: { id: 31, role: 'student' } }),
}));
const course = { id: 18, name: 'Алгебра', teacher_name: 'Анна Иванова' };
const lesson = (id: number) => ({
  id,
  course_id: 18,
  title: `Занятие ${id}`,
  topic: `Тема ${id}`,
  scheduled_at: '2026-09-10T15:00:00Z',
  status: 'completed',
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
beforeEach(() => {
  window.scrollTo = vi.fn();
  api.mockReset().mockImplementation(async (path, options) => {
    if (path === '/courses') return { items: [course], total: 1 };
    if (path === '/lessons')
      return options.params.status
        ? { items: [lesson(99)], total: 1 }
        : {
            items: Array.from(
              { length: Math.min(20, 23 - options.params.offset) },
              (_, i) => lesson(options.params.offset + i + 1),
            ),
            total: 23,
          };
    if (path === '/lectures') return { items: [], total: 0 };
    if (path === '/homeworks') return [];
    throw new Error('Unexpected test read');
  });
});
function show(state = {}) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  });
  const router = createMemoryRouter(
    [{ path: '/student/materials', element: <StudentLessonsPage /> }],
    {
      initialEntries: [
        {
          pathname: '/student/materials',
          search: '?history-month=2026-09',
          state,
        },
      ],
    },
  );
  const result = render(
    <Providers>
      <QueryClientProvider client={client}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </Providers>,
  );
  return { ...result, router, user: userEvent.setup() };
}

it('coordinates real query hooks: course loading gates lessons, page 2 is server read, only latest/expanded fetch materials', async () => {
  const courses = deferred<{ items: (typeof course)[]; total: number }>();
  const fallback = api.getMockImplementation()!;
  api.mockImplementation((path, options) =>
    path === '/courses' ? courses.promise : fallback(path, options),
  );
  const { user, router } = show();
  expect(screen.getByRole('status')).toHaveTextContent('Загружаем');
  expect(api.mock.calls.some(([path]) => path === '/lessons')).toBe(false);
  await act(async () => courses.resolve({ items: [course], total: 1 }));
  const rows = await screen.findByRole('list', {
    name: 'Занятия выбранного месяца',
  });
  expect(within(rows).getAllByRole('button')).toHaveLength(20);
  await waitFor(() =>
    expect(
      api.mock.calls.filter(([path]) => path === '/lectures'),
    ).toHaveLength(1),
  );
  expect(
    api.mock.calls.find(([path]) => path === '/lectures')![1].params,
  ).toMatchObject({ lesson_id: 99, student_user_id: 31 });
  await user.click(within(rows).getAllByRole('button')[0]);
  await waitFor(() =>
    expect(
      api.mock.calls.filter(([path]) => path === '/lectures'),
    ).toHaveLength(2),
  );
  expect(
    api.mock.calls
      .filter(([path]) => path === '/lectures')
      .map(([, o]) => o.params.lesson_id),
  ).toEqual([99, 1]);
  await user.click(
    within(
      screen.getByRole('navigation', { name: 'Страницы истории занятий' }),
    ).getByRole('button', { name: 'Далее' }),
  );
  await waitFor(() =>
    expect(
      within(
        screen.getByRole('list', { name: 'Занятия выбранного месяца' }),
      ).getAllByRole('button'),
    ).toHaveLength(3),
  );
  expect(router.state.location.search).toContain('history-offset=20');
  expect(api).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({
      params: expect.objectContaining({
        limit: 20,
        offset: 20,
        from_date: '2026-08-31T21:00:00.000Z',
        to_date: '2026-09-30T20:59:59.999999Z',
      }),
    }),
  );
});

it('waits for lazy attachments before restoring exact explicit-return scroll, and restores only once', async () => {
  const lectures = deferred<{ items: never[]; total: number }>();
  const fallback = api.getMockImplementation()!;
  api.mockImplementation((path, options) =>
    path === '/lectures' ? lectures.promise : fallback(path, options),
  );
  const { user, router } = show({ restoreHistoryScroll: 432 });
  await screen.findByRole('heading', { name: 'Тема 99' });
  await screen.findByRole('list', { name: 'Занятия выбранного месяца' });
  expect(window.scrollTo).not.toHaveBeenCalled();
  expect(
    screen.queryByText('Конспект пока не добавлен.'),
  ).not.toBeInTheDocument();
  await act(async () => lectures.resolve({ items: [], total: 0 }));
  await waitFor(() => expect(window.scrollTo).toHaveBeenCalledWith(0, 432));
  expect(router.state.location.state.restoreHistoryScroll).toBeUndefined();
  const count = vi.mocked(window.scrollTo).mock.calls.length;
  await user.click(screen.getByRole('button', { name: 'Следующие месяцы' }));
  expect(vi.mocked(window.scrollTo).mock.calls).toHaveLength(count);
});

it('keeps a single archived course clearly read-only without a redundant selector', async () => {
  const fallback = api.getMockImplementation()!;
  api.mockImplementation((path, options) =>
    path === '/courses'
      ? Promise.resolve({
          items: [
            {
              ...course,
              is_deleted: true,
              access_mode: 'read_only',
              read_only_reason: 'course_archived',
            },
          ],
          total: 1,
        })
      : fallback(path, options),
  );
  show();
  expect(
    await screen.findByText('Курс: Алгебра · Анна Иванова · Архив'),
  ).toBeVisible();
  expect(
    screen.queryByRole('combobox', { name: 'Курс' }),
  ).not.toBeInTheDocument();
  expect(screen.getByText(/Только просмотр: Курс в архиве/)).toBeVisible();
});
