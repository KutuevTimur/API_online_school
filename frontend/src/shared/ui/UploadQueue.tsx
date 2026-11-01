import { useContext, useState, useSyncExternalStore } from 'react';
import { Button, Group, Progress, Stack, Text } from '@mantine/core';
import { DraftContext } from '../../app/DraftProvider';
import {
  acceptedFiles,
  answerFiles,
  type Answer,
  type UploadAdapter,
  type FileDescriptor,
} from '../api/files';
import { UploadQueueModel } from '../lib/uploadQueue';
import { ConflictCompare } from './ConflictCompare';
import { ConfirmDialog } from './ConfirmDialog';
import styles from './files.module.css';
export function UploadQueue({
  draftKey,
  initial,
  adapter,
  onPreview,
  readOnly = false,
  model: providedModel,
  disabled = false,
  deferUpload = false,
  integrated = false,
  onFilesSelected,
}: {
  draftKey: string;
  initial: Answer;
  adapter: UploadAdapter;
  onPreview: (files: FileDescriptor[], index: number) => void;
  readOnly?: boolean;
  model?: UploadQueueModel;
  disabled?: boolean;
  deferUpload?: boolean;
  integrated?: boolean;
  onFilesSelected?: () => void;
}) {
  const drafts = useContext(DraftContext);
  const [model] = useState(() => {
    if (providedModel) return providedModel;
    const previous = drafts.get(draftKey);
    if (previous instanceof UploadQueueModel) return previous;
    const next = new UploadQueueModel(initial, adapter);
    drafts.set(draftKey, next);
    return next;
  });
  const state = useSyncExternalStore(model.subscribe, model.snapshot);
  const [removing, setRemoving] = useState<FileDescriptor | null>(null);
  const [deleteError, setDeleteError] = useState('');
  const files = answerFiles(state.answer);
  const locked =
    disabled || readOnly || state.busy || state.needsRead || state.blocked;
  return (
    <section
      aria-label="Файлы ответа"
      className={`${styles.queue} ${integrated ? styles.integrated : ''}`}
    >
      <h2>Файлы ответа</h2>
      <p id="upload-limits">
        {integrated
          ? 'Фото или PDF · до 20 МБ на файл. Макс. 10 файлов.'
          : 'PDF и фото JPEG, PNG, WebP, HEIC · до 20 МиБ каждый, 10 файлов и 100 МиБ всего.'}
      </p>
      {readOnly && (
        <p role="status">Только просмотр. Изменение файлов недоступно.</p>
      )}
      {!readOnly && (
        <label className={styles.picker}>
          Добавить файлы
          <input
            type="file"
            multiple
            accept={acceptedFiles}
            aria-label="Добавить файлы"
            aria-describedby="upload-limits"
            disabled={locked}
            onChange={(event) => {
              const before = model.state.items.length;
              model.add(Array.from(event.target.files || []));
              if (model.state.items.length > before) onFilesSelected?.();
              event.target.value = '';
            }}
          />
        </label>
      )}
      {state.message && <p role="status">{state.message}</p>}
      {state.conflict && (
        <ConflictCompare
          local={
            <ul>
              {state.items
                .filter((item) => item.file)
                .map((item) => (
                  <li key={item.id}>{item.name}</li>
                ))}
            </ul>
          }
          server={
            <>
              <p>Версия {state.answer.version}</p>
              <ul>
                {files.map((file) => (
                  <li key={file.id}>{file.display_name}</li>
                ))}
              </ul>
            </>
          }
          onReload={() => void model.read()}
        />
      )}
      <Stack gap="md">
        {state.items
          .filter((item) => !integrated || item.status !== 'saved')
          .map((item) => (
            <article
              key={item.id}
              className={styles.row}
              aria-label={item.name}
            >
              {item.localUrl && (
                <img
                  className={styles.thumbnail}
                  src={item.localUrl}
                  alt={`Локально: ${item.name}`}
                />
              )}
              <div className={styles.details}>
                <strong>{item.name}</strong>
                <Text size="sm">
                  {(item.size / 1024 / 1024).toFixed(2)} МиБ
                  {item.replaceId !== undefined
                    ? ' · замена выбранного файла'
                    : ''}
                </Text>
                <p role="status">
                  {
                    {
                      ready: 'Готов к загрузке',
                      uploading: 'Загружаем…',
                      processing: 'Обрабатываем…',
                      saved: 'Сохранён',
                      error: 'Не сохранён',
                      uncertain: 'Сохранение не подтверждено',
                    }[item.status]
                  }
                </p>
                {['uploading', 'processing'].includes(item.status) && (
                  <Progress
                    value={item.progress}
                    aria-label={`Загрузка ${item.name}`}
                  />
                )}
                {item.error && <p role="alert">{item.error}</p>}
                {item.file && !item.localUrl && (
                  <p>Предпросмотр появится после обработки сервером.</p>
                )}
                <Group>
                  {['error', 'uncertain'].includes(item.status) && (
                    <Button
                      variant="default"
                      disabled={locked}
                      onClick={() => {
                        model.retry(item.id);
                        onFilesSelected?.();
                      }}
                    >
                      Повторить {item.name}
                    </Button>
                  )}
                  <Button
                    variant="subtle"
                    color="var(--lgg-danger)"
                    disabled={disabled || state.busy || state.needsRead}
                    onClick={() => model.removeLocal(item.id)}
                  >
                    Убрать из очереди {item.name}
                  </Button>
                </Group>
              </div>
            </article>
          ))}
      </Stack>
      {!files.length && <p>Сохранённых файлов пока нет.</p>}
      {files.map((file, index) => (
        <article
          key={file.id}
          className={styles.row}
          aria-label={`Сохранён: ${file.display_name}`}
        >
          <div className={styles.details}>
            <strong>{file.display_name}</strong>
            <Group mt="sm">
              <Button variant="default" onClick={() => onPreview(files, index)}>
                Открыть {file.display_name}
              </Button>
              {!readOnly && (
                <>
                  <label className={styles.picker}>
                    Заменить
                    <input
                      type="file"
                      accept={acceptedFiles}
                      aria-label={`Заменить ${file.display_name}`}
                      disabled={locked}
                      onChange={(event) => {
                        if (event.target.files?.[0]) {
                          const before = model.state.items.length;
                          model.add([event.target.files[0]], file.id);
                          if (model.state.items.length > before)
                            onFilesSelected?.();
                        }
                        event.target.value = '';
                      }}
                    />
                  </label>
                  <Button
                    variant="subtle"
                    color="var(--lgg-danger)"
                    disabled={locked}
                    onClick={() => {
                      setDeleteError('');
                      setRemoving(file);
                    }}
                  >
                    Удалить {file.display_name}
                  </Button>
                </>
              )}
            </Group>
          </div>
        </article>
      ))}
      <Group mt="md">
        {!readOnly && !integrated && (
          <Button
            disabled={
              locked ||
              deferUpload ||
              !state.items.some((item) => item.status === 'ready')
            }
            onClick={() => void model.run()}
          >
            Загрузить выбранные файлы
          </Button>
        )}
        {state.busy && (
          <Button variant="default" onClick={model.abort}>
            Остановить загрузку
          </Button>
        )}
        {(!integrated || state.needsRead || state.conflict) && (
          <Button
            variant="default"
            disabled={disabled || state.busy}
            onClick={() => void model.read()}
          >
            Проверить сохранение файлов
          </Button>
        )}
      </Group>
      {state.needsRead && (
        <p role="alert">
          Результат требует проверки. Отмена не откатывает сохранение на
          сервере. Перечитайте список перед повтором.
        </p>
      )}
      <ConfirmDialog
        destructive
        opened={!!removing}
        title="Удалить файл из ответа?"
        confirmLabel="Удалить файл"
        pending={state.busy}
        error={deleteError}
        confirmDisabled={state.needsRead}
        onCancel={() => setRemoving(null)}
        onConfirm={() => {
          if (removing)
            void model
              .removeServer(removing.id)
              .then(() => setRemoving(null))
              .catch(() =>
                setDeleteError(
                  'Не удалось подтвердить удаление. Закройте окно и перечитайте список.',
                ),
              );
        }}
      >
        Файл «{removing?.display_name}» будет удалён из ответа. Остальные файлы
        сохранятся.
      </ConfirmDialog>
    </section>
  );
}
