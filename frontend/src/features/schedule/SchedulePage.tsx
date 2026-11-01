import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import { Button } from '@mantine/core';
import { WeekNavigation } from '../../shared/ui/WeekNavigation';
import { LinkButton } from '../../shared/ui/LinkButton';
import { usePageTitle } from '../../app/router';
import {
  lessonStatus,
  moscow,
  weekStart,
  weekWindow,
} from '../../shared/lib/datetime';
import { type Lesson, type Page, useRead } from '../courses/queries';
import { CourseContext } from '../courses/CourseContext';
import { ReadState } from '../courses/ReadUI';
import styles from './schedule.module.css';
function ScheduleLesson({ item, now }: { item: Lesson; now: number }) {
  const elapsed =
    item.status !== 'cancelled' &&
    new Date(item.scheduled_at).getTime() + item.duration_minutes * 60000 <=
      now;
  return (
    <article className={styles.event} data-status={item.status}>
      <div className={styles.eventHeading}>
        <strong className={styles.eventTime}>
          {moscow(item.scheduled_at).format('HH:mm')}
        </strong>
        <span>{lessonStatus(item.status)}</span>
      </div>
      {elapsed && <span className={styles.elapsed}>Уже прошло</span>}
      <LinkButton
        variant="default"
        className={styles.lessonLink}
        to={`/student/lessons/${item.id}`}
        aria-label={`Открыть занятие: ${item.topic || item.title}`}
      >
        {item.topic || item.title}
      </LinkButton>
      <CourseContext lesson={item} />
      {item.access_mode === 'read_only' && <span>Только просмотр</span>}
    </article>
  );
}
export function SchedulePage() {
  usePageTitle('Расписание');
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60000);
    return () => window.clearInterval(timer);
  }, []);
  const [params, set] = useSearchParams();
  const start = weekStart(params.get('week'));
  const rawDay = Number(params.get('day') ?? (moscow().day() + 6) % 7);
  const day =
    Number.isInteger(rawDay) && rawDay >= 0 && rawDay <= 6 ? rawDay : 0;
  const update = (values: Record<string, string | number>) => {
    const next = new URLSearchParams(params);
    Object.entries(values).forEach(([key, value]) =>
      next.set(key, String(value)),
    );
    set(next);
  };
  const range = weekWindow(start.format('YYYY-MM-DD'));
  const query = useRead<Page<Lesson>>(
    '/lessons',
    {
      view: 'active',
      ...range,
      sort_date: 'asc',
      limit: 1000,
      offset: 0,
    },
    true,
    60000,
  );
  const days = Array.from({ length: 7 }, (_, i) => start.add(i, 'day'));
  return (
    <>
      <h1>Расписание</h1>
      <WeekNavigation
        week={start.format('YYYY-MM-DD')}
        onChange={(week, today) =>
          update({ week, ...(today ? { day: (moscow().day() + 6) % 7 } : {}) })
        }
      />
      <h2 aria-live="polite">
        {start.format('D MMMM')} — {start.add(6, 'day').format('D MMMM YYYY')} ·
        МСК
      </h2>
      <div className={styles.dayButtons} aria-label="День недели">
        {days.map((date, i) => (
          <Button
            key={i}
            variant={
              day === i
                ? 'filled'
                : query.data?.items.some(
                      (item) =>
                        item.status !== 'cancelled' &&
                        moscow(item.scheduled_at).isSame(date, 'day'),
                    )
                  ? 'light'
                  : 'default'
            }
            aria-label={`${date.format('dd D MMMM')}${query.data?.items.some((item) => item.status !== 'cancelled' && moscow(item.scheduled_at).isSame(date, 'day')) ? ', есть занятия' : ''}`}
            aria-pressed={day === i}
            onClick={() => update({ day: i })}
          >
            <span>
              {date.format('dd')} <br />
              {date.format('D')}
            </span>
          </Button>
        ))}
      </div>
      <ReadState query={query}>
        {(data) => {
          // Calendar is a bounded weekly dataset, not a paginated page filtered in memory.
          if (data.total > 1000)
            return (
              <p role="alert">
                Слишком много занятий для одной недели. Обратитесь к
                преподавателю.
              </p>
            );
          return (
            <>
              {!data.items.length && <p>На этой неделе занятий пока нет.</p>}
              <div className={styles.calendar} aria-label="Календарь недели">
                {days.map((date, i) => {
                  const items = data.items.filter(
                    (item) =>
                      moscow(item.scheduled_at).format('YYYY-MM-DD') ===
                      date.format('YYYY-MM-DD'),
                  );
                  return (
                    <section
                      key={i}
                      className={styles.day}
                      data-selected={day === i}
                      data-today={date.isSame(moscow(), 'day')}
                      data-empty={!items.length}
                    >
                      <h3>
                        {date.format('dddd')}
                        <span>{date.format('D MMMM')}</span>
                      </h3>
                      <div className={styles.dayLessons}>
                        {items.map((item) => (
                          <ScheduleLesson key={item.id} item={item} now={now} />
                        ))}
                        {!items.length && (
                          <p className={styles.emptyDay}>
                            В этот день занятий нет.
                          </p>
                        )}
                      </div>
                    </section>
                  );
                })}
              </div>
            </>
          );
        }}
      </ReadState>
    </>
  );
}
