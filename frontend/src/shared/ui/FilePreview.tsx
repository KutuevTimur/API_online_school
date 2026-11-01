import { useModalIsolation } from '../lib/modalIsolation';
import {
  useLayoutEffect,
  useMemo,
  useCallback,
  useEffect,
  useEffectEvent,
  useRef,
  useState,
} from 'react';
import {
  ActionIcon,
  Button,
  Modal,
  Tooltip,
  VisuallyHidden,
} from '@mantine/core';
import { Download, Minus, Plus, X } from 'lucide-react';
import type { RefObject } from 'react';
import { useResizeObserver } from '@mantine/hooks';
import { session } from '../../features/auth/session';
import { fetchFile, type FileDescriptor } from '../api/files';
import { ApiError } from '../api/error';
import styles from './files.module.css';
import type { PDFDocumentProxy } from 'pdfjs-dist';
let pdfjsModule: Promise<typeof import('pdfjs-dist')> | undefined;
const loadPdfJs = () =>
  (pdfjsModule ??= import('pdfjs-dist').catch((error) => {
    pdfjsModule = undefined;
    throw error;
  }));
type PinchAnchor = {
  selector: string;
  x: number;
  y: number;
  screenX: number;
  screenY: number;
};
function restorePinch(
  root: HTMLDivElement,
  pending: RefObject<PinchAnchor | null>,
) {
  const anchor = pending.current;
  if (!anchor) return false;
  const target = root.querySelector<HTMLElement>(anchor.selector);
  pending.current = null;
  if (!target) return false;
  root.scrollTo({
    left: target.offsetLeft + target.offsetWidth * anchor.x - anchor.screenX,
    top: target.offsetTop + target.offsetHeight * anchor.y - anchor.screenY,
    behavior: 'instant',
  });
  return true;
}
function PdfPage({
  document,
  page,
  zoom,
  width,
}: {
  document: PDFDocumentProxy;
  page: number;
  zoom: number;
  width: number;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const text = useRef<HTMLDivElement>(null);
  const [rendering, setRendering] = useState(true);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let cancelled = false;
    let render: { cancel: () => void } | undefined;
    let layer: { cancel: () => void } | undefined;
    let currentPage:
      Awaited<ReturnType<PDFDocumentProxy['getPage']>> | undefined;
    const target = canvas.current!;
    const container = text.current!;
    container.replaceChildren();
    void (async () => {
      setRendering(true);
      setFailed(false);
      const pdfjs = await loadPdfJs();
      const current = await document.getPage(page);
      if (cancelled) return;
      currentPage = current;
      const base = current.getViewport({ scale: 1 });
      const scale = Math.min(1, Math.max(1, width) / base.width) * zoom;
      const viewport = current.getViewport({ scale });
      // Keep text crisp on high-DPI screens without allocating unbounded bitmaps.
      const ratio = Math.min(
        window.devicePixelRatio || 1,
        2,
        Math.sqrt(4_000_000 / (viewport.width * viewport.height)),
      );
      target.width = Math.ceil(viewport.width * ratio);
      target.height = Math.ceil(viewport.height * ratio);
      target.style.width = `${viewport.width}px`;
      target.style.height = `${viewport.height}px`;
      container.style.width = `${viewport.width}px`;
      container.style.height = `${viewport.height}px`;
      container.style.setProperty('--total-scale-factor', String(scale));
      const task = current.render({
        canvas: target,
        viewport,
        transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
        annotationMode: pdfjs.AnnotationMode.DISABLE,
      });
      render = task;
      await task.promise;
      if (cancelled) return;
      const content = await current.getTextContent();
      if (cancelled) return;
      const textLayer = new pdfjs.TextLayer({
        textContentSource: content,
        container,
        viewport,
      });
      layer = textLayer;
      await textLayer.render();
      if (!cancelled) setRendering(false);
    })().catch(() => {
      if (!cancelled) {
        setRendering(false);
        setFailed(true);
      }
    });
    return () => {
      cancelled = true;
      render?.cancel();
      layer?.cancel();
      container.replaceChildren();
      target.width = target.height = 0;
      // PDF.js defers cleanup while a cancelled render is still settling.
      currentPage?.cleanup();
    };
  }, [document, page, zoom, width, attempt]);
  return (
    <div
      className={styles.page}
      style={{ width: 'max-content' }}
      aria-busy={rendering}
    >
      {rendering && (
        <p className={styles.renderStatus} role="status">
          Готовим страницу {page}…
        </p>
      )}
      {failed && (
        <div className={styles.renderStatus} role="alert">
          <p>
            Не удалось показать страницу {page}. Остальные страницы доступны.
          </p>
          <Button
            variant="default"
            onClick={() => setAttempt((value) => value + 1)}
          >
            Повторить страницу {page}
          </Button>
        </div>
      )}
      <canvas ref={canvas} aria-label={`Страница ${page}`} />
      <div ref={text} className={styles.textLayer} />
    </div>
  );
}
export type FileViewState = {
  page: number;
  zoom: number;
  offset?: number;
  left?: number;
};

function pageGeometry(
  sizes: { width: number; height: number }[],
  width: number,
  zoom: number,
) {
  let top = 0;
  return sizes.map((size) => {
    const scale = Math.min(1, Math.max(1, width) / size.width) * zoom;
    const item = {
      top,
      width: size.width * scale,
      height: size.height * scale,
    };
    top += item.height + 16;
    return item;
  });
}

// Only geometry is retained for distant pages. Canvases and text layers live near
// the viewport; selected/focused pages stay mounted until the user releases them.
function PdfPages({
  document,
  width,
  viewport,
  view,
  onChange,
  pinchAnchor,
}: {
  pinchAnchor: RefObject<PinchAnchor | null>;
  document: PDFDocumentProxy;
  width: number;
  viewport: RefObject<HTMLDivElement | null>;
  view: FileViewState;
  onChange: (view: FileViewState) => void;
}) {
  const [sizes, setSizes] = useState<{ width: number; height: number }[]>([]);
  const [top, setTop] = useState(0);
  const [pinned, setPinned] = useState<number[]>([]);
  const [geometryError, setGeometryError] = useState(false);
  const saved = useRef(view);
  const change = useEffectEvent(onChange);
  useEffect(() => {
    let dead = false;
    void (async () => {
      const result = [];
      for (let page = 1; page <= document.numPages; page++) {
        try {
          const current = await document.getPage(page);
          if (dead) return;
          const size = current.getViewport({ scale: 1 });
          result.push({ width: size.width, height: size.height });
          current.cleanup();
        } catch {
          // A broken page must not hide the rest of the document.
          result.push({ width: 600, height: 800 });
        }
      }
      if (!dead) setSizes(result);
    })().catch(() => {
      if (!dead) setGeometryError(true);
    });
    return () => {
      dead = true;
    };
  }, [document]);
  const pages = useMemo(
    () => pageGeometry(sizes, width, view.zoom),
    [sizes, width, view.zoom],
  );
  // Restore by page + fractional offset, including embedded/fullscreen resize.
  useLayoutEffect(() => {
    const root = viewport.current;
    const anchor = pages[Math.min(saved.current.page, pages.length) - 1];
    if (!root || !anchor) return;
    if (!restorePinch(root, pinchAnchor))
      root.scrollTo({
        top: anchor.top + (saved.current.offset || 0) * anchor.height,
        left: (saved.current.left || 0) * root.scrollWidth,
        behavior: 'instant',
      });
    setTop(root.scrollTop);
  }, [pages, viewport, pinchAnchor]);
  const scroll = useEffectEvent(() => {
    const root = viewport.current;
    if (!root) return;
    let current = pages.length - 1;
    while (current >= 0 && pages[current].top > root.scrollTop + 1) current--;
    setTop(root.scrollTop);
    if (current < 0) return;
    saved.current = {
      page: current + 1,
      zoom: view.zoom,
      offset: (root.scrollTop - pages[current].top) / pages[current].height,
      left: root.scrollLeft / Math.max(1, root.scrollWidth),
    };
    change(saved.current);
  });
  useEffect(() => {
    const root = viewport.current;
    if (!root) return;
    const retain = () => {
      const selection = window.getSelection();
      const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
      setPinned(
        [...root.querySelectorAll<HTMLElement>('[data-pdf-page]')]
          .filter(
            (node) =>
              node.contains(window.document.activeElement) ||
              (!!range &&
                !!node.querySelector('canvas') &&
                !selection?.isCollapsed &&
                range.intersectsNode(node)),
          )
          .map((node) => Number(node.dataset.pdfPage)),
      );
    };
    const onScroll = () => scroll();
    root.addEventListener('scroll', onScroll);
    window.document.addEventListener('selectionchange', retain);
    root.addEventListener('focusin', retain);
    root.addEventListener('focusout', retain);
    return () => {
      root.removeEventListener('scroll', onScroll);
      window.document.removeEventListener('selectionchange', retain);
      root.removeEventListener('focusin', retain);
      root.removeEventListener('focusout', retain);
    };
  }, [viewport]);
  const height = viewport.current?.clientHeight || 800;
  return (
    <>
      {!sizes.length && <p role="status">Готовим страницы…</p>}
      {geometryError && (
        <p role="alert">
          Не удалось открыть документ. Повторите просмотр или скачайте PDF.
        </p>
      )}
      {pages.map((size, index) => (
        <div
          key={index}
          data-pdf-page={index + 1}
          className={styles.pageSlot}
          style={{ width: size.width, height: size.height }}
        >
          {((size.top + size.height >= top - height &&
            size.top <= top + height * 2) ||
            pinned.includes(index + 1)) && (
            <PdfPage
              key={`${view.zoom}:${width}`}
              document={document}
              page={index + 1}
              zoom={view.zoom}
              width={width}
            />
          )}
        </div>
      ))}
    </>
  );
}
export function FilePreview({
  files,
  index,
  onIndexChange,
  onClose,
  viewState,
  onViewChange,
}: {
  files: FileDescriptor[];
  index: number;
  onIndexChange: (index: number) => void;
  onClose: () => void;
  viewState?: FileViewState;
  onViewChange?: (state: FileViewState) => void;
}) {
  const file = files[index];
  useModalIsolation(!!file);
  // Keyed content ensures every file has independent page/zoom/error state.
  return (
    <Modal.Root
      opened={!!file}
      onClose={onClose}
      fullScreen
      classNames={{ content: styles.modalContent }}
      zIndex="var(--lgg-z-preview)"
    >
      <Modal.Overlay />
      <Modal.Content aria-label={file?.display_name || 'Файл'}>
        <Modal.Body className={styles.modalBody}>
          {file && (
            <FilePreviewBody
              key={`${file.id}:${file.download_url}`}
              file={file}
              files={files}
              index={index}
              onIndexChange={onIndexChange}
              onClose={onClose}
              viewState={viewState}
              onViewChange={onViewChange}
            />
          )}
        </Modal.Body>
      </Modal.Content>
    </Modal.Root>
  );
}
export function FilePreviewBody({
  file,
  onClose,
  embedded = false,
  viewportLabel = 'Область просмотра файла',
  viewState,
  onViewChange,
}: {
  file: FileDescriptor;
  files: FileDescriptor[];
  index: number;
  onIndexChange: (index: number) => void;
  onClose: () => void;
  embedded?: boolean;
  viewportLabel?: string;
  viewState?: FileViewState;
  onViewChange?: (state: FileViewState) => void;
}) {
  const [viewport, dimensions] = useResizeObserver<HTMLDivElement>();
  const scrollport = useRef<HTMLDivElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const pinchAnchor = useRef<PinchAnchor | null>(null);
  const attachViewport = useCallback(
    (node: HTMLDivElement | null) => {
      scrollport.current = node;
      viewport(node);
    },
    [viewport],
  );
  const [blob, setBlob] = useState<Blob>();
  const [url, setUrl] = useState('');
  const [document, setDocument] = useState<PDFDocumentProxy>();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [localView, setLocalView] = useState<FileViewState>({
    page: 1,
    zoom: 1,
  });
  const currentView = viewState || localView;
  const { zoom } = currentView;
  const changeView = onViewChange || setLocalView;
  const setZoom = (zoom: number) => changeView({ ...currentView, zoom });
  const commitZoom = useEffectEvent(setZoom);
  const readZoom = useEffectEvent(() => zoom);
  useLayoutEffect(() => {
    if (url && scrollport.current)
      restorePinch(scrollport.current, pinchAnchor);
  }, [zoom, url]);
  useEffect(() => {
    const root = scrollport.current;
    const surface = content.current;
    if (!root || !surface) return;
    let gesture: {
      distance: number;
      zoom: number;
      scale: number;
      x: number;
      y: number;
      anchor: PinchAnchor | null;
    } | null = null;
    const points = (event: TouchEvent) => {
      const [a, b] = [event.touches[0], event.touches[1]];
      const rect = root.getBoundingClientRect();
      return {
        distance: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY),
        x: (a.clientX + b.clientX) / 2 - rect.left,
        y: (a.clientY + b.clientY) / 2 - rect.top,
      };
    };
    const start = (event: TouchEvent) => {
      if (event.touches.length !== 2 || gesture) return;
      const point = points(event);
      if (!point.distance) return;
      if (event.cancelable) event.preventDefault();
      const nodes = [
        ...root.querySelectorAll<HTMLElement>(
          '[data-pdf-page], [data-zoom-image]',
        ),
      ];
      const target =
        [...nodes]
          .reverse()
          .find((node) => node.offsetTop <= root.scrollTop + point.y) ||
        nodes[0];
      const anchor =
        target && target.offsetWidth && target.offsetHeight
          ? {
              selector: target.dataset.pdfPage
                ? `[data-pdf-page="${target.dataset.pdfPage}"]`
                : '[data-zoom-image]',
              x:
                (root.scrollLeft + point.x - target.offsetLeft) /
                target.offsetWidth,
              y:
                (root.scrollTop + point.y - target.offsetTop) /
                target.offsetHeight,
              screenX: point.x,
              screenY: point.y,
            }
          : null;
      gesture = { ...point, zoom: readZoom(), scale: 1, anchor };
      surface.style.transformOrigin = `${root.scrollLeft + point.x}px ${root.scrollTop + point.y}px`;
    };
    const move = (event: TouchEvent) => {
      if (!gesture || event.touches.length !== 2) return;
      if (event.cancelable) event.preventDefault();
      const point = points(event);
      const nextZoom = Math.min(
        3,
        Math.max(0.5, (gesture.zoom * point.distance) / gesture.distance),
      );
      gesture.scale = nextZoom / gesture.zoom;
      if (gesture.anchor) {
        gesture.anchor.screenX = point.x;
        gesture.anchor.screenY = point.y;
      }
      surface.style.transform = `translate(${point.x - gesture.x}px, ${point.y - gesture.y}px) scale(${gesture.scale})`;
    };
    const finish = (event: TouchEvent) => {
      if (!gesture || event.touches.length >= 2) return;
      const previous = gesture;
      gesture = null;
      surface.style.transform = '';
      surface.style.transformOrigin = '';
      if (event.type !== 'touchcancel') {
        pinchAnchor.current = previous.anchor;
        const next = previous.zoom * previous.scale;
        if (Math.abs(next - previous.zoom) < 0.00001)
          restorePinch(root, pinchAnchor);
        else commitZoom(next);
      }
    };
    root.addEventListener('touchstart', start, { passive: false });
    root.addEventListener('touchmove', move, { passive: false });
    root.addEventListener('touchend', finish);
    root.addEventListener('touchcancel', finish);
    return () => {
      root.removeEventListener('touchstart', start);
      root.removeEventListener('touchmove', move);
      root.removeEventListener('touchend', finish);
      root.removeEventListener('touchcancel', finish);
      surface.style.transform = '';
    };
  }, []);
  const [attempt, setAttempt] = useState(0);
  const close = useEffectEvent(onClose);
  const read = useEffectEvent((signal: AbortSignal) => fetchFile(file, signal));
  const generation = useRef(0);
  const downloadUrls = useRef(new Set<string>());
  const downloadController = useRef<AbortController | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    let dead = false;
    let objectUrl = '';
    let task: { destroy: () => Promise<void> } | undefined;

    const stop = () => {
      dead = true;
      controller.abort();
      downloadController.current?.abort();
      generation.current += 1;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      for (const value of downloadUrls.current) URL.revokeObjectURL(value);
      downloadUrls.current.clear();
      void task?.destroy();
    };
    const unregister = session.cleanup(() => {
      stop();
      close();
    });
    void read(controller.signal)
      .then(async (value) => {
        if (dead) return;
        setBlob(value);
        const mime = value.type.split(';')[0].toLowerCase();
        if (mime === 'application/pdf') {
          const pdfjs = await loadPdfJs();
          const worker =
            await import('pdfjs-dist/build/pdf.worker.min.mjs?url');
          if (dead) return;
          pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
          const data = new Uint8Array(await value.arrayBuffer());
          if (dead) return;
          const loadingTask = pdfjs.getDocument({
            data,
            enableXfa: false,
            cMapUrl: '/pdfjs/cmaps/',
            standardFontDataUrl: '/pdfjs/standard_fonts/',
            wasmUrl: '/pdfjs/wasm/',
            iccUrl: '/pdfjs/iccs/',
            useSystemFonts: false,
          });
          task = loadingTask;
          const pdf = await loadingTask.promise;
          if (!dead) setDocument(pdf);
        } else if (['image/jpeg', 'image/png', 'image/webp'].includes(mime)) {
          objectUrl = URL.createObjectURL(value);
          setUrl(objectUrl);
        } else setError('Этот формат не поддерживает просмотр. Скачайте файл.');
      })
      .catch((cause) => {
        if (!dead)
          setError(
            cause instanceof ApiError
              ? cause.message
              : 'Не удалось открыть PDF. Он повреждён или защищён паролем. Скачайте файл.',
          );
      })
      .finally(() => {
        if (!dead) setLoading(false);
      });
    return () => {
      stop();
      unregister();
    };
  }, [file.id, file.download_url, attempt]);
  async function download() {
    if (downloadBusy) return;
    setDownloadBusy(true);
    const current = generation.current;
    downloadController.current = new AbortController();
    try {
      const value =
        blob || (await fetchFile(file, downloadController.current.signal, 0));
      if (current !== generation.current) return;
      const target = URL.createObjectURL(value);
      downloadUrls.current.add(target);
      const link = window.document.createElement('a');
      link.href = target;
      link.download = file.display_name;
      link.click();
      // Keep the URL alive until the browser has consumed the click, then release it.
      window.setTimeout(() => {
        URL.revokeObjectURL(target);
        downloadUrls.current.delete(target);
      }, 1000);
    } catch {
      if (current === generation.current)
        setError('Не удалось скачать файл. Проверьте подключение и доступ.');
    } finally {
      if (current === generation.current) setDownloadBusy(false);
    }
  }
  return (
    <div
      className={embedded ? styles.embeddedBody : styles.fullscreenBody}
      data-file-viewer={embedded ? 'embedded' : 'fullscreen'}
    >
      <div
        className={styles.toolbar}
        role="group"
        aria-label="Управление просмотром"
      >
        <VisuallyHidden role="status">
          Масштаб {Math.round(zoom * 100)}%
        </VisuallyHidden>
        <Tooltip
          label="Уменьшить"
          withinPortal={false}
          transitionProps={{ duration: 0 }}
          events={{ hover: true, focus: true, touch: false }}
        >
          <ActionIcon
            size={44}
            variant="default"
            aria-label="Уменьшить"
            disabled={loading || zoom <= 0.5}
            onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
          >
            <Minus size={20} />
          </ActionIcon>
        </Tooltip>
        <Tooltip
          label="Увеличить"
          withinPortal={false}
          transitionProps={{ duration: 0 }}
          events={{ hover: true, focus: true, touch: false }}
        >
          <ActionIcon
            size={44}
            variant="default"
            aria-label="Увеличить"
            disabled={loading || zoom >= 3}
            onClick={() => setZoom(Math.min(3, zoom + 0.25))}
          >
            <Plus size={20} />
          </ActionIcon>
        </Tooltip>
        <Tooltip
          label="Скачать файл"
          withinPortal={false}
          transitionProps={{ duration: 0 }}
          events={{ hover: true, focus: true, touch: false }}
        >
          <ActionIcon
            size={44}
            variant="default"
            aria-label="Скачать файл"
            loading={downloadBusy}
            disabled={downloadBusy}
            onClick={() => void download()}
          >
            <Download size={20} />
          </ActionIcon>
        </Tooltip>
        {!embedded && (
          <Tooltip
            label="Закрыть просмотр"
            withinPortal={false}
            transitionProps={{ duration: 0 }}
            events={{ hover: true, focus: true, touch: false }}
          >
            <ActionIcon
              size={44}
              variant="default"
              aria-label="Закрыть просмотр"
              onClick={onClose}
            >
              <X size={20} />
            </ActionIcon>
          </Tooltip>
        )}
      </div>
      {loading && <p role="status">Загружаем файл…</p>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          <Button
            variant="default"
            onClick={() => {
              setLoading(true);
              setError('');
              setBlob(undefined);
              setUrl('');
              setDocument(undefined);
              setAttempt((value) => value + 1);
            }}
          >
            Повторить просмотр
          </Button>
          <p>
            Скачивание большого файла может потребовать больше памяти.
            Предпросмотр ограничен 20 МиБ.
          </p>
        </div>
      )}
      <div
        ref={attachViewport}
        className={styles.viewport}
        tabIndex={0}
        aria-busy={loading}
        role="region"
        aria-label={viewportLabel}
      >
        <div
          ref={content}
          className={styles.documentContent}
          style={url ? { width: '100%' } : undefined}
        >
          {url && (
            <img
              data-zoom-image
              className={styles.picture}
              src={url}
              alt={file.display_name}
              style={{ width: `${zoom * 100}%` }}
              onError={() =>
                setError('Фото не удалось открыть. Скачайте файл.')
              }
            />
          )}
          {document && dimensions.width > 0 && (
            <PdfPages
              document={document}
              width={dimensions.width}
              viewport={scrollport}
              view={currentView}
              onChange={changeView}
              pinchAnchor={pinchAnchor}
            />
          )}
        </div>
      </div>
    </div>
  );
}
