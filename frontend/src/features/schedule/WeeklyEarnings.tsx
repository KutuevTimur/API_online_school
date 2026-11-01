import { useRead } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { formatKopecks, lessonPlural } from '../students/pricing';
import type { components } from '../../shared/api/schema';
import { Badge } from '@mantine/core';
import styles from './weeklyEarnings.module.css';

export type WeeklyEarningsResult = components['schemas']['WeeklyEarningsDTO'];

export function weeklyEarningsSummary(data: WeeklyEarningsResult) {
  const incomplete = data.unpriced_count > 0;
  return {
    amountLabel: incomplete ? 'Известная сумма' : 'Итого',
    amount: formatKopecks(data.total_kopecks),
    lessonCount: data.lesson_count,
    completedCount: data.completed_count,
    incompleteMessage: incomplete
      ? `Итог неполный: ${data.unpriced_count} ${lessonPlural(data.unpriced_count)} без указанной цены.`
      : null,
  };
}

export function WeeklyEarnings({ week }: { week: string }) {
  const query = useRead<WeeklyEarningsResult>(
    '/teacher-planning/weekly-earnings',
    { week },
    true,
    60000,
  );
  return (
    <section className={styles.panel} aria-label="Итоги выбранной недели">
      <ReadState query={query}>
        {(data) => {
          const summary = weeklyEarningsSummary(data);
          return (
            <div>
              <div className={styles.row}>
                <h2 id="weekly-earnings-title">За проведённые занятия</h2>
                <strong
                  aria-label={`${summary.amountLabel}: ${summary.amount}`}
                >
                  {summary.incompleteMessage && 'Известная сумма: '}
                  {summary.amount}
                </strong>
                <Badge variant="light" size="lg">
                  Занятий за неделю · {summary.lessonCount}
                </Badge>
              </div>
              {summary.incompleteMessage && (
                <p role="status">{summary.incompleteMessage}</p>
              )}
            </div>
          );
        }}
      </ReadState>
    </section>
  );
}
