import { render, screen, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { AppShell, roleNavigation, type Role } from './AppShell';
beforeEach(() => {
  window.scrollTo = vi.fn();
});
vi.mock('../../features/notifications/NotificationCount', () => ({
  NotificationCount: () => null,
}));
function show(role: Role, pathname: string, state = {}) {
  const router = createMemoryRouter(
    [
      {
        path: '*',
        element: (
          <AppShell role={role}>
            <h1>Кабинет</h1>
          </AppShell>
        ),
      },
    ],
    { initialEntries: [{ pathname, state }] },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
}
it('makes student history a primary mobile entry and keeps courses secondary', () => {
  show('student', '/student/materials');
  const main = within(
    screen.getByRole('navigation', { name: 'Основные разделы' }),
  );
  expect(main.getByRole('link', { name: 'Занятия' })).toHaveAttribute(
    'aria-current',
    'page',
  );
  expect(main.getByRole('link', { name: 'Курсы' })).toHaveAttribute(
    'href',
    '/student/courses',
  );
  const mobile = within(
    screen.getByRole('navigation', { name: 'Разделы на телефоне' }),
  );
  expect(mobile.getByRole('link', { name: 'Занятия' })).toHaveAttribute(
    'href',
    '/student/materials',
  );
  expect(mobile.queryByRole('link', { name: 'Курсы' })).not.toBeInTheDocument();
});
it('keeps history active through its lesson/homework origin', () => {
  show('student', '/student/lessons/9', {
    studentHistoryReturnTo: '/student/materials?history-month=2026-09',
  });
  const main = within(
    screen.getByRole('navigation', { name: 'Основные разделы' }),
  );
  expect(main.getByRole('link', { name: 'Занятия' })).toHaveAttribute(
    'aria-current',
    'location',
  );
  expect(main.getByRole('link', { name: 'Расписание' })).not.toHaveAttribute(
    'aria-current',
  );
});
it('preserves teacher lesson ownership and all teacher navigation links', () => {
  show('teacher', '/teacher/lessons/9');
  const main = within(
    screen.getByRole('navigation', { name: 'Основные разделы' }),
  );
  expect(
    main
      .getAllByRole('link')
      .map((a) => [a.textContent, a.getAttribute('href')]),
  ).toEqual([
    ['Мой день', '/teacher'],
    ['Ученики', '/teacher/students'],
    ['Расписание', '/teacher/schedule'],
    ['На проверку', '/teacher/review'],
  ]);
  expect(main.getByRole('link', { name: 'Расписание' })).toHaveAttribute(
    'aria-current',
    'location',
  );
});
it('keeps teacher mobile routes separate from student navigation', () => {
  show('teacher', '/teacher');
  const nav = within(
    screen.getByRole('navigation', { name: 'Разделы на телефоне' }),
  );
  expect(
    nav
      .getAllByRole('link')
      .map((a) => [a.textContent, a.getAttribute('href')]),
  ).toEqual([
    ['Мой день', '/teacher'],
    ['Расписание', '/teacher/schedule'],
    ['Проверка', '/teacher/review'],
  ]);
  expect(document.querySelectorAll('a[href^="/student"]')).toHaveLength(0);
  expect(
    within(screen.getByRole('banner')).getByRole('link', {
      name: 'Уведомления',
    }),
  ).toHaveAttribute('href', '/notifications');
  // Native popup focus, More routing and Back are covered by teacher-shell E2E.
});

it('puts schedule in the student bottom bar and keeps homework under More with its active state', () => {
  show('student', '/student/homeworks/63');
  const nav = within(
    screen.getByRole('navigation', { name: 'Разделы на телефоне' }),
  );
  expect(nav.getAllByRole('link').map((a) => a.textContent)).toEqual([
    'Мой день',
    'Занятия',
    'Расписание',
  ]);
  expect(nav.getByRole('link', { name: 'Расписание' })).toHaveAttribute(
    'href',
    '/student/schedule',
  );
  expect(nav.queryByRole('link', { name: 'Д/з' })).not.toBeInTheDocument();
  const more = nav.getByRole('button', { name: 'Ещё' });
  expect(more).toHaveAttribute('data-active', 'true');
  expect(roleNavigation.student).toContainEqual(['Д/з', '/student/homeworks']);
});
