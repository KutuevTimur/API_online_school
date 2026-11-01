import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import type { Answer } from '../../shared/api/files';
import { ReviewForm } from './ReviewForm';
import { ApiError } from '../../shared/api/error';
const { check, read } = vi.hoisted(() => ({ check: vi.fn(), read: vi.fn() }));
vi.mock('./api', () => ({ reviewAPI: () => ({ check, read }) }));
const answer = {
  id: 12,
  homework_id: 5,
  version: 3,
  status: 'submitted',
  text_content: 'Строка 1\nСтрока 2',
  files: [],
  grade: null,
} as unknown as Answer;
function show(initial = answer, canReview = true) {
  const router = createMemoryRouter([
    {
      path: '/',
      element: (
        <ReviewForm
          initial={initial}
          student="Synthetic Student"
          title="Уравнение"
          canReview={canReview}
        />
      ),
    },
  ]);
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
}
it('requires explicit grade, then confirms 0 with identity and immutability before sending', async () => {
  check.mockResolvedValue({ ...answer, status: 'checked', grade: 0 });
  show();
  const user = userEvent.setup();
  const submit = screen.getByRole('button', {
    name: 'Завершить проверку',
  });
  expect(
    screen.getAllByRole('radio').every((r) => !(r as HTMLInputElement).checked),
  ).toBe(true);
  await user.click(submit);
  expect(screen.getByText('Выберите оценку от 0 до 5')).toBeInTheDocument();
  expect(screen.getByRole('radio', { name: '0' })).toHaveFocus();
  expect(check).not.toHaveBeenCalled();
  await user.keyboard(' ');
  await user.click(submit);
  const dialog = await screen.findByRole('dialog', {
    name: 'Завершить проверку?',
  });
  expect(
    within(dialog).getByText('Synthetic Student · Уравнение'),
  ).toBeInTheDocument();
  expect(within(dialog).getByText('Оценка: 0 из 5.')).toBeInTheDocument();
  expect(
    within(dialog).getByText(/Оценку и комментарий изменить нельзя/),
  ).toBeInTheDocument();
  expect(check).not.toHaveBeenCalled();
  await user.click(
    within(dialog).getByRole('button', {
      name: 'Завершить проверку',
    }),
  );
  await waitFor(() => expect(check).toHaveBeenCalledWith(3, 0, ''));
  expect(
    await screen.findByText('Проверено · Оценка: 0 из 5'),
  ).toBeInTheDocument();
  expect(screen.queryByRole('radio')).not.toBeInTheDocument();
});
it('checked result shows server 0 and comment with no editable controls', () => {
  show(
    {
      ...answer,
      status: 'checked',
      grade: 0,
      teacher_comment: 'Проверь знаки',
    },
    false,
  );
  expect(screen.getByText('Проверено · Оценка: 0 из 5')).toBeInTheDocument();
  expect(screen.getByText('Проверь знаки')).toBeInTheDocument();
  expect(screen.queryByRole('radio')).not.toBeInTheDocument();
  expect(
    screen.queryByLabelText('Комментарий ученику'),
  ).not.toBeInTheDocument();
});

it.each([409, 422, 503])(
  'retains grade, comment and selected File after %s; cancel never sends',
  async (status) => {
    check
      .mockReset()
      .mockRejectedValue(new ApiError(status, 'Ошибка проверки'));
    read.mockReset().mockResolvedValue({
      ...answer,
      version: 4,
      text_content: 'Обновлённое решение',
    });
    show();
    const user = userEvent.setup();
    const file = new File(['pdf'], 'feedback.pdf', { type: 'application/pdf' });
    await user.click(screen.getByRole('radio', { name: '0' }));
    await user.type(
      screen.getByLabelText('Комментарий ученику'),
      'Сохранённый комментарий',
    );
    await user.upload(screen.getByLabelText('Добавить файлы к проверке'), file);
    const submit = screen.getByRole('button', { name: 'Завершить проверку' });
    await user.click(submit);
    let dialog = await screen.findByRole('dialog', {
      name: 'Завершить проверку?',
    });
    await user.click(within(dialog).getByRole('button', { name: 'Отмена' }));
    expect(check).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
    );
    await user.click(submit);
    dialog = await screen.findByRole('dialog', { name: 'Завершить проверку?' });
    await user.click(
      within(dialog).getByRole('button', { name: 'Завершить проверку' }),
    );
    await waitFor(() =>
      expect(check).toHaveBeenCalledWith(3, 0, 'Сохранённый комментарий', [
        file,
      ]),
    );
    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
    );
    expect(screen.getByRole('radio', { name: '0' })).toBeChecked();
    expect(screen.getByLabelText('Комментарий ученику')).toHaveValue(
      'Сохранённый комментарий',
    );
    expect(screen.getByText('feedback.pdf')).toBeVisible();
    if (status !== 422) {
      await user.click(
        screen.getByRole('button', { name: 'Проверить результат на сервере' }),
      );
      await screen.findByText('Обновлённое решение');
      await user.click(
        screen.getByRole('button', { name: 'Открыть обновлённый ответ' }),
      );
      expect(screen.getByText('feedback.pdf')).toBeVisible();
      expect(screen.getByRole('radio', { name: '0' })).toBeChecked();
      expect(screen.getByLabelText('Комментарий ученику')).toHaveValue(
        'Сохранённый комментарий',
      );
      expect(check).toHaveBeenCalledTimes(1);
    }
  },
);
