import { render, screen, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { MyDayPage } from './MyDayPage';
import { SchedulePage } from '../schedule/SchedulePage';
import { CallLink } from '../lessons/LessonPage';
const { read } = vi.hoisted(() => ({ read: vi.fn() }));
vi.mock('./queries', async (original) => ({
  ...(await original<object>()),
  useRead: read,
}));
vi.mock('../auth/session', async (original) => ({
  ...(await original<object>()),
  useSession: () => ({ user: { id: 31, role: 'student' } }),
}));
const lesson = {
  id: 124,
  course_id: 900,
  course_name: 'Fallback курса',
  title: 'Занятие',
  topic: 'Тема из API',
  scheduled_at: '2026-10-27T11:00:00Z',
  duration_minutes: 55,
  status: 'scheduled',
  effective_call_url: 'https://example.com/meeting',
};
const hw = {
  id: 55,
  title: 'Задача',
  course_name: 'Курс',
  lesson_id: 123,
  working_submission_id: 77,
};
const ok = (data: unknown) => ({
  data,
  isPending: false,
  isError: false,
  isFetching: false,
  refetch: vi.fn(),
});
let count = 2;
let metaError = false;
let nearest = true;
let pending = false;
beforeEach(() => {
  count = 2;
  metaError = false;
  nearest = true;
  pending = false;
  read.mockReset().mockImplementation((path, params) => {
    if (path === '/courses/900')
      return metaError
        ? { ...ok(undefined), isError: true, error: new Error() }
        : ok({
            id: 900,
            name: 'Курс вне первой страницы',
            teacher_name: 'Настоящий преподаватель',
          });
    if (path === '/courses') return ok({ items: [], total: 0 });
    if (path === '/lessons' && params?.status === 'completed')
      return ok({ items: [], total: 0 });
    if (path === '/lessons')
      return pending
        ? { isPending: true }
        : ok({ items: nearest ? [lesson] : [], total: nearest ? 1 : 0 });
    if (path === '/homeworks/my/page')
      return ok({
        items:
          params.status === 'checked'
            ? [hw]
            : Array.from({ length: count }, (_, i) => ({ ...hw, id: 55 + i })),
        total: params.status === 'checked' ? 1 : count,
      });
    if (path === '/submissions/77') return ok({ status: 'checked', grade: 0 });
    return ok({ items: [], total: 0 });
  });
});
function show(element: React.ReactNode) {
  const router = createMemoryRouter([{ path: '*', element }]);
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
}
it('uses topic and scoped course detail independently of first catalog page', () => {
  show(<MyDayPage />);
  expect(screen.getByText('Тема из API')).toBeInTheDocument();
  expect(
    screen.getByText('Курс: Курс вне первой страницы'),
  ).toBeInTheDocument();
  expect(
    screen.getByText('Преподаватель: Настоящий преподаватель'),
  ).toBeInTheDocument();
  expect(read).toHaveBeenCalledWith('/courses/900');
  expect(screen.queryByText(/55 мин/)).not.toBeInTheDocument();
});
it('keeps source order and uses student waiting badges for every submitted row', () => {
  show(<MyDayPage />);
  const names = screen
    .getAllByRole('heading', { level: 2 })
    .map((e) => e.textContent);
  expect(names.slice(0, 4)).toEqual([
    'Ближайшее занятие',
    'К выполнению',
    'На проверке',
    'Последний результат',
  ]);
  expect(
    screen.getAllByText('На проверке', { exact: true, selector: 'span' }),
  ).toHaveLength(2);
  expect(
    screen
      .getAllByRole('link', { name: 'Открыть решение' })
      .map((e) => e.getAttribute('href')),
  ).toEqual(['/student/homeworks/55', '/student/homeworks/56']);
});
it('shows grade zero compactly and links to the exact visible result', () => {
  show(<MyDayPage />);
  const region = screen.getByRole('region', { name: 'Последний результат' });
  expect(within(region).getByText('Проверено · 0 из 5')).toBeInTheDocument();
  expect(
    within(region).getByRole('link', { name: 'Посмотреть результат' }),
  ).toHaveAttribute('href', '/student/homeworks/55#result');
});
it('handles missing nearest and empty lists', () => {
  nearest = false;
  count = 0;
  show(<MyDayPage />);
  expect(screen.getByText(/Пока нет предстоящих/)).toBeInTheDocument();
  expect(
    screen.getByText('Заданий к выполнению пока нет.'),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('link', { name: 'Присоединиться' }),
  ).not.toBeInTheDocument();
});
it('keeps one submitted item with the same student status', () => {
  count = 1;
  show(<MyDayPage />);
  expect(
    screen.getAllByText('На проверке', { exact: true, selector: 'span' }),
  ).toHaveLength(1);
});
it('metadata error preserves lesson, fallback and retry', () => {
  metaError = true;
  show(<MyDayPage />);
  expect(screen.getByText('Курс: Fallback курса')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent(
    'Не удалось загрузить данные курса и преподавателя',
  );
  expect(screen.getByRole('link', { name: 'Открыть занятие' })).toHaveAttribute(
    'href',
    '/student/lessons/124',
  );
  expect(screen.getByRole('button', { name: 'Повторить' })).toBeInTheDocument();
});
it('keeps independent task sections during nearest loading', () => {
  pending = true;
  show(<MyDayPage />);
  expect(
    screen.getByRole('heading', { name: 'К выполнению' }),
  ).toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: 'Открыть решение' })).toHaveLength(
    2,
  );
});
afterEach(() => vi.useRealTimers());
it('schedule uses topic, teacher and planned status without duration', () => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-10-26T09:00:00Z'));
  show(<SchedulePage />);
  expect(
    screen.getByRole('link', { name: 'Открыть занятие: Тема из API' }),
  ).toBeInTheDocument();
  expect(screen.getByText('Запланировано')).toBeInTheDocument();
  expect(
    screen.getByText('Преподаватель: Настоящий преподаватель'),
  ).toBeInTheDocument();
  expect(screen.queryByText(/55 мин/)).not.toBeInTheDocument();
});
it('CallLink keeps teacher semantics and student video variant', () => {
  show(
    <>
      <CallLink url="https://example.com" />
      <CallLink audience="student" url="http://example.com" />
    </>,
  );
  expect(screen.getByRole('link', { name: 'Открыть встречу' })).toHaveAttribute(
    'rel',
    'noopener noreferrer',
  );
  expect(
    screen.getByRole('link', { name: 'Присоединиться' }).querySelector('svg'),
  ).not.toBeNull();
});
it.each([undefined, 'javascript:alert(1)', 'data:text/html,hello'])(
  'does not offer an unsafe or absent meeting %s',
  (url) => {
    show(<CallLink audience="student" url={url} />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(
      screen.getByText('Ссылка на встречу ещё не добавлена'),
    ).toBeInTheDocument();
  },
);

it('summarizes the last completed date/teacher but opens only the lessons section', () => {
  const original = read.getMockImplementation()!;
  read.mockImplementation((path, params, ...rest) =>
    path === '/lessons' && params?.status === 'completed'
      ? ok({
          items: [
            {
              ...lesson,
              id: 127,
              topic: 'Последняя тема',
              access_mode: 'read_only',
            },
          ],
          total: 1,
        })
      : original(path, params, ...rest),
  );
  show(<MyDayPage />);
  const block = screen.getByRole('region', {
    name: /^Мои занятия$/,
  });
  expect(read).toHaveBeenCalledWith('/lessons', {
    view: 'all',
    status: 'completed',
    sort_date: 'desc',
    limit: 1,
    offset: 0,
  });
  expect(within(block).queryByText('Последняя тема')).not.toBeInTheDocument();
  expect(within(block).queryByText(/^Курс:/)).not.toBeInTheDocument();
  expect(
    within(block).getByText(/Последнее занятие.*27 октября, 14:00 МСК/),
  ).toBeInTheDocument();
  expect(
    within(block).getByText('Преподаватель: Настоящий преподаватель'),
  ).toBeInTheDocument();
  expect(within(block).getAllByRole('link')).toHaveLength(1);
  expect(
    within(block).getByRole('link', { name: 'Открыть занятия' }),
  ).toHaveAttribute('href', '/student/materials');
});
it('keeps history reachable without completed lessons', () => {
  show(<MyDayPage />);
  const block = screen.getByRole('region', {
    name: /^Мои занятия$/,
  });
  expect(
    within(block).getByText('Здесь появится последнее проведённое занятие.'),
  ).toBeInTheDocument();
  expect(
    within(block).getByRole('link', { name: 'Открыть занятия' }),
  ).toBeInTheDocument();
});
