import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { useFeedback } from './FeedbackProvider';
function Harness({ run }: { run: () => Promise<void> }) {
  const show = useFeedback();
  return (
    <>
      <button
        onClick={() =>
          show('Сохранено', {
            durationMs: 15000,
            action: { label: 'Вернуть', run },
          })
        }
      >
        Показать
      </button>
      <button onClick={() => show('Новое событие')}>Другое</button>
    </>
  );
}
it('waits for the inverse acknowledgement and blocks duplicate clicks', async () => {
  let resolve!: () => void;
  const run = vi.fn(
    () =>
      new Promise<void>((r) => {
        resolve = r;
      }),
  );
  const user = userEvent.setup();
  render(
    <Providers>
      <Harness run={run} />
    </Providers>,
  );
  await user.click(screen.getByText('Показать'));
  await user.dblClick(screen.getByRole('button', { name: 'Вернуть' }));
  expect(run).toHaveBeenCalledOnce();
  expect(screen.getByRole('button', { name: 'Вернуть' })).toBeDisabled();
  expect(
    screen.queryByText('Предыдущее действие отменено'),
  ).not.toBeInTheDocument();
  await act(async () => resolve());
  expect(screen.getByText('Предыдущее действие отменено')).toBeInTheDocument();
});
it('reports failure without an automatic retry or false success', async () => {
  const run = vi.fn().mockRejectedValue(new Error('Конфликт версии'));
  const user = userEvent.setup();
  render(
    <Providers>
      <Harness run={run} />
    </Providers>,
  );
  await user.click(screen.getByText('Показать'));
  await user.click(screen.getByRole('button', { name: 'Вернуть' }));
  expect(await screen.findByText('Конфликт версии')).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'Вернуть' }),
  ).not.toBeInTheDocument();
  expect(run).toHaveBeenCalledOnce();
});
it('does not overwrite a newer notice with a late inverse acknowledgement', async () => {
  let resolve!: () => void;
  const user = userEvent.setup();
  render(
    <Providers>
      <Harness
        run={() =>
          new Promise<void>((r) => {
            resolve = r;
          })
        }
      />
    </Providers>,
  );
  await user.click(screen.getByText('Показать'));
  await user.click(screen.getByRole('button', { name: 'Вернуть' }));
  await user.click(screen.getByText('Другое'));
  await act(async () => resolve());
  expect(screen.getByText('Новое событие')).toBeInTheDocument();
});
