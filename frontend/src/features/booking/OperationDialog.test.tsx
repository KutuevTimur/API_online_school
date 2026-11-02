import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { describe, it, expect, vi } from 'vitest';
import { OperationDialog } from './OperationDialog';
import { execute, receipt } from './api';
import { ApiError } from '../../shared/api/error';
vi.mock('./api', () => ({ execute: vi.fn(), receipt: vi.fn() }));
const command = {
  path: '/teacher-planning/booking-windows',
  action: 'windows_publish',
  body: {},
};
function mount(success = vi.fn(), reload?: () => Promise<void>) {
  const router = createMemoryRouter([
    {
      path: '/',
      element: (
        <OperationDialog
          title="Открыть окно"
          label="Сохранить окно"
          command={command}
          onSuccess={success}
          onClose={vi.fn()}
          onReload={reload}
        >
          <input aria-label="Время" defaultValue="15:00" />
        </OperationDialog>
      ),
    },
  ]);
  render(
    <MantineProvider>
      <QueryClientProvider client={new QueryClient()}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </MantineProvider>,
  );
  return success;
}
describe('operation confirmation', () => {
  it('checks receipt after timeout and never repeats POST', async () => {
    vi.mocked(execute).mockRejectedValueOnce(new ApiError(0, 'timeout'));
    vi.mocked(receipt)
      .mockRejectedValueOnce(new ApiError(404, 'unknown'))
      .mockResolvedValueOnce({
        operation_id: 'id',
        state: 'committed',
        result: {},
        delivery: {},
      });
    const success = mount();
    fireEvent.click(
      await screen.findByRole('button', { name: 'Сохранить окно' }),
    );
    fireEvent.click(
      await screen.findByRole('button', { name: 'Проверить результат' }),
    );
    await screen.findByText(/Результат пока неизвестен/);
    expect(execute).toHaveBeenCalledTimes(1);
    fireEvent.click(
      screen.getByRole('button', { name: 'Проверить результат' }),
    );
    await waitFor(() => expect(success).toHaveBeenCalledTimes(1));
    expect(execute).toHaveBeenCalledTimes(1);
  });
  it('preserves entered values on conflict and requires explicit reload', async () => {
    vi.mocked(execute)
      .mockClear()
      .mockRejectedValueOnce(new ApiError(409, 'stale'));
    const reload = vi.fn().mockResolvedValue(undefined);
    mount(vi.fn(), reload);
    fireEvent.change(await screen.findByLabelText('Время'), {
      target: { value: '17:00' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить окно' }));
    await screen.findByText(/Данные изменились/);
    expect(screen.getByLabelText('Время')).toHaveValue('17:00');
    expect(
      screen.getByRole('button', { name: 'Сохранить окно' }),
    ).toBeDisabled();
    fireEvent.click(
      screen.getByRole('button', {
        name: 'Обновить данные, сохранив введённое',
      }),
    );
    await waitFor(() => expect(reload).toHaveBeenCalledTimes(1));
    expect(screen.getByLabelText('Время')).toHaveValue('17:00');
  });
});
