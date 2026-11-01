import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router';
import { Button, Checkbox } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { usePageTitle } from '../../app/router';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import { dateLabel } from '../../shared/lib/datetime';
import { useSession } from '../auth/session';
import { type Page } from '../courses/queries';
import { Pages, ReadState, useListState } from '../courses/ReadUI';
import {
  type Notice,
  type Target,
  notificationLabel,
  targetPath,
  useNotices,
} from './api';
import styles from '../courses/read.module.css';
export function NotificationsPage() {
  usePageTitle('Уведомления');
  const state = useListState();
  const auth = useSession();
  const navigate = useNavigate();
  const client = useQueryClient();
  const unread = state.params.get('unread') === '1';
  const query = useNotices<Page<Notice>>('/notifications', {
    limit: state.limit,
    offset: state.offset,
    unread_only: unread ? 'true' : 'false',
  });
  const [pending, setPending] = useState<number>();
  const [message, setMessage] = useState('');
  const controller = useRef<AbortController | undefined>(undefined);
  useEffect(() => () => controller.current?.abort(), []);
  async function open(item: Notice) {
    if (controller.current) return;
    const abort = new AbortController();
    controller.current = abort;
    setPending(item.id);
    setMessage('');
    try {
      await request(`/notifications/${item.id}/read`, {
        method: 'PATCH',
        signal: abort.signal,
      });
      await client.invalidateQueries({ queryKey: ['notifications'] });
      const target = await request<Target>(`/notifications/${item.id}/target`, {
        signal: abort.signal,
      });
      const path = targetPath(target, auth.user!.role);
      if (abort.signal.aborted) return;
      if (path) navigate(path);
      else
        setMessage(
          'Материал больше недоступен. Уведомление прочитано; остальные разделы остаются доступны.',
        );
    } catch (error) {
      if (!abort.signal.aborted)
        setMessage(
          error instanceof ApiError
            ? error.message + '. Повторите открытие уведомления.'
            : 'Не удалось открыть уведомление. Повторите попытку.',
        );
    } finally {
      if (!abort.signal.aborted) setPending(undefined);
      controller.current = undefined;
    }
  }
  return (
    <>
      <header className={styles.heading}>
        <h1>Уведомления</h1>
        <p>Задания, изменения занятий и результаты проверки.</p>
      </header>
      <Checkbox
        mb="lg"
        label="Только непрочитанные"
        checked={unread}
        onChange={(e) =>
          state.update({
            unread: e.currentTarget.checked ? '1' : '0',
            offset: 0,
          })
        }
      />
      {message && <p role="status">{message}</p>}
      {query.pollingPaused && (
        <p role="status">
          Обновление уведомлений приостановлено. Проверьте соединение; список
          обновится при возвращении в активную вкладку.
        </p>
      )}
      {query.pollingPaused && !query.data ? null : (
        <ReadState query={query}>
          {(data) => (
            <>
              <section
                className={styles.noticeList}
                aria-label="Список уведомлений"
              >
                {!data.items.length && (
                  <p>
                    {unread
                      ? 'Непрочитанных уведомлений нет.'
                      : 'Уведомлений пока нет.'}
                  </p>
                )}
                {data.items.map((item) => (
                  <article
                    className={styles.notification}
                    data-unread={!item.read_at}
                    key={item.id}
                  >
                    <div className={styles.noticeCopy}>
                      <h2>{notificationLabel(item.event_type)}</h2>
                      <p>
                        <time dateTime={item.created_at}>
                          {dateLabel(item.created_at)}
                        </time>
                        {' · '}
                        <strong className={styles.noticeStatus}>
                          {item.read_at ? 'Прочитано' : 'Новое · не прочитано'}
                        </strong>
                      </p>
                    </div>
                    <Button
                      variant={item.read_at ? 'default' : 'filled'}
                      disabled={pending !== undefined && pending !== item.id}
                      loading={pending === item.id}
                      onClick={() => void open(item)}
                    >
                      Открыть уведомление
                    </Button>
                  </article>
                ))}
              </section>
              <Pages total={data.total} state={state} />
            </>
          )}
        </ReadState>
      )}
    </>
  );
}
