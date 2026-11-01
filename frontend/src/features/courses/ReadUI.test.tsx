import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router';
import { expect, it, vi } from 'vitest';
import { Providers } from '../../app/providers';
import type { FileDescriptor } from '../../shared/api/files';
import { ReadFiles } from './ReadUI';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';

// Exercise route behavior without PDF.js/network; native modal focus is E2E-tested.
vi.mock('../../shared/ui/FilePreview', () => ({
  FilePreview: ({
    index,
    onClose,
    onIndexChange,
  }: {
    index: number;
    onClose: () => void;
    onIndexChange: (i: number) => void;
  }) =>
    index >= 0 ? (
      <div role="dialog">
        <button onClick={() => onIndexChange(1)}>Следующий файл</button>
        <button onClick={onClose}>Закрыть</button>
      </div>
    ) : null,
}));
const files = [
  { id: 11, display_name: 'PDF' },
  { id: 12, display_name: 'Фото' },
] as FileDescriptor[];
const state = {
  returnTo: '/teacher/schedule?week=2026-10-19',
  studentListSearch: 'synthetic search',
};
const search = '?week=2026-10-19&student=7&view=all&limit=50&offset=20';
function Scene() {
  const location = useLocation();
  return (
    <>
      <DirtyFormGuard dirty allowPreviewQuery />
      <output>{JSON.stringify(location.state)}</output>
      <ReadFiles files={files} />
      <ReadFiles files={files} condition />
      <ReadFiles files={files} review />
      <ReadFiles files={files} material />
      <ReadFiles files={files} owner="latest-lectures" />
      <ReadFiles files={files} owner="history-9-lectures" />
      <ReadFiles
        files={[files[0]]}
        material
        owner="compact-latest"
        singleFileLabel="Конспект"
      />
    </>
  );
}
function show(initialSearch = search) {
  const router = createMemoryRouter(
    [
      { path: '/list', element: <p>Список</p> },
      { path: '/lesson', element: <Scene /> },
    ],
    {
      initialEntries: [
        '/list',
        { pathname: '/lesson', search: initialSearch, state },
      ],
      initialIndex: 1,
    },
  );
  render(
    <Providers>
      <RouterProvider router={router} />
    </Providers>,
  );
  return router;
}
it.each(['file', 'condition-file', 'review-file', 'material-file'])(
  'preserves context and consumes open/close history with dirty form: %s',
  async (param) => {
    const router = show();
    const user = userEvent.setup();
    const i = [
      'file',
      'condition-file',
      'review-file',
      'material-file',
    ].indexOf(param);
    await user.click(screen.getAllByRole('button', { name: 'Открыть PDF' })[i]);
    expect(router.state.location.search).toBe(search + `&${param}=11`);
    expect(router.state.location.state).toEqual(state);
    await user.click(screen.getByRole('button', { name: 'Следующий файл' }));
    expect(router.state.location.search).toBe(search + `&${param}=12`);
    await user.click(screen.getByRole('button', { name: 'Закрыть' }));
    await waitFor(() => expect(router.state.location.search).toBe(search));
    expect(router.state.location.state).toEqual(state);
    expect(screen.queryByRole('dialog')).toBeNull();
    // Back to a different page still prompts; preview must not bypass real dirty navigation.
    void router.navigate(-1);
    expect(
      await screen.findByRole('dialog', { name: 'Уйти без сохранения?' }),
    ).toBeInTheDocument();
  },
);
it('closes a direct preview URL in place and keeps all route state', async () => {
  const router = show(search + '&file=11');
  await userEvent
    .setup()
    .click(screen.getByRole('button', { name: 'Закрыть' }));
  await waitFor(() => expect(router.state.location.search).toBe(search));
  expect(router.state.location.state).toEqual(state);
});

it('opens one viewer when the same file appears in latest lesson and history, preserving dirty form context', async () => {
  const router = show();
  const user = userEvent.setup();
  await user.click(screen.getAllByRole('button', { name: 'Открыть PDF' })[5]);
  expect(screen.getAllByRole('dialog')).toHaveLength(1);
  expect(router.state.location.search).toContain(
    'file-owner=history-9-lectures',
  );
  await user.click(screen.getByRole('button', { name: 'Закрыть' }));
  await waitFor(() => expect(router.state.location.search).toBe(search));
  await user.click(screen.getAllByRole('button', { name: 'Открыть PDF' })[4]);
  expect(screen.getAllByRole('dialog')).toHaveLength(1);
  expect(router.state.location.search).toContain('file-owner=latest-lectures');
});

it('compact single-file label uses the same owner-aware viewer and preserves URL/Back', async () => {
  const router = show();
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: 'Конспект' }));
  expect(router.state.location.search).toContain('material-file=11');
  expect(router.state.location.search).toContain('file-owner=compact-latest');
  expect(screen.getAllByRole('dialog')).toHaveLength(1);
  await user.click(screen.getByRole('button', { name: 'Закрыть' }));
  await waitFor(() => expect(router.state.location.search).toBe(search));
  expect(router.state.location.state).toEqual(state);
});
