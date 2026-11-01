import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { LessonEditor } from './LessonEditor';
import type { Lesson } from '../courses/queries';
const { saveRequest } = vi.hoisted(() => ({ saveRequest: vi.fn() }));
vi.mock('../../shared/api/client', async (original) => ({
  ...(await original<object>()),
  request: saveRequest,
}));
vi.mock('../courses/queries', async (original) => ({
  ...(await original<object>()),
  useRead: () => ({ data: { items: [], total: 0 }, isPending: false }),
}));
// Real form/fields/route guard; native modal focus is covered by E2E.
vi.mock('../../shared/ui/ConfirmDialog', () => ({
  ConfirmDialog: ({
    opened,
    title,
    children,
    onCancel,
    onConfirm,
    confirmLabel,
  }: {
    opened: boolean;
    title: string;
    children: React.ReactNode;
    onCancel: () => void;
    onConfirm: () => void;
    confirmLabel: string;
  }) =>
    opened ? (
      <div role="dialog" aria-label={title}>
        {children}
        <button onClick={onCancel}>Отмена</button>
        <button onClick={onConfirm}>{confirmLabel}</button>
      </div>
    ) : null,
}));
function show(lesson?: Lesson) {
  const close = vi.fn();
  const router = createMemoryRouter([
    {
      path: '/',
      element: (
        <LessonEditor
          initial="2026-10-22T16:15:00+03:00"
          lesson={lesson}
          onClose={close}
        />
      ),
    },
    { path: '/away', element: <p>Другая страница</p> },
  ]);
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { close, router, user: userEvent.setup() };
}
it('closes pristine form after disclosure and search', async () => {
  const { user, close } = show();
  await user.click(screen.getByText('Дополнительно'));
  await user.type(screen.getByRole('combobox', { name: 'Ученик' }), 'Поиск');
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(close).toHaveBeenCalledOnce();
});
it.each([
  'Название занятия',
  'Тема (необязательно)',
  'Длительность, минут',
  'Ссылка встречи (замена ссылки курса)',
])('protects %s and preserves it after cancellation', async (name) => {
  const { user, close } = show();
  await user.click(screen.getByText('Дополнительно'));
  await user.type(screen.getByLabelText(name, { exact: true }), '1');
  const value = (
    screen.getByLabelText(name, { exact: true }) as HTMLInputElement
  ).value;
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(
    screen.getByRole('dialog', { name: 'Закрыть форму занятия?' }),
  ).toBeInTheDocument();
  expect(close).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(screen.getByLabelText(name, { exact: true })).toHaveValue(value);
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  await user.click(screen.getByRole('button', { name: 'Закрыть форму' }));
  expect(close).toHaveBeenCalledOnce();
});
it('restoring baseline removes protection; weekly choice protects', async () => {
  const { user, close } = show();
  const title = screen.getByLabelText('Название занятия');
  await user.clear(title);
  await user.type(title, 'Занятие');
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(close).toHaveBeenCalledOnce();
  await user.click(screen.getByLabelText('Закрепить время еженедельно'));
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(
    screen.getByRole('dialog', { name: 'Закрыть форму занятия?' }),
  ).toBeInTheDocument();
});
it('pristine edit compares existing lesson values', async () => {
  const { user, close } = show({
    title: 'Алгебра',
    topic: 'Уравнения',
    duration_minutes: 45,
    call_url_override: 'https://example.com',
  } as Lesson);
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(close).toHaveBeenCalledOnce();
});
it('route cancellation preserves edited values', async () => {
  const { user, router } = show();
  await user.type(screen.getByLabelText('Название занятия'), ' новое');
  void router.navigate('/away');
  expect(
    await screen.findByRole('dialog', { name: 'Уйти без сохранения?' }),
  ).toBeInTheDocument();
  await user.click(screen.getAllByRole('button', { name: 'Отмена' })[0]);
  expect(screen.getByLabelText('Название занятия')).toHaveValue(
    'Занятие новое',
  );
});

it('keeps pristine edit protected after uncertain save; no automatic retry', async () => {
  let fail!: (error: Error) => void;
  saveRequest.mockImplementationOnce(
    () =>
      new Promise((_, reject) => {
        fail = reject;
      }),
  );
  const { user, close } = show({
    id: 1,
    title: 'Занятие',
    duration_minutes: 55,
  } as Lesson);
  await user.click(screen.getByRole('button', { name: 'Проверить перенос' }));
  await user.click(screen.getByRole('button', { name: 'Подтвердить перенос' }));
  // close() also defends pending even if called directly by the modal adapter.
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(close).not.toHaveBeenCalled();
  await act(async () => fail(new Error('Connection lost')));
  await user.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(
    screen.getByRole('dialog', { name: 'Закрыть форму занятия?' }),
  ).toBeInTheDocument();
  expect(saveRequest).toHaveBeenCalledOnce();
  expect(close).not.toHaveBeenCalled();
});
