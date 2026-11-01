import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { CourseHistory } from './CourseHistory';
const { read, pages } = vi.hoisted(() => ({
  read: vi.fn(),
  pages: {
    past: { items: [], total: 0 },
    future: { items: [], total: 0 },
    next: { items: [], total: 0 },
  },
}));
vi.mock('./queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
beforeEach(() => {
  pages.past = { items: [], total: 0 };
  pages.future = { items: [], total: 0 };
  pages.next = { items: [], total: 0 };
  read.mockReset().mockImplementation((path, params) => ({
    data:
      path === '/lessons'
        ? params.limit === 1
          ? pages.next
          : params.sort_date === 'asc'
            ? pages.future
            : pages.past
        : path === '/homeworks'
          ? []
          : { items: [], total: 0 },
    isPending: false,
  }));
});
function show(url = '/?history-offset=20&next-offset=40&next-limit=50') {
  const router = createMemoryRouter(
    [{ path: '/', element: <CourseHistory courseId={7} studentId="42" /> }],
    {
      initialEntries: [
        {
          pathname: '/',
          search: url.split('?')[1] ? '?' + url.split('?')[1] : '',
          state: { studentListSearch: 'limit=50&sort=recent' },
        },
      ],
    },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { router, user: userEvent.setup() };
}
it('uses complementary inclusive API ranges, server sort and independent pages', async () => {
  const { router, user } = show();
  const params = read.mock.calls
    .filter(([path]) => path === '/lessons')
    .map(([, p]) => p);
  const nearest = params.find((p) => p.limit === 1);
  const past = params.find((p) => p.sort_date === 'desc');
  const future = params.find((p) => p.limit === 50);
  expect(nearest).toMatchObject({
    course_id: 7,
    student_user_id: 42,
    status: 'scheduled',
    view: 'active',
    sort_date: 'asc',
    offset: 0,
  });
  expect(past).toMatchObject({
    course_id: 7,
    student_user_id: 42,
    view: 'all',
    limit: 20,
    offset: 20,
  });
  expect(future).toMatchObject({
    course_id: 7,
    student_user_id: 42,
    view: 'all',
    sort_date: 'asc',
    offset: 40,
    from_date: nearest.from_date,
  });
  expect(past.to_date).toMatch(/\.999999Z$/);
  expect(Date.parse(nearest.from_date) - Date.parse(past.to_date)).toBe(1);
  await user.click(
    within(
      screen.getByRole('navigation', { name: 'Страницы прошедших занятий' }),
    ).getByRole('button', { name: 'Назад' }),
  );
  expect(router.state.location.search).toContain('next-offset=40');
  expect(router.state.location.search).toContain('history-offset=0');
  expect(router.state.location.state).toEqual({
    studentListSearch: 'limit=50&sort=recent',
  });
  expect(read.mock.calls.at(-2)?.[1].to_date).toBe(past.to_date);
});
it('keeps empty recovery and archived/cancelled materials scoped to the recipient', async () => {
  const lesson = {
    id: 9,
    scheduled_at: '2026-10-01T10:00:00Z',
    title: 'Прежняя встреча',
    status: 'cancelled',
    is_deleted: true,
    recipient_materials: [
      { student_user_id: 99, needs_homework: true },
      { student_user_id: 42, needs_lecture: true },
    ],
  };
  Object.assign(pages.past, { items: [lesson], total: 1 });
  const { user } = show('/');
  expect(
    screen.getByRole('link', { name: 'Открыть расписание' }),
  ).toHaveAttribute('href', '/teacher/schedule');
  expect(screen.getByText('В архиве · Отменено')).toBeInTheDocument();
  expect(screen.queryByText('ДЗ не выдано')).not.toBeInTheDocument();
  expect(screen.getByText('Конспект не загружен')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Открыть материалы' }));
  expect(read).toHaveBeenCalledWith('/homeworks', {
    lesson_id: '9',
    student_user_id: '42',
  });
  expect(screen.getByRole('link', { name: /Прежняя встреча/ })).toHaveAttribute(
    'href',
    '/teacher/lessons/9?student=42',
  );
});
