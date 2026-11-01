import { useId, useRef, useState, type ReactNode } from 'react';
import { useMediaQuery } from '@mantine/hooks';
import type { UseQueryResult } from '@tanstack/react-query';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router';
import { Button, Group } from '@mantine/core';
import { FileText } from 'lucide-react';
import { AsyncState } from '../../shared/ui/AsyncState';
import { Pagination } from '../../shared/ui/Pagination';
import { ApiError } from '../../shared/api/error';
import { readOnlyReason } from '../../shared/lib/datetime';
import {
  FilePreview,
  FilePreviewBody,
  type FileViewState,
} from '../../shared/ui/FilePreview';
import fileStyles from '../../shared/ui/files.module.css';
import type { FileDescriptor } from '../../shared/api/files';
import styles from './read.module.css';
import { useSession, home } from '../auth/session';
export function ReadState<T>({
  query,
  children,
}: {
  query: UseQueryResult<T>;
  children: (data: T) => ReactNode;
}) {
  const auth = useSession();
  if (query.isPending) return <AsyncState kind="loading" />;
  if (query.isError && query.data === undefined)
    return (
      <AsyncState kind="error" onRetry={() => void query.refetch()}>
        <p>
          {query.error instanceof ApiError
            ? query.error.message
            : 'Попробуйте ещё раз'}
        </p>
        <Link to={auth.user ? home(auth.user) : '/login'}>
          {auth.user?.role === 'student' ? 'В мой день' : 'В свой кабинет'}
        </Link>
      </AsyncState>
    );
  return (
    <>
      {query.isFetching && <p role="status">Обновляем…</p>}
      {query.isError && (
        <p role="alert">
          Не удалось обновить данные. Показана последняя загруженная версия.{' '}
          <Button variant="default" onClick={() => void query.refetch()}>
            Повторить обновление
          </Button>
        </p>
      )}
      {children(query.data!)}
    </>
  );
}
export function ReadOnly({
  mode,
  reason,
}: {
  mode?: string;
  reason?: string | null;
}) {
  return mode === 'read_only' ? (
    <p className={styles.readonly} role="status">
      Только просмотр: {readOnlyReason(reason)}. Материалы и история доступны
      для чтения и скачивания.
    </p>
  ) : null;
}
export function useListState(prefix = '') {
  const location = useLocation();
  const [params, set] = useSearchParams();
  const limit: 20 | 50 = params.get(prefix + 'limit') === '50' ? 50 : 20;
  const raw = Number(params.get(prefix + 'offset'));
  const offset = Number.isSafeInteger(raw) && raw >= 0 ? raw : 0;
  const view = ['active', 'archive', 'all'].includes(
    params.get(prefix + 'view') || '',
  )
    ? params.get(prefix + 'view')!
    : 'active';
  const update = (values: Record<string, string | number>) => {
    const next = new URLSearchParams(params);
    Object.entries(values).forEach(([key, value]) =>
      next.set(prefix + key, String(value)),
    );
    set(next, { state: location.state });
  };
  return { params, view, limit, offset, update };
}
export function Views({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <Group
      mb="md"
      gap="xs"
      className={styles.viewFilters}
      aria-label="Раздел списка"
    >
      {[
        ['active', 'Активные'],
        ['archive', 'Архив'],
        ['all', 'Все'],
      ].map(([id, label]) => (
        <Button
          key={id}
          variant={id === value ? 'filled' : 'default'}
          aria-pressed={id === value}
          onClick={() => onChange(id)}
        >
          {label}
        </Button>
      ))}
    </Group>
  );
}
export function Pages({
  total,
  state,
  label,
}: {
  label?: string;
  total: number;
  state: ReturnType<typeof useListState>;
}) {
  if (total <= state.limit && state.offset === 0) return null;
  return (
    <>
      <p className={styles.muted}>Всего: {total}</p>
      <Pagination
        label={label}
        total={total}
        limit={state.limit}
        offset={state.offset}
        onChange={(offset, limit) => state.update({ offset, limit })}
      />
    </>
  );
}
export function ReadFiles({
  files,
  condition = false,
  review = false,
  material = false,
  embedded = false,
  studyLabel,
  initiallyCollapsed = false,
  singleFileLabel,
  owner,
}: {
  files: FileDescriptor[];
  condition?: boolean;
  review?: boolean;
  material?: boolean;
  embedded?: boolean;
  studyLabel?: string;
  initiallyCollapsed?: boolean;
  singleFileLabel?: string;
  owner?: string;
}) {
  const previewParam = material
    ? 'material-file'
    : review
      ? 'review-file'
      : condition
        ? 'condition-file'
        : 'file';
  const [params, set] = useSearchParams();
  const previewKeys = [
    'file',
    'condition-file',
    'review-file',
    'material-file',
  ];
  const activePreview = [...params.keys()]
    .filter((key) => previewKeys.includes(key))
    .at(-1);
  const index =
    activePreview === previewParam &&
    params.get('file-owner') === (owner ?? null)
      ? files.findIndex((file) => String(file.id) === params.get(previewParam))
      : -1;
  const studyRegion = useId();
  const desktop = useMediaQuery('(min-width: 1024px)');
  const [studyOpen, setStudyOpen] = useState<boolean>();
  const expanded = studyOpen ?? (initiallyCollapsed ? false : desktop);
  const [selectedId, setSelectedId] = useState<number>();
  const [stopped, setStopped] = useState(false);
  const [views, setViews] = useState<Record<number, FileViewState>>({});
  const selectedIndex =
    index >= 0
      ? index
      : Math.max(
          0,
          files.findIndex((f) => f.id === selectedId),
        );
  const selected = files[selectedIndex];
  const changeView = (id: number, state: FileViewState) =>
    setViews((previous) => ({ ...previous, [id]: state }));
  const location = useLocation();
  const navigate = useNavigate();
  const origin = useRef<string | null>(null);
  const open = (index: number, replace = false) => {
    if (!replace) origin.current = location.key;
    const next = new URLSearchParams(params);
    if (index < 0) {
      next.delete(previewParam);
      next.delete('file-owner');
    } else {
      setSelectedId(files[index].id);
      setStopped(false);
      // A page owns one fullscreen preview, including direct multi-key URLs.
      for (const key of previewKeys) next.delete(key);
      if (owner) next.set('file-owner', owner);
      else next.delete('file-owner');
      next.set(previewParam, String(files[index].id));
    }
    set(next, {
      replace,
      state: location.state,
      preventScrollReset: true,
    });
  };
  const close = () => {
    if (index >= 0) setSelectedId(files[index].id);
    // Consume the entry created by opening; direct preview URLs have no origin.
    if (origin.current && origin.current !== location.key) {
      origin.current = null;
      void navigate(-1);
    } else open(-1, true);
  };
  return (
    <>
      {studyLabel && files.length > 0 && (
        <Button
          variant="default"
          className={styles.fileButton}
          aria-expanded={expanded}
          aria-controls={studyRegion}
          onClick={() => {
            setStudyOpen(!expanded);
            setStopped(false);
          }}
        >
          {expanded ? 'Свернуть' : 'Развернуть'} {studyLabel}
        </Button>
      )}
      <div id={studyRegion} hidden={!!studyLabel && !expanded}>
        {(!studyLabel || files.length > 1) && (
          <div className={styles.fileList}>
            {files.map((file, i) => (
              <Button
                className={styles.fileButton}
                key={file.id}
                variant="default"
                leftSection={
                  singleFileLabel && files.length === 1 ? (
                    <FileText size={18} aria-hidden="true" />
                  ) : undefined
                }
                aria-pressed={studyLabel ? selectedIndex === i : undefined}
                onClick={() => {
                  if (studyLabel) {
                    setSelectedId(file.id);
                    setStopped(false);
                  } else open(i);
                }}
              >
                {singleFileLabel && files.length === 1
                  ? singleFileLabel
                  : `${studyLabel ? 'Выбрать' : 'Открыть'} ${file.display_name}`}
              </Button>
            ))}
          </div>
        )}
        {(studyLabel ? expanded : embedded && desktop) && selected && (
          <section
            className={fileStyles.embedded}
            aria-label={
              studyLabel ? `Просмотр: ${studyLabel}` : 'Просмотр файла решения'
            }
          >
            <div className={fileStyles.previewHeading}>
              <strong>{selected.display_name}</strong>
              <Button variant="default" onClick={() => open(selectedIndex)}>
                Открыть крупно
              </Button>
            </div>
            {!activePreview && !stopped ? (
              <FilePreviewBody
                key={`${selected.id}:${selected.download_url}`}
                embedded
                viewportLabel={
                  studyLabel ? `Область просмотра: ${studyLabel}` : undefined
                }
                file={selected}
                files={files}
                index={selectedIndex}
                onIndexChange={(i) => {
                  setSelectedId(files[i].id);
                  setStopped(false);
                }}
                onClose={() => setStopped(true)}
                viewState={views[selected.id]}
                onViewChange={(state) => changeView(selected.id, state)}
              />
            ) : (
              <div className={fileStyles.previewPlaceholder}>
                {stopped ? (
                  <Button variant="default" onClick={() => setStopped(false)}>
                    Повторить просмотр
                  </Button>
                ) : (
                  <p>
                    Встроенный просмотр приостановлен, пока файл открыт крупно.
                  </p>
                )}
              </div>
            )}
          </section>
        )}
      </div>
      <FilePreview
        files={files}
        index={index}
        onIndexChange={(i) => open(i, true)}
        onClose={close}
        viewState={index >= 0 ? views[files[index].id] : undefined}
        onViewChange={
          index >= 0 ? (state) => changeView(files[index].id, state) : undefined
        }
      />
    </>
  );
}
