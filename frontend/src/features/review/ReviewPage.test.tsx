import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { ReviewPage } from './ReviewPage';
const { read } = vi.hoisted(() => ({ read: vi.fn() }));
vi.mock('../courses/queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
vi.mock('./ReviewForm', () => ({ ReviewForm: () => <p>Форма проверки</p> }));
beforeEach(() => {
  read.mockImplementation((path) => ({
    isPending: false,
    data: path.startsWith('/homeworks/')
      ? {
          id: 5,
          title: 'Уравнения',
          course_name: 'Ева Елсукова',
          lesson_title: 'Практика',
          lesson_id: 7,
          student_user_id: 42,
          can_review: true,
          description: 'Короткое условие https://example.com/task',
        }
      : path.startsWith('/users/')
        ? {
            user_id: 42,
            first_name: 'Ева',
            last_name: 'Елсукова',
            school_grade: 7,
            username: 'eva',
          }
        : path.startsWith('/lessons/')
          ? { scheduled_at: '2026-10-22T14:00:00Z' }
          : { id: 12 },
  }));
});
it('leads with a single student identity, secondary title/date and expanded condition; keeps queue params', async () => {
  const router = createMemoryRouter(
    [{ path: '/teacher/review/:submissionId', element: <ReviewPage /> }],
    {
      initialEntries: [
        '/teacher/review/12?homework_id=5&limit=50&offset=20&course_id=7&condition-file=3',
      ],
    },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
    'Ева Елсукова · 7',
  );
  expect(screen.getAllByText('Ева Елсукова · 7 класс')).toHaveLength(1);
  expect(screen.queryByText('eva')).not.toBeInTheDocument();
  expect(screen.getByText(/22 октября, 17:00 МСК/)).toBeVisible();
  expect(screen.getByRole('link', { name: 'К занятию' })).toHaveAttribute(
    'href',
    '/teacher/lessons/7?student=42',
  );
  expect(screen.getByRole('link', { name: 'К очереди' })).toHaveAttribute(
    'href',
    '/teacher/review?limit=50&offset=20&course_id=7',
  );
  const condition = screen.getByText('Условие задания').closest('details')!;
  expect(condition.open).toBe(true);
  await userEvent.click(screen.getByText('Условие задания'));
  expect(condition.open).toBe(false);
  expect(screen.getByRole('heading', { level: 1 })).toBeVisible();
  expect(screen.getByText('Форма проверки')).toBeVisible();
});
