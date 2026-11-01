import type { ReactNode } from 'react';
import { Button } from '@mantine/core';
import styles from './ui.module.css';
export function ConflictCompare({
  local,
  server,
  onReload,
}: {
  local: ReactNode;
  server: ReactNode;
  onReload: () => void;
}) {
  return (
    <section aria-label="Сравнение версий">
      <p role="alert">
        Ответ изменился. Ваша работа сохранена в этой вкладке. Сравните её с
        серверной версией перед повтором.
      </p>
      <div className={styles.grid}>
        <div>
          <h3>В этой вкладке</h3>
          {local}
        </div>
        <div>
          <h3>На сервере</h3>
          {server}
        </div>
      </div>
      <Button variant="default" onClick={onReload}>
        Открыть обновлённый ответ
      </Button>
    </section>
  );
}
