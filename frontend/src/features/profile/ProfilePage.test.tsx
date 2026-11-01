import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider, Link } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { ApiError } from '../../shared/api/error';
import { ProfilePage } from './ProfilePage';
const { read, request, expire } = vi.hoisted(() => ({
  read: vi.fn(),
  request: vi.fn(),
  expire: vi.fn(),
}));
vi.mock('../courses/queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
vi.mock('../../shared/api/client', () => ({ request, upload: vi.fn() }));
vi.mock('../auth/session', async (original) => {
  const actual = await original<typeof import('../auth/session')>();
  return {
    ...actual,
    session: { ...actual.session, cleanup: () => () => {}, expire },
    useSession: () => ({ user: { id: 7, role: 'teacher' }, status: 'ready' }),
  };
});
beforeEach(() => {
  request.mockReset();
  expire.mockReset();
  read.mockImplementation((path) => ({
    isPending: false,
    refetch: vi.fn().mockResolvedValue({}),
    data:
      path === '/users/me'
        ? { id: 7, role: 'teacher', username: 'teacher', email: null }
        : {
            id: 7,
            username: 'teacher',
            email: null,
            teacher: {
              first_name: 'Тимур',
              last_name: '',
              middle_name: '',
              avatar_path: null,
            },
          },
  }));
});
function show() {
  const router = createMemoryRouter(
    [
      {
        path: '/profile',
        element: (
          <>
            <Link to="/other">Уйти</Link>
            <ProfilePage />
          </>
        ),
      },
      { path: '/other', element: <p>Другая страница</p> },
    ],
    { initialEntries: ['/profile'] },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { user: userEvent.setup(), router };
}
it('keeps profile and collapsed password drafts through disclosures and cancelled route change', async () => {
  const { user, router } = show();
  expect(
    screen.getByRole('button', { name: 'Сохранить профиль' }),
  ).toBeDisabled();
  const first = screen.getByLabelText('Имя', { exact: true });
  await user.clear(first);
  await user.type(first, 'Новое имя');
  const summary = screen.getByText('Изменить пароль', { selector: 'summary' });
  await user.click(summary);
  const current = screen.getByLabelText('Текущий пароль', { exact: true });
  await user.type(current, 'old-password');
  await user.click(summary);
  await user.click(summary);
  expect(current).toHaveValue('old-password');
  await user.click(summary);
  await user.click(screen.getByRole('link', { name: 'Уйти' }));
  const dialog = await screen.findByRole('dialog');
  await user.click(within(dialog).getByRole('button', { name: 'Отмена' }));
  expect(router.state.location.pathname).toBe('/profile');
  expect(first).toHaveValue('Новое имя');
  await user.click(summary);
  expect(current).toHaveValue('old-password');
  expect(request).not.toHaveBeenCalled();
});
it('preserves validation/incorrect-current recovery and expires only after success', async () => {
  const { user } = show();
  await user.click(
    screen.getByText('Изменить пароль', { selector: 'summary' }),
  );
  const current = screen.getByLabelText('Текущий пароль', { exact: true });
  await user.type(current, 'old-password');
  await user.type(
    screen.getByLabelText('Новый пароль', { exact: true }),
    'new-password',
  );
  await user.type(screen.getByLabelText('Повторите новый пароль'), 'mismatch');
  const submit = screen.getByRole('button', {
    name: /^Изменить пароль$/,
  });
  await user.click(submit);
  expect(await screen.findAllByText('Пароли не совпадают')).not.toHaveLength(0);
  expect(request).not.toHaveBeenCalled();
  await user.clear(screen.getByLabelText('Повторите новый пароль'));
  await user.type(
    screen.getByLabelText('Повторите новый пароль'),
    'new-password',
  );
  request
    .mockRejectedValueOnce(new ApiError(401, 'Unauthorized'))
    .mockResolvedValueOnce({ id: 7 });
  await user.click(submit);
  expect(
    await screen.findByText('Пароль не изменён', { exact: true }),
  ).toBeVisible();
  expect(current).toHaveValue('old-password');
  expect(expire).not.toHaveBeenCalled();
  request.mockResolvedValueOnce({});
  await user.click(submit);
  await waitFor(() => expect(expire).toHaveBeenCalledTimes(1));
  expect(current).toHaveValue('');
  expect(request.mock.calls[0]).toMatchObject([
    '/auth/change_password/7',
    {
      method: 'POST',
      body: { current_password: 'old-password', new_password: 'new-password' },
    },
  ]);
});
