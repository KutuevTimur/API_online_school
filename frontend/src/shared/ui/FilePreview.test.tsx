import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import { beforeEach, expect, it, vi } from 'vitest';
import { FilePreviewBody } from './FilePreview';
import type { FileDescriptor } from '../api/files';
const { fetchFile, load, destroy, getPage, cancel, cleanups, resizeRef } =
  vi.hoisted(() => ({
    fetchFile: vi.fn(),
    resizeRef: vi.fn(),
    load: vi.fn(),
    destroy: vi.fn(),
    getPage: vi.fn(),
    cancel: vi.fn(),
    cleanups: new Set<() => void>(),
  }));
vi.mock('../api/files', async (original) => ({
  ...(await original<object>()),
  fetchFile,
}));
vi.mock('../../features/auth/session', () => ({
  session: {
    cleanup: (fn: () => void) => {
      cleanups.add(fn);
      return () => cleanups.delete(fn);
    },
  },
}));
vi.mock('@mantine/hooks', async (original) => ({
  ...(await original<object>()),
  useResizeObserver: function useResizeObserver() {
    return [resizeRef, { width: 420, height: 280 }];
  },
}));
vi.mock('pdfjs-dist', () => ({
  GlobalWorkerOptions: {},
  AnnotationMode: { DISABLE: 0 },
  getDocument: load,
  TextLayer: class {
    render = () => Promise.resolve();
    cancel = cancel;
  },
}));
const file = {
  id: 1,
  download_url: '/submissions/12/files/1?homework_id=5',
  display_name: 'Решение.pdf',
} as FileDescriptor;
beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(window, 'devicePixelRatio', {
    configurable: true,
    value: 1,
  });
  Element.prototype.scrollTo = function (options?: ScrollToOptions | number) {
    if (options && typeof options !== 'number') {
      this.scrollTop = options.top || 0;
      this.scrollLeft = options.left || 0;
    }
  };
  cleanups.clear();
  URL.createObjectURL = vi.fn(() => 'blob:preview');
  URL.revokeObjectURL = vi.fn();
  getPage.mockResolvedValue({
    getViewport: ({ scale }: { scale: number }) => ({
      width: 600 * scale,
      height: 800 * scale,
    }),
    render: () => ({ promise: Promise.resolve(), cancel }),
    getTextContent: () => Promise.resolve({ items: [] }),
    cleanup: vi.fn(),
  });
  load.mockReturnValue({
    promise: Promise.resolve({ numPages: 3, getPage }),
    destroy,
  });
});
function show(onClose = vi.fn()) {
  return render(
    <MantineProvider env="test">
      <FilePreviewBody
        embedded
        file={file}
        files={[file]}
        index={0}
        onIndexChange={() => {}}
        onClose={onClose}
      />
    </MantineProvider>,
  );
}
it('shares one lazy PDF pipeline, fits the container and fetches pages on demand; destroys on unmount', async () => {
  fetchFile.mockResolvedValue({
    type: 'application/pdf',
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
  });
  const view = show();
  await waitFor(() =>
    expect(screen.getByLabelText('Страница 1')).toHaveAttribute('width', '420'),
  );
  expect(load).toHaveBeenCalledTimes(1);
  expect(load.mock.calls[0][0]).toMatchObject({
    enableXfa: false,
    useSystemFonts: false,
  });
  expect(
    screen.queryByRole('button', { name: 'Следующая страница' }),
  ).not.toBeInTheDocument();
  await userEvent.click(
    await screen.findByRole('button', { name: 'Увеличить' }),
  );
  await waitFor(() =>
    expect(screen.getByLabelText('Страница 1')).toHaveAttribute('width', '525'),
  );
  expect(fetchFile).toHaveBeenCalledTimes(1);
  view.rerender(
    <MantineProvider env="test">
      <FilePreviewBody
        embedded
        file={{ ...file, display_name: 'Уточнённое название.pdf' }}
        files={[file]}
        index={0}
        onIndexChange={() => {}}
        onClose={() => {}}
      />
    </MantineProvider>,
  );
  await waitFor(() =>
    expect(screen.getByLabelText('Страница 1')).toHaveAttribute('width', '525'),
  );
  expect(fetchFile).toHaveBeenCalledTimes(1);
  const signal = fetchFile.mock.calls[0][1] as AbortSignal;
  view.unmount();
  expect(signal.aborted).toBe(true);
  expect(destroy).toHaveBeenCalledTimes(1);
  expect(cancel).toHaveBeenCalled();
});
it('does not create a PDF task after a delayed buffer resolves following unmount', async () => {
  let release!: (value: ArrayBuffer) => void;
  const buffer = vi.fn(
    () =>
      new Promise<ArrayBuffer>((resolve) => {
        release = resolve;
      }),
  );
  fetchFile.mockResolvedValue({ type: 'application/pdf', arrayBuffer: buffer });
  const view = show();
  await waitFor(() => expect(buffer).toHaveBeenCalled());
  view.unmount();
  await act(async () => release(new ArrayBuffer(8)));
  expect(load).not.toHaveBeenCalled();
});
it('revokes image URLs and aborts on session cleanup; retains retry/download on failed preview', async () => {
  fetchFile
    .mockRejectedValueOnce(new Error('broken'))
    .mockResolvedValueOnce({ type: 'image/webp' });
  const close = vi.fn(),
    view = show(close);
  await screen.findByRole('alert');
  expect(screen.getByRole('button', { name: 'Скачать файл' })).toBeEnabled();
  await userEvent.click(
    screen.getByRole('button', { name: 'Повторить просмотр' }),
  );
  await screen.findByRole('img', { name: 'Решение.pdf' });
  expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
  act(() => cleanups.forEach((fn) => fn()));
  expect(close).toHaveBeenCalledOnce();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview');
  expect((fetchFile.mock.calls.at(-1)![1] as AbortSignal).aborted).toBe(true);
  view.unmount();
});

it('keeps 100-page geometry but releases distant canvases and preserves the fractional reading anchor on zoom', async () => {
  fetchFile.mockResolvedValue({
    type: 'application/pdf',
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
  });
  load.mockReturnValue({
    promise: Promise.resolve({ numPages: 100, getPage }),
    destroy,
  });
  const view = show();
  await waitFor(() =>
    expect(view.container.querySelectorAll('[data-pdf-page]')).toHaveLength(
      100,
    ),
  );
  expect(view.container.querySelectorAll('canvas').length).toBeLessThan(8);
  const root = screen.getByLabelText('Область просмотра файла');
  // Page 51, halfway down its 560px height; each slot adds a 16px gap.
  root.scrollTop = 50 * 576 + 280;
  fireEvent.scroll(root);
  await waitFor(() =>
    expect(screen.getByLabelText('Страница 51')).toHaveAttribute(
      'width',
      '420',
    ),
  );
  expect(screen.queryByLabelText('Страница 1')).toBeNull();
  expect(view.container.querySelectorAll('canvas').length).toBeLessThan(8);
  await userEvent.click(
    await screen.findByRole('button', { name: 'Увеличить' }),
  );
  await waitFor(() => expect(root.scrollTop).toBe(50 * 716 + 350));
  expect(fetchFile).toHaveBeenCalledTimes(1);
});
it('isolates a failed page without hiding its neighbours', async () => {
  fetchFile.mockResolvedValue({
    type: 'application/pdf',
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
  });
  const good = await getPage();
  getPage.mockImplementation((page: number) =>
    page === 2 ? Promise.reject(new Error('bad page')) : Promise.resolve(good),
  );
  show();
  await screen.findByRole('alert');
  expect(screen.getByLabelText('Страница 1')).toBeInTheDocument();
  expect(screen.getByLabelText('Страница 3')).toBeInTheDocument();
  getPage.mockResolvedValue(good);
  await userEvent.click(
    screen.getByRole('button', { name: 'Повторить страницу 2' }),
  );
  await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
  expect(fetchFile).toHaveBeenCalledTimes(1);
});

it('uses high-DPI backing pixels and caps each large canvas at four megapixels', async () => {
  Object.defineProperty(window, 'devicePixelRatio', {
    configurable: true,
    value: 2,
  });
  fetchFile.mockResolvedValue({
    type: 'application/pdf',
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
  });
  show();
  const canvas = (await screen.findByLabelText(
    'Страница 1',
  )) as HTMLCanvasElement;
  await waitFor(() => expect(canvas.width).toBe(840));
  expect(canvas.style.width).toBe('420px');
  for (let i = 0; i < 8; i++)
    await userEvent.click(screen.getByRole('button', { name: 'Увеличить' }));
  await waitFor(() =>
    expect(
      parseFloat(screen.getByLabelText('Страница 1').style.width),
    ).toBeCloseTo(1260),
  );
  const large = screen.getByLabelText('Страница 1') as HTMLCanvasElement;
  expect(large.width * large.height).toBeLessThan(4_010_000);
});

it('pinches in both directions and cancels without changing zoom; single-finger scrolling stays native', async () => {
  fetchFile.mockResolvedValue({
    type: 'application/pdf',
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
  });
  show();
  await waitFor(() =>
    expect(screen.getByLabelText('Страница 1')).toHaveAttribute('width', '420'),
  );
  const root = screen.getByLabelText('Область просмотра файла');
  const points = (distance: number) => [
    { clientX: 100, clientY: 100 },
    { clientX: 100 + distance, clientY: 100 },
  ];
  fireEvent.touchStart(root, { touches: points(100) });
  fireEvent.touchMove(root, { touches: points(150) });
  expect(root.firstElementChild).toHaveStyle({
    transform: 'translate(25px, 0px) scale(1.5)',
  });
  fireEvent.touchEnd(root, { touches: [] });
  await waitFor(() =>
    expect(screen.getByLabelText('Страница 1')).toHaveAttribute('width', '630'),
  );
  fireEvent.touchStart(root, { touches: points(150) });
  fireEvent.touchMove(root, { touches: points(100) });
  fireEvent.touchEnd(root, { touches: [] });
  await waitFor(() =>
    expect(screen.getByLabelText('Страница 1')).toHaveAttribute('width', '420'),
  );
  fireEvent.touchStart(root, { touches: points(100) });
  fireEvent.touchMove(root, { touches: points(200) });
  fireEvent.touchCancel(root, { touches: [] });
  expect((root.firstElementChild as HTMLElement).style.transform).toBe('');
  expect(screen.getByLabelText('Страница 1')).toHaveAttribute('width', '420');
  expect(
    fireEvent.touchStart(root, { touches: [{ clientX: 100, clientY: 100 }] }),
  ).toBe(true);
  expect(fetchFile).toHaveBeenCalledTimes(1);
});

it('uses the same pinch controls for a photo without creating a PDF pipeline', async () => {
  fetchFile.mockResolvedValue({ type: 'image/webp' });
  show();
  const photo = await screen.findByRole('img');
  const root = screen.getByLabelText('Область просмотра файла');
  fireEvent.touchStart(root, {
    touches: [
      { clientX: 100, clientY: 100 },
      { clientX: 200, clientY: 100 },
    ],
  });
  fireEvent.touchMove(root, {
    touches: [
      { clientX: 75, clientY: 100 },
      { clientX: 225, clientY: 100 },
    ],
  });
  fireEvent.touchEnd(root, { touches: [] });
  expect(photo).toHaveStyle({ width: '150%' });
  expect(load).not.toHaveBeenCalled();
});
