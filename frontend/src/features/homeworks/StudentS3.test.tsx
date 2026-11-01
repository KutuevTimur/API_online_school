import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import type { Answer } from '../../shared/api/files';
import type { Homework } from '../courses/queries';
import { AnswerForm } from './AnswerForm';
import { HomeworkThread } from '../lessons/LessonPage';
import { studentAnswerState } from '../../shared/lib/studentAnswerState';
import { StatusBadge, StudentAnswerBadge } from '../../shared/ui/StatusBadge';
const { read, api } = vi.hoisted(() => ({ read: vi.fn(), api: vi.fn() }));
vi.mock('../courses/queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
vi.mock('../../shared/api/client', async (original) => ({
  ...(await original<object>()),
  request: api,
}));
vi.mock('../auth/session', async (original) => ({
  ...(await original<object>()),
  useSession: () => ({ user: { id: 31, role: 'student' } }),
}));
const answer = {
  id: 12,
  homework_id: 5,
  version: 3,
  status: 'draft',
  text_content: 'Сохранённый текст',
  files: [],
  review_files: [],
  grade: null,
} as unknown as Answer;
const homework = {
  id: 5,
  title: 'Уравнения',
  description: 'Решите уравнение',
  working_submission_id: 12,
  access_mode: 'active',
  placement_kind: 'debt',
} as unknown as Homework;
function show(element: React.ReactNode) {
  const router = createMemoryRouter([{ path: '/', element }]);
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
}
const success = (data: unknown) => ({
  data,
  isPending: false,
  isFetching: false,
  isError: false,
  refetch: vi.fn(),
});
beforeEach(() => {
  api.mockReset();
  read
    .mockReset()
    .mockImplementation((_path, _params, enabled = true) =>
      enabled ? success(answer) : { isPending: true },
    );
  Element.prototype.scrollIntoView = vi.fn();
});
it('separates id=0, local work, persisted draft, unknown and readonly', () => {
  expect(studentAnswerState({ ...answer, id: 0 })).toBe('empty');
  expect(studentAnswerState({ ...answer, id: 0 }, { dirty: true })).toBe(
    'local',
  );
  expect(studentAnswerState(answer)).toBe('draft');
  expect(studentAnswerState(answer, { uncertain: true })).toBe('unknown');
  expect(studentAnswerState(answer, { readOnly: true })).toBe('readonly');
});
it('opening and typing in an id=0 form creates no submission and shows local unsaved work', async () => {
  show(
    <AnswerForm
      homeworkId={5}
      initial={{ ...answer, id: 0, text_content: null }}
      readOnly={false}
    />,
  );
  expect(screen.getByText('Решение ещё не отправлено')).toBeInTheDocument();
  await userEvent.type(
    screen.getByLabelText('Текст решения или вопросы'),
    'Мой ответ',
  );
  expect(
    screen.getByText('Локальное решение · не сохранено'),
  ).toBeInTheDocument();
  expect(api).not.toHaveBeenCalled();
});
it('marks saved draft separately and retains local changes over the server copy', async () => {
  show(<AnswerForm homeworkId={5} initial={answer} readOnly={false} />);
  expect(
    screen.getByText('Черновик сохранён · не отправлен'),
  ).toBeInTheDocument();
  await userEvent.type(
    screen.getByLabelText('Текст решения или вопросы'),
    ' + правка',
  );
  expect(screen.getByText(/Есть несохранённые изменения/)).toBeInTheDocument();
  expect(api).not.toHaveBeenCalled();
});
it('submitted explains past sending and offers saving edits', () => {
  show(
    <AnswerForm
      homeworkId={5}
      initial={{ ...answer, status: 'submitted' }}
      readOnly={false}
    />,
  );
  expect(screen.getByText('На проверке')).toBeInTheDocument();
  expect(
    screen.getByText(/Решение отправлено. До проверки/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: 'Сохранить изменения' }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'Отправить решение' }),
  ).not.toBeInTheDocument();
});
it.each([0, 5])(
  'checked grade %i stays read-only with optional feedback files',
  (grade) => {
    show(
      <AnswerForm
        homeworkId={5}
        initial={{ ...answer, status: 'checked', grade }}
        readOnly={false}
      />,
    );
    expect(screen.getByText(`Оценка: ${grade} из 5`)).toBeInTheDocument();
    expect(
      screen.getByText('Учитель не добавил комментарий'),
    ).toBeInTheDocument();
    expect(screen.queryByText('Файлы от учителя')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Текст решения или вопросы')).toHaveAttribute(
      'readonly',
    );
    expect(
      screen.queryByRole('button', { name: 'Сохранить изменения' }),
    ).not.toBeInTheDocument();
  },
);
it('archive has no mutation controls but keeps answer readable', () => {
  show(<AnswerForm homeworkId={5} initial={answer} readOnly />);
  expect(screen.getByText('Только просмотр')).toBeInTheDocument();
  expect(screen.getByLabelText('Текст решения или вопросы')).toHaveValue(
    'Сохранённый текст',
  );
  expect(
    screen.queryByRole('button', { name: 'Отправить решение' }),
  ).not.toBeInTheDocument();
});
it('failed stale GET is unknown and cannot expose mutation controls', () => {
  show(
    <AnswerForm homeworkId={5} initial={answer} readOnly={false} loadError />,
  );
  expect(
    screen.getByText('Состояние решения не подтверждено'),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('button', { name: 'Отправить решение' }),
  ).not.toBeInTheDocument();
});
it('each homework/debt has its own condition and action that only navigates', () => {
  show(
    <>
      <HomeworkThread homework={{ ...homework, working_submission_id: null }} />
      <HomeworkThread homework={{ ...homework, id: 6, title: 'Графики' }} />
    </>,
  );
  expect(
    screen.getByRole('link', { name: 'Подготовить решение' }),
  ).toHaveAttribute('href', '/student/homeworks/5');
  expect(
    screen.getByRole('link', { name: 'Продолжить решение' }),
  ).toHaveAttribute('href', '/student/homeworks/6');
  expect(screen.getAllByText(/Долг/)).toHaveLength(2);
  expect(api).not.toHaveBeenCalled();
});
it('checked CTA focuses the visible review result, including grade zero', async () => {
  read.mockReturnValue(success({ ...answer, status: 'checked', grade: 0 }));
  show(<HomeworkThread homework={homework} />);
  await userEvent.click(
    screen.getByRole('button', { name: 'Посмотреть результат' }),
  );
  expect(
    screen.getByRole('region', { name: 'Результат проверки: Уравнения' }),
  ).toHaveFocus();
  expect(screen.getByText('Оценка: 0 из 5')).toBeInTheDocument();
});
it.each(['loading', 'error'])(
  'answer %s never becomes missing or an invitation to submit',
  (kind) => {
    read.mockReturnValue({
      isPending: kind === 'loading',
      isError: kind === 'error',
      refetch: vi.fn(),
    });
    show(<HomeworkThread homework={homework} />);
    expect(
      screen.getByText('Состояние решения не подтверждено'),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Подготовить решение' }),
    ).not.toBeInTheDocument();
  },
);
it('student waiting variant does not change teacher badge presentation', () => {
  show(
    <>
      <StatusBadge status="submitted" />
      <StudentAnswerBadge state="submitted" />
    </>,
  );
  const badges = screen.getAllByText('На проверке');
  expect(badges[0]).toHaveAttribute('data-tone', 'neutral');
  expect(badges[1]).toHaveAttribute('data-state', 'submitted');
});
