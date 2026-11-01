import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import type { Lesson } from '../courses/queries';
import { Providers } from '../../app/providers';
import { LessonStatusDialog } from './LessonStatusDialog';
const { send } = vi.hoisted(() => ({ send: vi.fn() }));
vi.mock('../../shared/api/client', () => ({ request: send }));
vi.mock('../../shared/ui/ConfirmDialog', () => ({
  ConfirmDialog: ({
    children,
    onConfirm,
    onCancel,
    confirmDisabled,
    pending,
  }: {
    children: React.ReactNode;
    onConfirm: () => void;
    onCancel: () => void;
    confirmDisabled: boolean;
    pending: boolean;
  }) => (
    <div role="dialog">
      {children}
      <button disabled={confirmDisabled || pending} onClick={onConfirm}>
        Подтвердить
      </button>
      <button onClick={onCancel}>Закрыть</button>
    </div>
  ),
}));
it('does not write before confirmation; uncertain write requires a read and never auto-retries', async () => {
  send.mockReset();
  send.mockRejectedValueOnce(new Error('timeout'));
  const close = vi.fn(),
    saved = vi.fn(),
    user = userEvent.setup();
  const lesson = {
    id: 7,
    title: 'Тест',
    status: 'scheduled',
    scheduled_at: '2026-11-02T12:00:00Z',
    updated_at: 'v1',
  } as Lesson;
  render(
    <Providers>
      <LessonStatusDialog
        lesson={lesson}
        status="cancelled"
        onClose={close}
        onSaved={saved}
      />
    </Providers>,
  );
  expect(send).not.toHaveBeenCalled();
  await user.click(screen.getByText('Подтвердить'));
  expect(send).toHaveBeenCalledWith('/lessons/7', {
    method: 'PATCH',
    body: { status: 'cancelled', expected_updated_at: 'v1' },
  });
  expect(screen.getByText('Подтвердить')).toBeDisabled();
  expect(saved).not.toHaveBeenCalled();
  send.mockResolvedValueOnce({
    ...lesson,
    status: 'cancelled',
    updated_at: 'v2',
  });
  await user.click(screen.getByText('Загрузить актуальное занятие'));
  expect(send).toHaveBeenCalledTimes(2);
  expect(close).toHaveBeenCalledOnce();
  expect(saved).not.toHaveBeenCalled();
});
