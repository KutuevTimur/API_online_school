import { useState, useEffect, useRef } from 'react';
import { Stack, Avatar, Button } from '@mantine/core';
import { request, upload } from '../api/client';
import { ApiError } from '../api/error';
import { ConfirmDialog } from './ConfirmDialog';
import styles from '../../features/courses/read.module.css';
import profileStyles from '../../features/profile/profile.module.css';
export function AvatarEditor({
  profile,
  path,
  allowDelete = true,
  variant = 'avatar',
  onRefresh,
}: {
  profile: {
    avatar_path?: string | null;
    first_name: string;
    last_name: string;
  };
  path: string;
  allowDelete?: boolean;
  variant?: 'avatar' | 'cover';
  onRefresh: () => Promise<unknown>;
}) {
  const cover = variant === 'cover';
  const label = cover ? 'Обложка курса' : 'Аватар';
  const object = cover ? 'обложку' : 'аватар';
  const [src, setSrc] = useState<string>();
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [needsRead, setNeedsRead] = useState(false);
  const [progress, setProgress] = useState('');
  const [revision, setRevision] = useState(0);
  const [avatarError, setAvatarError] = useState(false);
  const controller = useRef<AbortController | undefined>(undefined);
  const objectUrl = useRef<string | undefined>(undefined);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      controller.current?.abort();
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    };
  }, []);
  useEffect(() => {
    const abort = new AbortController();
    if (!profile.avatar_path) {
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = undefined;
      return;
    }
    void request<Blob>(path, {
      response: 'blob',
      signal: abort.signal,
      maxBytes: 10 * 1024 * 1024,
    })
      .then((blob) => {
        if (abort.signal.aborted) return;
        const url = URL.createObjectURL(blob);
        if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
        objectUrl.current = url;
        setSrc(url);
        setAvatarError(false);
      })
      .catch(() => {
        if (!abort.signal.aborted) setAvatarError(true);
      });
    return () => abort.abort();
  }, [path, profile.avatar_path, revision]);
  async function change(file?: File) {
    if (pending || needsRead || controller.current) return;
    if (
      file &&
      (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) ||
        file.size > 10 * 1024 * 1024 ||
        !file.size)
    ) {
      setMessage('Выберите JPG, PNG или WebP до 10 МиБ.');
      return;
    }
    const abort = new AbortController();
    controller.current = abort;
    setPending(true);
    setMessage('');
    setProgress('');
    try {
      if (file) {
        const body = new FormData();
        body.append('avatar', file);
        await upload(path, body, {
          method: 'PATCH',
          signal: abort.signal,
          onProgress: (loaded, total) =>
            setProgress(
              total && loaded < total
                ? `Загрузка: ${Math.round((loaded / total) * 100)}%`
                : 'Обработка изображения…',
            ),
        });
      } else await request(path, { method: 'DELETE', signal: abort.signal });
      if (abort.signal.aborted || !mounted.current) return;
      await onRefresh();
      if (mounted.current) {
        setRevision((v) => v + 1);
        setConfirm(false);
        setMessage(
          file
            ? cover
              ? 'Обложка обновлена'
              : 'Аватар обновлён'
            : cover
              ? 'Обложка удалена'
              : 'Аватар удалён',
        );
      }
    } catch (error) {
      let refreshed = false;
      try {
        await onRefresh();
        refreshed = true;
      } catch {
        /* A failed read must block another write. Keep the last confirmed avatar. */
      }
      if (mounted.current) {
        setNeedsRead(!refreshed);
        setRevision((v) => v + 1);
        setMessage(
          !refreshed
            ? `Результат изменения неизвестен. Сначала проверьте ${object}.`
            : error instanceof ApiError && error.status === 404 && !file
              ? cover
                ? 'Обложка уже удалена. Данные обновлены.'
                : 'Аватар уже удалён. Данные обновлены.'
              : 'Не удалось подтвердить изменение изображения. Данные перечитаны, проверьте изображение перед повтором.',
        );
        setConfirm(false);
      }
    } finally {
      controller.current = undefined;
      if (mounted.current) {
        setPending(false);
        setProgress('');
      }
    }
  }
  return (
    <section className={styles.panel}>
      <h2>{label}</h2>
      <Stack>
        <Avatar
          src={profile.avatar_path ? src : undefined}
          size={96}
          alt={cover ? 'Обложка курса' : 'Ваш аватар'}
        >
          {(profile.first_name[0] || '') + (profile.last_name[0] || '') || 'Я'}
        </Avatar>
        {avatarError && (
          <p role="status">
            Не удалось загрузить изображение.{' '}
            <Button variant="default" onClick={() => setRevision((v) => v + 1)}>
              Обновить {object}
            </Button>
          </p>
        )}
        <label className={profileStyles.avatarPicker}>
          {cover ? 'Новая обложка' : 'Новый аватар'} (JPG, PNG, WebP, до 10 МиБ)
          <input
            aria-label={cover ? 'Новая обложка' : 'Новый аватар'}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            disabled={pending || needsRead}
            onChange={(e) => {
              const file = e.currentTarget.files?.[0];
              e.currentTarget.value = '';
              if (file) void change(file);
            }}
          />
        </label>
        {allowDelete && profile.avatar_path && (
          <Button
            variant="default"
            disabled={pending || needsRead}
            onClick={() => setConfirm(true)}
          >
            Удалить {object}
          </Button>
        )}
        {pending && (
          <>
            <p role="status">{progress || `Обновляем ${object}…`}</p>
            <Button
              variant="default"
              onClick={() => controller.current?.abort()}
            >
              Отменить загрузку
            </Button>
          </>
        )}
        {message && <p role="status">{message}</p>}
        {needsRead && (
          <Button
            variant="default"
            loading={pending}
            onClick={() => {
              if (pending) return;
              setPending(true);
              void onRefresh()
                .then(() => {
                  if (mounted.current) {
                    setNeedsRead(false);
                    setRevision((v) => v + 1);
                    setMessage(
                      'Данные обновлены. Проверьте изображение перед повтором.',
                    );
                  }
                })
                .catch(() => {
                  if (mounted.current)
                    setMessage(
                      `Не удалось проверить ${object}. Восстановите связь и повторите проверку.`,
                    );
                })
                .finally(() => {
                  if (mounted.current) setPending(false);
                });
            }}
          >
            Проверить {object}
          </Button>
        )}
        <ConfirmDialog
          opened={confirm}
          title={`Удалить ${object}?`}
          confirmLabel={`Удалить ${object}`}
          pending={pending}
          onCancel={() => setConfirm(false)}
          onConfirm={() => void change()}
        >
          Вместо фотографии будут показаны инициалы.
        </ConfirmDialog>
      </Stack>
    </section>
  );
}
