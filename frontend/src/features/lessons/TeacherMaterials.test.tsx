import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { TeacherMaterials } from './TeacherMaterials';
const { read, mutate, fixture } = vi.hoisted(() => ({
  read: vi.fn(),
  mutate: vi.fn(),
  fixture: {
    homeworks: [] as unknown[],
    has: false,
    notNeeded: false,
    failed: false,
  },
}));
vi.mock('../courses/queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
vi.mock('../../shared/api/client', async (original) => ({
  ...(await original<object>()),
  request: mutate,
}));
// Upload behaviour is owned by the existing queue; this suite tests its placement.
vi.mock('../../shared/ui/MaterialUploadQueue', () => ({
  MaterialUploadQueue: () => <p>Очередь конспектов</p>,
}));
beforeEach(() => {
  fixture.homeworks = [];
  fixture.has = false;
  fixture.notNeeded = false;
  fixture.failed = false;
  mutate.mockReset();
  read.mockReset().mockImplementation((path) => ({
    data:
      path === '/homeworks'
        ? fixture.homeworks
        : path === '/teacher-planning/reminders'
          ? {
              items: [
                {
                  has_lecture: fixture.has,
                  has_homework: fixture.has,
                  lecture_not_needed: fixture.notNeeded,
                  homework_not_needed: fixture.notNeeded,
                },
              ],
              total: 1,
            }
          : { items: [], total: 0 },
    isPending: false,
    isError: fixture.failed,
    refetch: vi.fn().mockResolvedValue({ isError: false }),
  }));
});
function show(readOnly = false) {
  const dirty = vi.fn();
  const router = createMemoryRouter([
    {
      path: '/',
      element: (
        <TeacherMaterials
          lessonId={8}
          studentId={42}
          readOnly={readOnly}
          onDirtyChange={dirty}
        />
      ),
    },
    { path: '/away', element: <p>Вышли</p> },
  ]);
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { router, dirty, user: userEvent.setup() };
}
it('discloses issuance and preserves dirty text/files across cancel and confirmed collapse', async () => {
  const { user, dirty, router } = show();
  expect(screen.queryByLabelText('Название задания')).not.toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Выдать задание' }));
  await user.type(screen.getByLabelText('Название задания'), 'Новая работа');
  await user.type(screen.getByLabelText('Условие', { exact: true }), 'Текст');
  await user.upload(
    screen.getByLabelText('Добавить файл'),
    new File(['pdf'], 'draft.pdf', { type: 'application/pdf' }),
  );
  expect(dirty).toHaveBeenLastCalledWith(true);
  await user.click(
    screen.getByRole('button', { name: 'Свернуть выдачу задания' }),
  );
  const dialog = await screen.findByRole('dialog', {
    name: 'Свернуть выдачу задания?',
  });
  await user.click(within(dialog).getByRole('button', { name: 'Отмена' }));
  expect(screen.getByLabelText('Название задания')).toHaveValue('Новая работа');
  await user.click(
    screen.getByRole('button', { name: 'Свернуть выдачу задания' }),
  );
  await user.click(
    screen.getByRole('button', { name: 'Свернуть, сохранив ввод' }),
  );
  await user.click(screen.getByRole('button', { name: 'Выдать задание' }));
  expect(screen.getByLabelText('Название задания')).toHaveValue('Новая работа');
  expect(screen.getByText('draft.pdf')).toBeVisible();
  expect(mutate).not.toHaveBeenCalled();
  void router.navigate('/away');
  await waitFor(() =>
    expect(
      screen.getByRole('dialog', { name: 'Уйти без сохранения?' }),
    ).toBeVisible(),
  );
});
it('distinguishes all answer states and keeps not-needed controls in their sections', () => {
  fixture.has = true;
  fixture.homeworks = ['checked', 'submitted', 'draft', null].map(
    (status, id) => ({
      id,
      title: `Работа ${id}`,
      description: 'https://example.com',
      submission_status: status,
      working_submission_id: status ? id + 1 : null,
    }),
  );
  show();
  expect(screen.getByText('Работа проверена', { exact: false })).toBeVisible();
  expect(screen.getByText(/Ответ получен/)).toBeVisible();
  expect(
    screen.getByText(/Ответ ещё не отправлен · у ученика черновик/),
  ).toBeVisible();
  expect(screen.getByText(/Ждём ответ ученика/)).toBeVisible();
  expect(
    screen.getByRole('link', { name: 'Посмотреть проверку' }),
  ).toBeVisible();
  expect(screen.getByRole('link', { name: 'Проверить работу' })).toBeVisible();
  expect(
    screen.getAllByRole('link', {
      name: /Проверить работу|Посмотреть проверку/,
    }),
  ).toHaveLength(2);
  expect(screen.getByRole('button', { name: 'Не задавать ДЗ' })).toBeVisible();
  expect(
    screen.getByRole('button', { name: 'Не добавлять конспект' }),
  ).toBeVisible();
});
it('does not offer writes in read-only lessons', () => {
  show(true);
  expect(
    screen.queryByRole('button', { name: 'Выдать задание' }),
  ).not.toBeInTheDocument();
  expect(screen.queryByText('Очередь конспектов')).not.toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'Не задавать ДЗ' }),
  ).not.toBeInTheDocument();
});
it('keeps draft and disables repeat after an uncertain mock request', async () => {
  mutate.mockRejectedValueOnce(new Error('uncertain'));
  const { user } = show();
  await user.click(screen.getByRole('button', { name: 'Выдать задание' }));
  await user.type(screen.getByLabelText('Название задания'), 'Сохранить ввод');
  await user.click(screen.getByRole('button', { name: 'Выдать задание' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Не удалось подтвердить выдачу',
  );
  expect(screen.getByLabelText('Название задания')).toHaveValue(
    'Сохранить ввод',
  );
  expect(screen.getByRole('button', { name: 'Выдать задание' })).toBeDisabled();
  expect(mutate).toHaveBeenCalledTimes(1);
});

it.each([
  [false, false, false, 'missing'],
  [true, false, false, 'ready'],
  [false, true, false, undefined],
  [true, true, false, undefined],
  [true, false, true, undefined],
])(
  'uses confirmed state and treats not-needed/error as neutral: %s/%s/%s',
  (has, notNeeded, failed, tone) => {
    fixture.has = has;
    fixture.notNeeded = notNeeded;
    fixture.failed = failed;
    show();
    for (const name of ['Конспекты', 'Домашние задания']) {
      const panel = screen.getByRole('region', { name });
      if (tone) expect(panel).toHaveAttribute('data-material-state', tone);
      else expect(panel).not.toHaveAttribute('data-material-state');
    }
    if (notNeeded) {
      expect(screen.getByText('Конспект не требуется')).toBeVisible();
      expect(screen.getByText('ДЗ не требуется')).toBeVisible();
    }
  },
);
it('keeps not-needed actions visible, patches only the selected kind and stays neutral while pending', async () => {
  let resolve!: (data: object) => void;
  mutate.mockImplementationOnce(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const { user } = show();
  await user.click(
    screen.getByRole('button', { name: 'Не добавлять конспект' }),
  );
  expect(mutate).toHaveBeenCalledWith(
    '/teacher-planning/lessons/8/students/42',
    expect.objectContaining({
      method: 'PATCH',
      body: { lecture_not_needed: true },
    }),
  );
  expect(screen.getByRole('region', { name: 'Конспекты' })).not.toHaveAttribute(
    'data-material-state',
  );
  expect(screen.getByRole('button', { name: 'Не задавать ДЗ' })).toBeDisabled();
  resolve({});
  await waitFor(() =>
    expect(
      screen.getByRole('button', { name: 'Не задавать ДЗ' }),
    ).toBeEnabled(),
  );
});

it.each([
  [undefined, 'Ждём ответ ученика', undefined],
  ['draft', 'Ответ ещё не отправлен · у ученика черновик', undefined],
  ['submitted', 'Ответ получен · нужно проверить', 'Проверить работу'],
  ['checked', 'Работа проверена', 'Посмотреть проверку'],
] as const)(
  'shows response state %s and the exact review destination',
  (status, text, action) => {
    fixture.homeworks = [
      {
        id: 73,
        title: 'Проверка состояний ответа',
        description: '',
        deadline: null,
        submission_status: status,
        working_submission_id: 94,
      },
    ];
    show();
    expect(screen.getByText(text, { exact: true })).toBeVisible();
    if (action) {
      expect(screen.getByRole('link', { name: action })).toHaveAttribute(
        'href',
        '/teacher/review/94?homework_id=73',
      );
    } else {
      expect(
        screen.queryByRole('link', {
          name: /Проверить работу|Посмотреть проверку/,
        }),
      ).not.toBeInTheDocument();
    }
  },
);

it('does not offer a review destination without a submission id', () => {
  fixture.homeworks = [
    {
      id: 73,
      title: 'Ответ без id',
      description: '',
      deadline: null,
      submission_status: 'submitted',
    },
  ];
  show();
  expect(screen.getByText('Ответ получен · нужно проверить')).toBeVisible();
  expect(
    screen.queryByRole('link', { name: 'Проверить работу' }),
  ).not.toBeInTheDocument();
});
