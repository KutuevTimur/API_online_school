import { MemoryRouter } from 'react-router';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Providers } from '../app/providers';
import { StudentPreview } from './StudentPreview';
function setup(path = '/__ui') {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Providers>
        <StudentPreview />
      </Providers>
    </MemoryRouter>,
  );
  return userEvent.setup();
}
it('opens a result, moves focus to its heading and returns to the overview', async () => {
  const user = setup();
  await user.click(
    screen.getByRole('button', { name: 'Посмотреть результат' }),
  );
  const heading = await screen.findByRole('heading', {
    name: 'Результат проверки',
  });
  expect(heading).toHaveFocus();
  expect(screen.getByText(/одного ответа недостаточно/)).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'К моему дню' }));
  expect(screen.getByRole('heading', { name: 'Привет, Иван.' })).toHaveFocus();
});
it('clearly explains that a sample meeting cannot connect and makes no request', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch');
  const user = setup();
  await user.click(screen.getByRole('button', { name: 'Подключиться' }));
  expect(await screen.findByRole('dialog')).toHaveAccessibleName(
    'Пример онлайн-занятия',
  );
  expect(
    screen.getByText(/В этом примере встреча не подключена/),
  ).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Понятно' }));
  await waitFor(() =>
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
  );
  expect(fetch).not.toHaveBeenCalled();
});
it('a geometry course opens its own subject rather than the mathematics lesson', async () => {
  const user = setup();
  await user.click(
    screen.getByRole('button', { name: 'Открыть курс Геометрия' }),
  );
  expect(
    await screen.findByRole('heading', { name: 'Геометрия', level: 1 }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('heading', { name: 'Треугольники', level: 2 }),
  ).toBeInTheDocument();
});
it('supports a direct sample assignment-list URL and honestly explains the unconnected answer', async () => {
  const user = setup('/__ui?role=student&section=%2Fstudent%2Fhomeworks');
  expect(
    screen.getByRole('heading', { name: 'Домашние задания', level: 1 }),
  ).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Открыть задание' }));
  expect(
    await screen.findByRole('heading', { name: 'Что нужно сделать' }),
  ).toBeInTheDocument();
  expect(
    screen.getByText(/В этом примере ответ не сохраняется/),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'Отправить решение' }),
  ).not.toBeInTheDocument();
});
