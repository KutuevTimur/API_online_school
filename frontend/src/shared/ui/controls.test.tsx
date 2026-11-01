import { useState } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { SelectField } from './SelectField';
import { ConfirmDialog } from './ConfirmDialog';
import { FormField } from './FormField';
import { ErrorSummary } from './ErrorSummary';
import { Pagination } from './Pagination';
it('select supports keyboard choice, Escape and clear', async () => {
  function Example() {
    const [value, setValue] = useState<string | null>(null);
    return (
      <SelectField
        label="Курс"
        data={['Математика', 'Физика']}
        value={value}
        onChange={setValue}
        clearable
      />
    );
  }
  render(
    <Providers>
      <Example />
    </Providers>,
  );
  const user = userEvent.setup();
  const input = screen.getByRole('combobox', { name: 'Курс' });
  await user.click(input);
  await user.keyboard('{ArrowDown}{Enter}');
  expect(input).toHaveValue('Математика');
  await user.click(input);
  await user.keyboard('{Escape}');
  expect(input).toHaveFocus();
  await user.click(screen.getByRole('button', { name: 'Очистить выбор' }));
  expect(input).toHaveValue('');
});
it('dialog focuses cancel, traps Tab and returns focus on Escape', async () => {
  function Example() {
    const [opened, setOpened] = useState(false);
    return (
      <>
        <button onClick={() => setOpened(true)}>Открыть</button>
        <ConfirmDialog
          opened={opened}
          title="Завершить проверку"
          onCancel={() => setOpened(false)}
          onConfirm={() => {}}
        >
          Результат изменить нельзя.
        </ConfirmDialog>
      </>
    );
  }
  render(
    <Providers>
      <Example />
    </Providers>,
  );
  const user = userEvent.setup();
  const trigger = screen.getByRole('button', { name: 'Открыть' });
  await user.click(trigger);
  expect(await screen.findByRole('dialog')).toHaveAccessibleName(
    'Завершить проверку',
  );
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Отмена' })).toHaveFocus(),
  );
  await user.tab();
  expect(screen.getByRole('button', { name: 'Подтвердить' })).toHaveFocus();
  await user.keyboard('{Escape}');
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  await waitFor(() => expect(trigger).toHaveFocus());
});
it('field errors associate label and focus first invalid field', () => {
  render(
    <Providers>
      <FormField id="title" label="Название" error="Заполните поле" />
      <ErrorSummary errors={{ title: 'Заполните поле' }} />
    </Providers>,
  );
  const input = screen.getByLabelText('Название');
  expect(input).toHaveFocus();
  expect(input).toHaveAttribute('aria-invalid', 'true');
  expect(input).toHaveAccessibleDescription('Заполните поле');
});
it('paging bounds and page size reset offset', async () => {
  const change = vi.fn();
  render(
    <Providers>
      <Pagination total={25} offset={0} limit={20} onChange={change} />
    </Providers>,
  );
  expect(screen.getByRole('button', { name: 'Назад' })).toBeDisabled();
  await userEvent.click(screen.getByRole('button', { name: 'Далее' }));
  expect(change).toHaveBeenCalledWith(20, 20);
});
