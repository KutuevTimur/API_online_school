import { Link } from 'react-router';
import { ArrowRight, BookOpen, Clock3, FileText } from 'lucide-react';
import { LinkButton } from '../../shared/ui/LinkButton';
import { StudentAnswerBadge } from '../../shared/ui/StatusBadge';
import { usePageTitle } from '../../app/router';
import { useEffect, useState } from 'react';
import { dateLabel, deadlineLabel } from '../../shared/lib/datetime';
import {
  type Course,
  type Lesson,
  type Homework,
  type Page,
  type Answer,
  useRead,
} from './queries';
import { ReadState } from './ReadUI';
import { CourseContext } from './CourseContext';
import { CallLink } from '../lessons/LessonPage';
import styles from './read.module.css';
function LastResult({ homework }: { homework: Homework }) {
  const answer = useRead<Answer>(
    `/submissions/${homework.working_submission_id}`,
    { homework_id: homework.id },
    !!homework.working_submission_id,
  );
  return (
    <>
      <h3>{homework.title}</h3>
      <ReadState query={answer}>
        {(data) =>
          data.status === 'checked' ? (
            <>
              <p>Проверено · {data.grade ?? '—'} из 5</p>
              <LinkButton
                navigation
                variant="default"
                to={`/student/homeworks/${homework.id}#result`}
              >
                Посмотреть результат
              </LinkButton>
            </>
          ) : (
            <p>Результат пока недоступен.</p>
          )
        }
      </ReadState>
    </>
  );
}
export function MyDayPage() {
  usePageTitle('Мой день');
  const [now, setNow] = useState(() => new Date().toISOString());
  useEffect(() => {
    const timer = window.setInterval(
      () => setNow(new Date().toISOString()),
      60000,
    );
    return () => window.clearInterval(timer);
  }, []);
  const lesson = useRead<Page<Lesson>>('/lessons', {
    view: 'active',
    status: 'scheduled',
    from_date: now,
    sort_date: 'asc',
    limit: 1,
    offset: 0,
  });
  const latest = useRead<Page<Lesson>>('/lessons', {
    view: 'all',
    status: 'completed',
    sort_date: 'desc',
    limit: 1,
    offset: 0,
  });
  const todo = useRead<Page<Homework>>('/homeworks/my/page', {
    view: 'active',
    status: 'todo',
    limit: 2,
    offset: 0,
  });
  const submitted = useRead<Page<Homework>>('/homeworks/my/page', {
    view: 'active',
    status: 'submitted',
    limit: 3,
    offset: 0,
  });
  const checked = useRead<Page<Homework>>('/homeworks/my/page', {
    view: 'all',
    status: 'checked',
    limit: 1,
    offset: 0,
  });
  const courses = useRead<Page<Course>>('/courses', {
    view: 'active',
    limit: 4,
    offset: 0,
  });
  return (
    <>
      <header className={styles.heading}>
        <h1>
          Мой день
          <span className={styles.dot} aria-hidden="true">
            .
          </span>
        </h1>
      </header>
      <div className={`${styles.overview} ${styles.studentDay}`}>
        <section
          className={`${styles.lesson} ${styles.studentNearest}`}
          aria-label="Ближайшее занятие"
        >
          <h2>Ближайшее занятие</h2>
          <ReadState query={lesson}>
            {(data) =>
              data.items[0] ? (
                <>
                  {(data.items[0].topic ||
                    data.items[0].title !== 'Занятие') && (
                    <h3 className={styles.lessonTitle}>
                      {data.items[0].topic || data.items[0].title}
                    </h3>
                  )}
                  <p className={styles.meetingTime}>
                    <Clock3 size={20} aria-hidden="true" />
                    {dateLabel(data.items[0].scheduled_at)}
                  </p>
                  <CourseContext lesson={data.items[0]} />
                  {data.items[0].access_mode === 'read_only' && (
                    <p>Только просмотр</p>
                  )}
                  <div className={styles.lessonActions}>
                    <CallLink
                      audience="student"
                      url={data.items[0].effective_call_url}
                    />
                    <LinkButton
                      navigation
                      variant="default"
                      to={`/student/lessons/${data.items[0].id}`}
                      rightSection={<ArrowRight size={18} aria-hidden="true" />}
                    >
                      Открыть занятие
                    </LinkButton>
                  </div>
                </>
              ) : (
                <p>
                  Пока нет предстоящих занятий. Время следующей встречи можно
                  уточнить у преподавателя.
                </p>
              )
            }
          </ReadState>
        </section>
        <div className={`${styles.dayColumn} ${styles.studentTasks}`}>
          <section className={`${styles.panel} ${styles.studentTodo}`}>
            <div className={styles.sectionHeading}>
              <h2>К выполнению</h2>
              <FileText size={22} aria-hidden="true" />
            </div>
            <ReadState query={todo}>
              {(data) => (
                <>
                  {!data.items.length && <p>Заданий к выполнению пока нет.</p>}
                  <ul className={styles.list}>
                    {data.items.map((item) => (
                      <li key={item.id} className={styles.task}>
                        <div className={styles.taskMeta}>
                          <span>{item.course_name}</span>
                          <span
                            className={styles.taskStatus}
                            data-debt={
                              item.placement_kind === 'debt' || undefined
                            }
                          >
                            {item.placement_kind === 'debt'
                              ? 'Долг'
                              : 'К выполнению'}
                          </span>
                        </div>
                        <h3>{item.title}</h3>
                        {item.description && (
                          <p className={styles.taskDescription}>
                            {item.description}
                          </p>
                        )}
                        <p className={styles.deadline}>
                          <Clock3 size={16} aria-hidden="true" />
                          {deadlineLabel(item.deadline)}
                        </p>
                        <LinkButton
                          navigation
                          variant="default"
                          to={`/student/homeworks/${item.id}`}
                        >
                          Открыть задание
                        </LinkButton>
                      </li>
                    ))}
                  </ul>
                  {data.total > 2 && (
                    <p>
                      Всего заданий: {data.total}. Остальные доступны в разделе
                      домашних заданий ваших курсов.
                    </p>
                  )}
                </>
              )}
            </ReadState>
          </section>
          <section className={`${styles.panel} ${styles.studentSubmitted}`}>
            <h2>На проверке</h2>
            <ReadState query={submitted}>
              {(data) => (
                <>
                  {!data.total && <p>Здесь появятся отправленные решения.</p>}
                  <ul className={styles.list}>
                    {data.items.map((item) => (
                      <li key={item.id} className={styles.task}>
                        <StudentAnswerBadge state="submitted" />
                        <h3>{item.title}</h3>
                        <p>Решение отправлено. Ждём проверку учителя.</p>
                        <LinkButton
                          navigation
                          variant="default"
                          to={`/student/homeworks/${item.id}`}
                        >
                          Открыть решение
                        </LinkButton>
                      </li>
                    ))}
                  </ul>
                  {data.total > 3 && (
                    <Link to="/student/homeworks?status=submitted">
                      Все отправленные решения · {data.total}
                    </Link>
                  )}
                </>
              )}
            </ReadState>
          </section>
        </div>
        <section
          className={`${styles.result} ${styles.studentLastResult}`}
          aria-label="Последний результат"
        >
          <h2>Последний результат</h2>
          <ReadState query={checked}>
            {(data) =>
              data.items[0] ? (
                <LastResult homework={data.items[0]} />
              ) : (
                <p>Здесь появится результат после проверки задания.</p>
              )
            }
          </ReadState>
        </section>
        <section
          className={`${styles.panel} ${styles.studentRecent}`}
          aria-label="Мои занятия"
        >
          <h2>Мои занятия</h2>
          <ReadState query={latest}>
            {(data) =>
              data.items[0] ? (
                <>
                  <div className={styles.recentMeta}>
                    <p className={styles.recentDate}>
                      Последнее занятие ·{' '}
                      {dateLabel(data.items[0].scheduled_at)}
                    </p>
                    <CourseContext
                      lesson={data.items[0]}
                      variant="teacher-inline"
                    />
                  </div>
                </>
              ) : (
                <p>Здесь появится последнее проведённое занятие.</p>
              )
            }
          </ReadState>
          <div className={styles.recentActions}>
            <LinkButton navigation variant="default" to="/student/materials">
              Открыть занятия
            </LinkButton>
          </div>
        </section>
      </div>
      <section className={styles.courses}>
        <div className={styles.sectionHeading}>
          <h2>Мои курсы</h2>
          <LinkButton
            navigation
            to="/student/courses"
            variant="subtle"
            rightSection={<ArrowRight size={18} aria-hidden="true" />}
          >
            Все курсы и архив
          </LinkButton>
        </div>
        <ReadState query={courses}>
          {(data) => (
            <>
              {!data.items.length && <p>Активных курсов пока нет.</p>}
              <ul className={styles.courseGrid}>
                {data.items.map((item) => (
                  <li key={item.id}>
                    <Link
                      className={styles.courseCard}
                      to={`/student/courses/${item.id}`}
                    >
                      <span className={styles.courseMark}>
                        <BookOpen size={24} aria-hidden="true" />
                      </span>
                      <span className={styles.courseCopy}>
                        <strong>{item.name}</strong>
                        <span>
                          {item.description || 'Занятия и материалы курса'}
                        </span>
                        <span className={styles.courseAction}>
                          Открыть курс{' '}
                          <ArrowRight size={16} aria-hidden="true" />
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </ReadState>
      </section>
    </>
  );
}
