import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { StudentHistory } from './StudentHistory';
import { historyMonth, historyMonthWindow } from './studentHistoryDates';

const { read } = vi.hoisted(() => ({ read: vi.fn() }));
vi.mock('./queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
beforeEach(() => {
  read.mockReset().mockImplementation((path, params) => ({
    data:
      path === '/lessons'
        ? {
            items:
              params.limit === 1
                ? []
                : [
                    {
                      id: 9,
                      title: 'Тема сентября',
                      topic: 'Точная тема',
                      scheduled_at: '2026-09-30T20:59:59Z',
                      status: 'cancelled',
                      is_deleted: true,
                      access_mode: 'read_only',
                    },
                  ],
            total: params.limit === 1 ? 0 : 53,
          }
        : path === '/homeworks'
          ? []
          : { items: [], total: 0 },
    isPending: false,
  }));
});
function show(
  search = '?history-month=2026-09&history-offset=20&next-offset=40',
) {
  const router = createMemoryRouter(
    [{ path: '/', element: <StudentHistory courseId={7} studentId="42" /> }],
    {
      initialEntries: [
        {
          pathname: '/',
          search,
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
it('uses exact Moscow month boundaries, including leap February and year rollover', () => {
  expect(historyMonthWindow('2024-02')).toEqual({
    from_date: '2024-01-31T21:00:00.000Z',
    to_date: '2024-02-29T20:59:59.999999Z',
  });
  expect(historyMonthWindow('2026-12')).toEqual({
    from_date: '2026-11-30T21:00:00.000Z',
    to_date: '2026-12-31T20:59:59.999999Z',
  });
  expect(historyMonth('2026-13', '2026-10')).toBe('2026-10');
});
it('filters the full month at the API before paging and preserves independent future state', async () => {
  const { router, user } = show();
  expect(read).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({
      course_id: 7,
      student_user_id: 42,
      from_date: '2026-08-31T21:00:00.000Z',
      to_date: '2026-09-30T20:59:59.999999Z',
      sort_date: 'desc',
      offset: 20,
      limit: 20,
      view: 'all',
    }),
    true,
  );
  expect(screen.getByText(/Занятий за выбранный месяц: 53/)).toHaveTextContent(
    'показано 21–21',
  );
  await user.click(
    within(
      screen.getByRole('navigation', { name: 'Страницы занятий месяца' }),
    ).getByRole('button', { name: 'Далее' }),
  );
  expect(router.state.location.search).toContain('history-offset=40');
  expect(router.state.location.search).toContain('next-offset=40');
  await user.click(screen.getByRole('button', { name: 'август 2026' }));
  expect(router.state.location.search).toContain('history-month=2026-08');
  expect(router.state.location.search).toContain('history-offset=0');
  expect(router.state.location.state).toEqual({
    studentListSearch: 'limit=50&sort=recent',
  });
});
it('restores row disclosure from the URL and links to the existing lesson with full return context', async () => {
  const { router, user } = show('?history-month=2026-09&history-lesson=9');
  expect(screen.getByRole('button', { name: /Тема сентября/ })).toHaveAttribute(
    'aria-expanded',
    'true',
  );
  expect(read).toHaveBeenCalledWith('/homeworks', {
    lesson_id: '9',
    student_user_id: '42',
  });
  const link = screen.getByRole('link', { name: 'Открыть занятие' });
  expect(link).toHaveAttribute('href', '/teacher/lessons/9?student=42');
  await user.click(screen.getByRole('button', { name: /Тема сентября/ }));
  expect(router.state.location.search).not.toContain('history-lesson');
  expect(router.state.location.search).toContain('history-month=2026-09');
});
it('does not request an inverted date range for a future month', () => {
  show('?history-month=9998-01');
  expect(screen.getByText(/Этот месяц ещё впереди/)).toBeVisible();
  expect(read).toHaveBeenCalledWith(
    '/lessons',
    expect.objectContaining({ from_date: '9997-12-31T21:00:00.000Z' }),
    false,
  );
});

it('keeps month positions on selection and pages the strip independently, including browser back', async () => {
  const { user, router } = show('?history-month=2026-10&history-offset=20');
  const strip = screen.getByRole('group', { name: 'Месяцы занятий' });
  const names = () =>
    within(strip)
      .getAllByRole('button')
      .map((b) => b.getAttribute('aria-label'));
  const initial = names();
  await user.click(
    within(strip).getByRole('button', { name: 'сентябрь 2026' }),
  );
  expect(names()).toEqual(initial);
  expect(
    within(strip).getByRole('button', { name: 'сентябрь 2026' }),
  ).toHaveAttribute('aria-pressed', 'true');
  expect(router.state.location.search).toContain('history-offset=0');
  await user.click(
    within(strip).getByRole('button', { name: 'Следующие месяцы' }),
  );
  expect(
    within(strip).getByRole('button', { name: 'январь 2027' }),
  ).toBeVisible();
  expect(router.state.location.search).toContain('history-month=2026-09');
  await user.click(
    within(strip).getByRole('button', { name: 'Предыдущие месяцы' }),
  );
  expect(names()).toEqual(initial);
  await router.navigate(-1);
  expect(
    await within(strip).findByRole('button', { name: 'январь 2027' }),
  ).toBeVisible();
});

it('keeps the strip inside supported years', async () => {
  const { user } = show('?history-month=1900-01');
  const strip = screen.getByRole('group', { name: 'Месяцы занятий' });
  expect(
    within(strip).getByRole('button', { name: 'Предыдущие месяцы' }),
  ).toBeDisabled();
  await user.click(within(strip).getByRole('button', { name: 'февраль 1900' }));
  expect(
    within(strip).getByRole('button', { name: 'январь 1900' }),
  ).toBeVisible();
});
