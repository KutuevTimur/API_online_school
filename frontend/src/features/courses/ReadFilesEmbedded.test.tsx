import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import { ReadFiles } from './ReadUI';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import type { FileDescriptor } from '../../shared/api/files';
import type { FileViewState } from '../../shared/ui/FilePreview';
const viewport = vi.hoisted(() => ({ desktop: true }));
vi.mock('@mantine/hooks', async (original) => ({
  ...(await original<object>()),
  useMediaQuery: () => viewport.desktop,
}));
vi.mock('../../shared/ui/FilePreview', () => {
  type Props = {
    file?: FileDescriptor;
    files: FileDescriptor[];
    index: number;
    onClose: () => void;
    onIndexChange: (i: number) => void;
    viewState?: FileViewState;
    onViewChange?: (state: FileViewState) => void;
  };
  function Body({ viewState, onViewChange, onIndexChange }: Props) {
    return (
      <div data-testid="heavy">
        <output>{JSON.stringify(viewState || { page: 1, zoom: 1 })}</output>
        <button onClick={() => onViewChange?.({ page: 2, zoom: 1.5 })}>
          Масштаб и страница
        </button>
        <button onClick={() => onIndexChange(1)}>Следующий</button>
      </div>
    );
  }
  return {
    FilePreviewBody: Body,
    FilePreview: (props: Props) =>
      props.index >= 0 ? (
        <div role="dialog">
          <Body {...props} />
          <button onClick={props.onClose}>Закрыть</button>
        </div>
      ) : null,
  };
});
const files = [
  { id: 11, display_name: 'PDF', download_url: '/files/11' },
  { id: 12, display_name: 'Фото', download_url: '/files/12' },
] as FileDescriptor[];
beforeEach(() => {
  viewport.desktop = true;
});
function show(search = '') {
  const router = createMemoryRouter(
    [
      {
        path: '/',
        element: (
          <>
            <DirtyFormGuard dirty allowPreviewQuery />
            <ReadFiles embedded files={files} />
            <ReadFiles condition files={files} />
          </>
        ),
      },
    ],
    {
      initialEntries: [
        {
          pathname: '/',
          search: '?homework_id=5&limit=50' + search,
          state: { returnTo: '/teacher/review?offset=20' },
        },
      ],
    },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { router, user: userEvent.setup() };
}
it('switches one renderer between embedded/fullscreen, preserves view state, history and dirty context', async () => {
  const { router, user } = show();
  const embedded = screen.getByRole('region', {
    name: 'Просмотр файла решения',
  });
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  await user.click(
    within(embedded).getByRole('button', { name: 'Масштаб и страница' }),
  );
  await user.click(screen.getByRole('button', { name: 'Открыть крупно' }));
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  expect(
    within(screen.getByRole('dialog')).getByRole('status'),
  ).toHaveTextContent('"page":2,"zoom":1.5');
  expect(router.state.location.search).toBe('?homework_id=5&limit=50&file=11');
  await user.click(screen.getByRole('button', { name: 'Закрыть' }));
  await waitFor(() =>
    expect(router.state.location.search).toBe('?homework_id=5&limit=50'),
  );
  expect(within(embedded).getByRole('status')).toHaveTextContent(
    '"page":2,"zoom":1.5',
  );
  expect(router.state.location.state).toEqual({
    returnTo: '/teacher/review?offset=20',
  });
  await user.click(screen.getAllByRole('button', { name: 'Открыть PDF' })[1]);
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  expect(router.state.location.search).toContain('condition-file=11');
});
it('arbitrates direct multi-preview URLs and does not embed on narrow screens', async () => {
  viewport.desktop = false;
  const { user } = show('&file=11&condition-file=12');
  expect(
    screen.queryByRole('region', { name: 'Просмотр файла решения' }),
  ).toBeNull();
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  await user.click(screen.getByRole('button', { name: 'Закрыть' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeInTheDocument());
  // The remaining earlier key becomes active, still only one renderer.
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
});

function studyShow() {
  const router = createMemoryRouter(
    [
      {
        path: '/',
        element: (
          <>
            <DirtyFormGuard dirty allowPreviewQuery />
            <ReadFiles
              material
              studyLabel="конспект"
              initiallyCollapsed
              files={files}
            />
            <ReadFiles condition studyLabel="файл задания" files={[files[0]]} />
          </>
        ),
      },
    ],
    { initialEntries: ['/?limit=50'] },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { router, user: userEvent.setup() };
}
it('lecture starts collapsed on desktop while condition stays expanded, preserves view after manual expansion', async () => {
  const { user } = studyShow();
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  expect(
    screen.queryByRole('region', { name: 'Просмотр: конспект' }),
  ).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Развернуть конспект' }));
  const material = screen.getByRole('region', { name: 'Просмотр: конспект' });
  expect(screen.getAllByTestId('heavy')).toHaveLength(2);
  await user.click(
    within(material).getByRole('button', { name: 'Масштаб и страница' }),
  );
  await user.click(screen.getByRole('button', { name: 'Свернуть конспект' }));
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  await user.click(screen.getByRole('button', { name: 'Развернуть конспект' }));
  expect(
    within(
      screen.getByRole('region', { name: 'Просмотр: конспект' }),
    ).getByRole('status'),
  ).toHaveTextContent('"page":2,"zoom":1.5');
  await user.click(screen.getByRole('button', { name: 'Выбрать Фото' }));
  expect(screen.getByRole('button', { name: 'Выбрать Фото' })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
  expect(screen.getAllByTestId('heavy')).toHaveLength(2);
});
it('study narrow starts compact, expands inline and arbitrates all renderers with fullscreen', async () => {
  viewport.desktop = false;
  const { user, router } = studyShow();
  expect(screen.queryAllByTestId('heavy')).toHaveLength(0);
  await user.click(screen.getByRole('button', { name: 'Развернуть конспект' }));
  const material = screen.getByRole('region', { name: 'Просмотр: конспект' });
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  await user.click(
    within(material).getByRole('button', { name: 'Открыть крупно' }),
  );
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
  expect(router.state.location.search).toBe('?limit=50&material-file=11');
  await user.click(screen.getByRole('button', { name: 'Закрыть' }));
  await waitFor(() => expect(router.state.location.search).toBe('?limit=50'));
  expect(screen.getAllByTestId('heavy')).toHaveLength(1);
});
