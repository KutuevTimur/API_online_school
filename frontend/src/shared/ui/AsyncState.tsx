import { Button } from '@mantine/core';
import type { ReactNode } from 'react';
import styles from './ui.module.css';
export type AsyncKind =
  | 'loading'
  | 'refresh'
  | 'empty'
  | 'no-results'
  | 'error'
  | 'offline'
  | 'readonly';
const text: Record<AsyncKind, string> = {
  loading: 'Загружаем…',
  refresh: 'Обновляем…',
  empty: 'Пока нет занятий',
  'no-results': 'Ничего не найдено',
  error: 'Не удалось загрузить данные',
  offline: 'Нет связи. Проверьте подключение',
  readonly: 'Только просмотр: курс в архиве',
};
export function AsyncState({
  kind,
  onRetry,
  children,
}: {
  kind: AsyncKind;
  onRetry?: () => void;
  children?: ReactNode;
}) {
  return (
    <div
      className={styles.state}
      aria-busy={kind === 'loading' || kind === 'refresh'}
    >
      <p role={kind === 'error' || kind === 'offline' ? 'alert' : 'status'}>
        {text[kind]}
      </p>
      {children}
      {onRetry && (
        <Button variant="default" onClick={onRetry}>
          {kind === 'no-results' ? 'Сбросить фильтры' : 'Повторить'}
        </Button>
      )}
    </div>
  );
}
