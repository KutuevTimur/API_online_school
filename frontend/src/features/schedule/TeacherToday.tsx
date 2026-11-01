import { CallLink } from '../lessons/LessonPage';
import { CalendarDays, Clock, UserRound } from 'lucide-react';
import { Link, useLocation } from 'react-router';
import { LinkButton } from '../../shared/ui/LinkButton';
import { useRead, type Page, type Lesson } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { moscow, dateLabel, lessonStatus } from '../../shared/lib/datetime';
import styles from '../courses/read.module.css';
function Meeting({ lesson }: { lesson: Lesson }) {
  return (
    <>
      <div className={styles.nextMeeting}>
        <p className={styles.nextTime}>
          <time dateTime={lesson.scheduled_at}>
            {moscow(lesson.scheduled_at).format('HH:mm')}
          </time>
          <span>{moscow(lesson.scheduled_at).format('D MMMM')} · МСК</span>
        </p>
        <div className={styles.nextIdentity}>
          <h3 className={styles.nextStudent}>
            {lesson.student_labels?.map((s) => s.display_name).join(', ') ||
              lesson.title}
          </h3>
          {!!lesson.student_labels?.length && (
            <p className={styles.nextTopic}>{lesson.title}</p>
          )}
        </div>
      </div>
      <div className={styles.lessonActions}>
        <LinkButton to={`/teacher/lessons/${lesson.id}`}>
          Открыть занятие
        </LinkButton>
        {lesson.student_labels?.map((student) => (
          <LinkButton
            variant="default"
            leftSection={<UserRound size={18} aria-hidden="true" />}
            key={student.user_id}
            to={`/teacher/students/${student.user_id}`}
          >
            {lesson.student_labels!.length === 1
              ? 'К ученику'
              : student.display_name}
          </LinkButton>
        ))}
        {lesson.effective_call_url && (
          <CallLink url={lesson.effective_call_url} variant="default" />
        )}
      </div>
    </>
  );
}
export function TeacherToday({ overview = false }: { overview?: boolean }) {
  const location = useLocation();
  const today = moscow().startOf('day');
  const query = useRead<Page<Lesson>>(
    '/lessons',
    {
      view: 'active',
      from_date: today.toISOString(),
      to_date: today
        .add(1, 'day')
        .subtract(1, 'millisecond')
        .toISOString()
        .replace('.999Z', '.999999Z'),
      sort_date: 'asc',
      limit: 1000,
    },
    true,
    60000,
  );
  const next = useRead<Page<Lesson>>(
    '/lessons',
    {
      view: 'active',
      status: 'scheduled',
      from_date: today.add(1, 'day').toISOString(),
      sort_date: 'asc',
      limit: 1,
    },
    overview,
    60000,
  );
  const Container = overview ? 'div' : 'details';
  if (overview && query.data === undefined) {
    return (
      <div className={styles.dayColumn}>
        <section
          className={`${styles.lesson} ${styles.dayPanel} ${styles.dayLoading}`}
        >
          <h2 className={styles.daySectionTitle}>
            <Clock size={20} aria-hidden="true" />
            Ближайшее занятие
          </h2>
          <ReadState query={query}>{() => null}</ReadState>
        </section>
        <section className={`${styles.panel} ${styles.dayPanel}`}>
          <h2 className={styles.daySectionTitle}>
            <CalendarDays size={20} aria-hidden="true" />
            Сегодня · {today.format('D MMMM')}
          </h2>
          <ReadState query={query}>{() => null}</ReadState>
        </section>
      </div>
    );
  }
  return (
    <Container className={overview ? styles.dayColumn : styles.panel}>
      {!overview && <summary>Сегодня · {today.format('D MMMM')} · МСК</summary>}
      <ReadState query={query}>
        {(data) => {
          const upcoming = data.items.find(
            (l) =>
              l.status === 'scheduled' &&
              new Date(l.scheduled_at).getTime() + l.duration_minutes * 60000 >
                Date.now(),
          );
          return (
            <>
              {overview ? (
                <section
                  className={`${styles.lesson} ${styles.dayPanel}`}
                  aria-labelledby="next-meeting-heading"
                >
                  <h2
                    id="next-meeting-heading"
                    className={styles.daySectionTitle}
                  >
                    <Clock size={20} aria-hidden="true" />
                    Ближайшее занятие
                  </h2>
                  {upcoming ? (
                    <Meeting lesson={upcoming} />
                  ) : (
                    <ReadState query={next}>
                      {(future) =>
                        future.items[0] ? (
                          <Meeting lesson={future.items[0]} />
                        ) : (
                          <p>
                            Будущих встреч пока нет. Добавьте занятие в
                            расписании.
                          </p>
                        )
                      }
                    </ReadState>
                  )}
                </section>
              ) : (
                <p>
                  {upcoming
                    ? `Ближайшая встреча: ${dateLabel(upcoming.scheduled_at)} · ${upcoming.student_labels?.map((s) => s.display_name).join(', ')}`
                    : 'Сегодня больше нет запланированных встреч.'}
                </p>
              )}
              <section
                className={
                  overview ? `${styles.panel} ${styles.dayPanel}` : undefined
                }
                aria-label="Сегодняшние занятия"
              >
                {overview && (
                  <h2 className={styles.daySectionTitle}>
                    <CalendarDays size={20} aria-hidden="true" />
                    Сегодня · {today.format('D MMMM')}
                  </h2>
                )}
                {!data.items.length && <p>Сегодня занятий нет.</p>}
                {overview ? (
                  <ul className={styles.todayList}>
                    {data.items.map((l) => (
                      <li key={l.id}>
                        <Link
                          className={`${styles.todayRow} ${l.id === upcoming?.id ? styles.todayNext : ''}`}
                          to={`/teacher/lessons/${l.id}`}
                          state={{
                            returnTo: location.pathname + location.search,
                          }}
                        >
                          <time dateTime={l.scheduled_at}>
                            {moscow(l.scheduled_at).format('HH:mm')}
                          </time>
                          <span>
                            {l.student_labels
                              ?.map((s) => s.display_name)
                              .join(', ') || l.title}
                          </span>
                          <span
                            className={styles.todayStatus}
                            data-status={l.status}
                          >
                            {lessonStatus(l.status)}
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  data.items.map((lesson) => (
                    <p key={lesson.id}>
                      <Link
                        to={`/teacher/lessons/${lesson.id}`}
                        state={{
                          returnTo: location.pathname + location.search,
                        }}
                      >
                        {moscow(lesson.scheduled_at).format('HH:mm')} ·{' '}
                        {lesson.student_labels
                          ?.map((student) => student.display_name)
                          .join(', ') || lesson.title}
                      </Link>{' '}
                      · {lessonStatus(lesson.status)}
                    </p>
                  ))
                )}
                {data.total > 1000 && (
                  <p role="alert">
                    Показана первая тысяча занятий. Откройте нужного ученика для
                    остальных.
                  </p>
                )}
              </section>
            </>
          );
        }}
      </ReadState>
    </Container>
  );
}
