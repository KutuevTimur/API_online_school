import { useEffect, useRef } from 'react';
import styles from './ui.module.css';
export function focusFirstError(errors: Record<string, string>) {
  const id = Object.keys(errors)[0];
  if (id) document.getElementById(id)?.focus();
}
export function ErrorSummary({ errors }: { errors: Record<string, string> }) {
  const ref = useRef<HTMLDivElement>(null);
  const firstError = Object.keys(errors)[0];
  useEffect(() => {
    if (firstError) document.getElementById(firstError)?.focus();
  }, [firstError]);
  if (!Object.keys(errors).length) return null;
  return (
    <div ref={ref} role="alert" className={styles.error}>
      <p>Проверьте отмеченные поля</p>
      <ul>
        {Object.entries(errors).map(([id, error]) => (
          <li key={id}>
            <a
              href={`#${id}`}
              onClick={(event) => {
                event.preventDefault();
                document.getElementById(id)?.focus();
              }}
            >
              {error}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
