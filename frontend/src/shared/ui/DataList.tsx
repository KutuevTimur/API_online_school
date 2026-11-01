import type { ReactNode } from 'react';
import { Link } from 'react-router';
import styles from './ui.module.css';
export function DataList<T>({
  rows,
  columns = [],
  rowKey,
  label,
  rowLink,
  renderRow,
  rowState,
  variant = 'default',
}: {
  rows: T[];
  columns?: { label: string; render: (row: T) => ReactNode }[];
  rowKey: (row: T) => string;
  label: string;
  rowState?: unknown;
  variant?: 'default' | 'review';
  rowLink?: (row: T) => string;
  renderRow?: (row: T) => ReactNode;
}) {
  if (rowLink && renderRow)
    return (
      <ul aria-label={label} className={styles.linkList} data-variant={variant}>
        {rows.map((row) => (
          <li key={rowKey(row)}>
            <Link to={rowLink(row)} state={rowState}>
              {renderRow(row)}
            </Link>
          </li>
        ))}
      </ul>
    );
  return (
    <>
      <table className={styles.table}>
        <caption>{label}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.label} scope="col">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((column) => (
                <td key={column.label}>{column.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <ul aria-label={label} className={styles.mobileList}>
        {rows.map((row) => (
          <li key={rowKey(row)}>
            {columns.map((column) => (
              <div key={column.label}>
                <strong>{column.label}: </strong>
                {column.render(row)}
              </div>
            ))}
          </li>
        ))}
      </ul>
    </>
  );
}
