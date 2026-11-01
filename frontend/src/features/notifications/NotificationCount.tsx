import { useNotices } from './api';
import styles from './notifications.module.css';
export function NotificationCount({
  variant = 'text',
}: {
  variant?: 'text' | 'badge';
}) {
  const query = useNotices<{ unread: number }>('/notifications/unread');
  if (variant === 'badge') {
    if (!query.data)
      return query.isError ? (
        <span className={styles.srOnly}>Число непрочитанных недоступно</span>
      ) : null;
    const count = query.data.unread;
    return count > 0 ? (
      <span className={styles.count} aria-label={`Непрочитанных: ${count}`}>
        {count > 99 ? '99+' : count}
      </span>
    ) : null;
  }
  return query.data ? (
    <span aria-label={`Непрочитанных: ${query.data.unread}`}>
      {' '}
      ({query.data.unread})
    </span>
  ) : null;
}
