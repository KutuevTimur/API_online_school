import styles from './files.module.css';
import { createPortal } from 'react-dom';
import { useEffect, useRef, useState } from 'react';
import { Button, Progress, Stack } from '@mantine/core';
import { upload } from '../api/client';
import { ApiError } from '../api/error';
import { acceptedFiles, validateSelection } from '../api/files';
type Item = {
  id: string;
  file: File;
  state: 'ready' | 'uploading' | 'unknown' | 'checked' | 'error' | 'saved';
  progress: number;
  message: string;
};
export function MaterialUploadQueue({
  lessonId,
  studentId,
  refresh,
  onDirtyChange,
  existingCount = 0,
  pickerLabel = 'Добавить файлы материалов',
  pickerTarget,
}: {
  lessonId: number;
  studentId: number;
  refresh: () => Promise<unknown>;
  onDirtyChange: (dirty: boolean) => void;
  existingCount?: number;
  pickerLabel?: string;
  pickerTarget?: HTMLElement | null;
}) {
  const [items, setItems] = useState<Item[]>([]);
  const active = useRef(false);
  const change = (id: string, patch: Partial<Item>) =>
    setItems((list) => list.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  const remove = (id: string) =>
    setItems((list) => list.filter((x) => x.id !== id));
  async function send(item: Item) {
    if (active.current) return false;
    active.current = true;
    change(item.id, { state: 'uploading', message: 'Загружаем…' });
    const body = new FormData();
    body.append('lesson_id', String(lessonId));
    body.append('student_user_id', String(studentId));
    body.append('file', item.file);
    try {
      await upload('/lectures', body, {
        onProgress: (loaded, total) =>
          change(item.id, {
            progress: total ? Math.round((loaded / total) * 100) : 0,
            message: total && loaded >= total ? 'Обрабатываем…' : 'Загружаем…',
          }),
      });
      change(item.id, {
        state: 'saved',
        message: 'Загружен · доступен ученику',
      });
      try {
        await refresh();
        remove(item.id);
      } catch {
        change(item.id, {
          message: 'Файл загружен. Обновите список материалов.',
        });
      }
      return true;
    } catch (error) {
      const unknown =
        !(error instanceof ApiError) ||
        !error.status ||
        error.status >= 500 ||
        error.status === 401;
      change(item.id, {
        state: unknown ? 'unknown' : 'error',
        message: unknown
          ? 'Не удалось подтвердить загрузку. Сначала проверьте список.'
          : error.message,
      });
      return false;
    } finally {
      active.current = false;
    }
  }
  const locked = items.some(
    (i) => i.state === 'uploading' || i.state === 'unknown',
  );
  const dirty = items.some((i) => i.state !== 'saved');
  useEffect(() => onDirtyChange(dirty), [dirty, onDirtyChange]);
  const picker = (
    <label
      className={`${styles.picker} ${pickerTarget !== undefined ? styles.primaryPicker : ''}`}
    >
      {pickerLabel}
      <input
        type="file"
        multiple
        accept={acceptedFiles}
        aria-label={pickerLabel}
        disabled={locked || existingCount >= 4}
        onChange={(e) => {
          const files = Array.from(e.currentTarget.files || []);
          e.currentTarget.value = '';
          const pending = items.filter((i) => i.state !== 'saved');
          const next: Item[] = files.map((file, i) => {
            const error =
              existingCount + pending.length + i >= 4
                ? 'К занятию можно добавить до 4 файлов.'
                : validateSelection(file, 0, 0);
            return {
              id: crypto.randomUUID(),
              file,
              state: error ? 'error' : 'ready',
              progress: 0,
              message: error || 'Ожидает загрузки',
            };
          });
          setItems((list) => [...list, ...next]);
          void (async () => {
            for (const item of next)
              if (item.state === 'ready' && !(await send(item))) break;
          })();
        }}
      />
    </label>
  );
  return (
    <section aria-label="Загрузка конспектов">
      <p>До 4 файлов · PDF или фото, до 20 МиБ каждый.</p>
      {pickerTarget === undefined
        ? picker
        : pickerTarget
          ? createPortal(picker, pickerTarget)
          : null}
      <Stack>
        {items.map((item) => (
          <article className={styles.row} data-state={item.state} key={item.id}>
            <div className={styles.details}>
              <strong>{item.file.name}</strong>
              <p
                role={
                  item.state === 'error' || item.state === 'unknown'
                    ? 'alert'
                    : 'status'
                }
              >
                {item.message}
              </p>
              {item.state === 'uploading' && (
                <Progress
                  value={item.progress}
                  aria-label={`Загрузка ${item.file.name}`}
                />
              )}
              {item.state === 'unknown' && (
                <Button
                  variant="default"
                  onClick={() => {
                    void refresh()
                      .then(() =>
                        change(item.id, {
                          state: 'checked',
                          message:
                            'Список обновлён. Если файл уже есть выше, уберите повтор. Иначе повторите загрузку.',
                        }),
                      )
                      .catch(() =>
                        change(item.id, {
                          message:
                            'Не удалось проверить загрузку. Повтор заблокирован.',
                        }),
                      );
                  }}
                >
                  Проверить загрузку
                </Button>
              )}
              {['checked', 'ready'].includes(item.state) && (
                <Button disabled={locked} onClick={() => void send(item)}>
                  Загрузить файл
                </Button>
              )}
              {item.state !== 'uploading' && (
                <Button
                  variant="subtle"
                  color="var(--lgg-danger)"
                  onClick={() => remove(item.id)}
                >
                  {item.state === 'saved' ? 'Закрыть сообщение' : 'Убрать файл'}
                </Button>
              )}
            </div>
          </article>
        ))}
      </Stack>
    </section>
  );
}
