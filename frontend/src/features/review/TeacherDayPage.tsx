import { Link } from 'react-router';
import { CalendarDays, ClipboardCheck } from 'lucide-react';
import { LinkButton } from '../../shared/ui/LinkButton';
import { usePageTitle } from '../../app/router';
import { useRead, type Page } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { TeacherToday } from '../schedule/TeacherToday';
import { TeacherReminders } from '../schedule/TeacherReminders';
import type { ReviewItem } from './api';
import { ReviewRows } from './ReviewQueuePage';
import styles from '../courses/read.module.css';
export function TeacherDayPage() {
  usePageTitle('Мой день');
  const queue = useRead<Page<ReviewItem>>(
    '/submissions/review-queue',
    { limit: 3, offset: 0 },
    true,
    60000,
  );
  return (
    <>
      <header className={`${styles.heading} ${styles.dayHeading}`}>
        <h1>Мой день</h1>
        <Link to="/teacher/schedule">
          <CalendarDays size={18} aria-hidden="true" />
          Открыть расписание
        </Link>
      </header>
      <div className={`${styles.overview} ${styles.teacherDay}`}>
        <TeacherToday overview />
        <div className={styles.dayColumn}>
          <section
            className={`${styles.panel} ${styles.dayPanel} ${styles.reviewPanel}`}
          >
            <h2 className={styles.daySectionTitle}>
              <ClipboardCheck size={20} aria-hidden="true" />
              На проверку
              {queue.data && (
                <span className={styles.dayCount}>{queue.data.total}</span>
              )}
            </h2>
            <ReadState query={queue}>
              {(data) => (
                <>
                  {!data.total && <p>Пока нет работ на проверку.</p>}
                  <div className={styles.dayReviewList}>
                    <ReviewRows items={data.items} compact />
                  </div>
                  <LinkButton to="/teacher/review" variant="default" navigation>
                    Вся очередь
                  </LinkButton>
                </>
              )}
            </ReadState>
          </section>
          <TeacherReminders overview />
        </div>
      </div>
    </>
  );
}
