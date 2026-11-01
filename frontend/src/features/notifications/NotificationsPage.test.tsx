import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { NotificationsPage } from './NotificationsPage';
const { read, request } = vi.hoisted(() => ({
  read: vi.fn(),
  request: vi.fn(),
}));
vi.mock('./api', async (original) => ({
  ...(await original<object>()),
  useNotices: read,
}));
vi.mock('../../shared/api/client', () => ({ request }));
vi.mock('../auth/session', async (original) => ({
  ...(await original<object>()),
  useSession: () => ({ user: { id: 7, role: 'teacher' }, status: 'ready' }),
}));
beforeEach(() => {
  request.mockReset();
  read.mockReturnValue({
    isPending: false,
    data: {
      items: [
        {
          id: 9,
          event_type: 'solution_submitted',
          created_at: '2026-10-22T12:00:00Z',
          read_at: null,
        },
        {
          id: 10,
          event_type: 'lesson_cancelled',
          created_at: '2026-10-21T12:00:00Z',
          read_at: '2026-10-22T12:00:00Z',
        },
      ],
      total: 2,
    },
  });
});
function show() {
  const router = createMemoryRouter(
    [
      { path: '/notifications', element: <NotificationsPage /> },
      { path: '/teacher/review/:id', element: <p>Проверка</p> },
    ],
    { initialEntries: ['/notifications?limit=50&offset=20'] },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { router, user: userEvent.setup() };
}
it('never reads/preloads targets on render/filter; opens with read then authorized target', async () => {
  const { user, router } = show();
  expect(screen.getByText('Новое · не прочитано')).toBeVisible();
  expect(screen.getByText('Прочитано', { exact: true })).toBeVisible();
  await user.click(screen.getByRole('checkbox'));
  expect(router.state.location.search).toContain('offset=0');
  expect(request).not.toHaveBeenCalled();
  let release!: () => void;
  request.mockImplementationOnce(
    () =>
      new Promise<void>((resolve) => {
        release = resolve;
      }),
  );
  request.mockResolvedValueOnce({
    available: true,
    object_type: 'submission',
    object_id: 12,
    homework_id: 5,
  });
  await user.click(
    within(screen.getAllByRole('article')[0]).getByRole('button'),
  );
  expect(request).toHaveBeenCalledTimes(1);
  expect(
    within(screen.getAllByRole('article')[1]).getByRole('button'),
  ).toBeDisabled();
  release();
  await waitFor(() =>
    expect(router.state.location.pathname).toBe('/teacher/review/12'),
  );
  expect(router.state.location.search).toBe('?homework_id=5');
  expect(request.mock.calls.map(([path]) => path)).toEqual([
    '/notifications/9/read',
    '/notifications/9/target',
  ]);
  expect(request.mock.calls[0][1].method).toBe('PATCH');
});
it('keeps unavailable and failed opens recoverable in the list', async () => {
  const { user, router } = show();
  request
    .mockResolvedValueOnce(undefined)
    .mockResolvedValueOnce({ available: false });
  const button = within(screen.getAllByRole('article')[0]).getByRole('button');
  await user.click(button);
  expect(await screen.findByText(/Материал больше недоступен/)).toBeVisible();
  expect(router.state.location.pathname).toBe('/notifications');
  request.mockRejectedValueOnce(new Error('offline'));
  await user.click(button);
  expect(
    await screen.findByText(
      'Не удалось открыть уведомление. Повторите попытку.',
    ),
  ).toBeVisible();
  expect(request).toHaveBeenCalledTimes(3);
  expect(button).toBeEnabled();
});
