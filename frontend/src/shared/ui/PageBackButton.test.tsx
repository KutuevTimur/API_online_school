import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { DirtyFormGuard } from './DirtyFormGuard';
import { PageBackButton } from './PageBackButton';
beforeEach(() => {
  sessionStorage.clear();
  window.history.replaceState({}, '');
});
afterEach(() => vi.restoreAllMocks());
function show(dirty = false) {
  const router = createMemoryRouter(
    [
      {
        path: '/teacher/students/33',
        element: (
          <>
            <PageBackButton role="teacher" />
            <DirtyFormGuard dirty={dirty} />
            <h1>Ученик</h1>
          </>
        ),
      },
      { path: '/teacher/students', element: <h1>Ученики</h1> },
    ],
    { initialEntries: ['/teacher/students/33'] },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return router;
}
it('keeps its parent fallback usable when session storage is blocked', async () => {
  vi.spyOn(window, 'sessionStorage', 'get').mockImplementation(() => {
    throw Error('blocked');
  });
  const router = show();
  await userEvent.click(screen.getByRole('button', { name: 'Назад' }));
  expect(router.state.location.pathname).toBe('/teacher/students');
});
it('respects cancel and confirm for unsaved work', async () => {
  const router = show(true);
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: 'Назад' }));
  await waitFor(() =>
    expect(
      screen.getByRole('dialog', { name: 'Уйти без сохранения?' }),
    ).toBeVisible(),
  );
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(router.state.location.pathname).toBe('/teacher/students/33');
  await user.click(screen.getByRole('button', { name: 'Назад' }));
  await user.click(screen.getByRole('button', { name: 'Уйти без сохранения' }));
  expect(router.state.location.pathname).toBe('/teacher/students');
});
