import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { request } from '../../shared/api/client';
import { useSession } from '../auth/session';
import type { components } from '../../shared/api/schema';
export type Notice = components['schemas']['NotificationResponseDTO'];
export type Target = components['schemas']['NotificationTargetDTO'];
export const notificationLabel = (event: string) =>
  ({
    homework_assigned: 'Назначено домашнее задание',
    lesson_rescheduled: 'Занятие перенесено',
    lesson_cancelled: 'Занятие отменено',
    lesson_restored: 'Занятие восстановлено',
    solution_submitted: 'Решение отправлено',
    solution_checked: 'Работа проверена',
  })[event] || 'Обновление в обучении';
export function targetPath(target: Target, role: string) {
  if (!target.available) return undefined;
  if (role === 'teacher') {
    if (
      target.object_type === 'lesson' &&
      target.object_id &&
      target.object_id > 0
    )
      return `/teacher/lessons/${target.object_id}`;
    if (
      target.object_type === 'submission' &&
      target.object_id &&
      target.object_id > 0 &&
      target.homework_id &&
      target.homework_id > 0
    )
      return `/teacher/review/${target.object_id}?homework_id=${target.homework_id}`;
    return undefined;
  }
  if (role !== 'student') return undefined;
  const id =
    target.object_type === 'submission' ? target.homework_id : target.object_id;
  if (!id || id < 1) return undefined;
  return target.object_type === 'lesson'
    ? `/student/lessons/${id}`
    : ['homework', 'submission'].includes(target.object_type || '')
      ? `/student/homeworks/${id}`
      : undefined;
}
export const pollActive = () =>
  document.visibilityState === 'visible' && navigator.onLine;
export function useNotices<T>(
  path: string,
  params: Record<string, string | number | undefined> = {},
  enabled = true,
) {
  const auth = useSession();
  const client = useQueryClient();
  const [active, setActive] = useState(pollActive);
  useEffect(() => {
    const changed = () => {
      const next = pollActive();
      setActive(next);
      if (!next) void client.cancelQueries({ queryKey: ['notifications'] });
      else
        void client.invalidateQueries(
          { queryKey: ['notifications'] },
          { cancelRefetch: false },
        );
    };
    document.addEventListener('visibilitychange', changed);
    window.addEventListener('focus', changed);
    window.addEventListener('online', changed);
    window.addEventListener('offline', changed);
    return () => {
      document.removeEventListener('visibilitychange', changed);
      window.removeEventListener('focus', changed);
      window.removeEventListener('online', changed);
      window.removeEventListener('offline', changed);
    };
  }, [client]);
  const query = useQuery({
    queryKey: ['notifications', auth.user?.id, path, params],
    queryFn: ({ signal }) => request<T>(path, { params, signal }),
    enabled: enabled && active && auth.status === 'ready' && !auth.reauth,
    refetchInterval: active ? 60000 : false,
    refetchOnWindowFocus: 'always',
    refetchOnMount: 'always',
  });
  return { ...query, pollingPaused: !active };
}
