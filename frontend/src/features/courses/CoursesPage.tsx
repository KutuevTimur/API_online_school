import { Link, useParams } from 'react-router';
import { usePageTitle } from '../../app/router';
import { dateLabel, lessonStatus } from '../../shared/lib/datetime';
import { type Course, type Lesson, type Page, useRead } from './queries';
import { Pages, ReadOnly, ReadState, useListState, Views } from './ReadUI';
import styles from './read.module.css';
export function CoursesPage() {
  usePageTitle('Мои курсы');
  const state = useListState();
  const query = useRead<Page<Course>>('/courses', {
    view: state.view,
    limit: state.limit,
    offset: state.offset,
  });
  return (
    <>
      <h1>Мои курсы</h1>
      <Views
        value={state.view}
        onChange={(view) => state.update({ view, offset: 0 })}
      />
      <ReadState query={query}>
        {(data) => (
          <>
            {!data.items.length && (
              <p>
                Курсов в этом разделе пока нет. Здесь появятся ваши занятия и
                материалы.
              </p>
            )}
            <ul className={styles.list}>
              {data.items.map((course) => (
                <li key={course.id} className={styles.row}>
                  <Link to={`/student/courses/${course.id}`}>
                    {course.name}
                  </Link>
                  <ReadOnly
                    mode={course.access_mode}
                    reason={course.read_only_reason}
                  />
                  <p>Преподаватель: {course.teacher_name}</p>
                  <p>{course.description}</p>
                </li>
              ))}
            </ul>
            <Pages total={data.total} state={state} />
          </>
        )}
      </ReadState>
    </>
  );
}
export function CoursePage() {
  const { courseId = '' } = useParams();
  const state = useListState();
  const course = useRead<Course>(`/courses/${encodeURIComponent(courseId)}`);
  const lessons = useRead<Page<Lesson>>(
    '/lessons',
    {
      course_id: courseId,
      view: state.view,
      limit: state.limit,
      offset: state.offset,
      sort_date: 'asc',
    },
    !!course.data,
  );
  usePageTitle(course.data?.name || 'Курс');
  return (
    <>
      <Link to="/student/courses">Мои курсы</Link>
      <ReadState query={course}>
        {(data) => (
          <>
            <h1>{data.name}</h1>
            <p>Преподаватель: {data.teacher_name}</p>
            <ReadOnly mode={data.access_mode} reason={data.read_only_reason} />
            <p className={styles.copy}>{data.description}</p>
            <h2>Занятия</h2>
            <Views
              value={state.view}
              onChange={(view) => state.update({ view, offset: 0 })}
            />
            {data.access_mode === 'read_only' && state.view === 'active' && (
              <p>Историю занятий можно открыть в разделе «Архив» или «Все».</p>
            )}
            <ReadState query={lessons}>
              {(page) => (
                <>
                  {!page.items.length && (
                    <p>В этом разделе пока нет занятий.</p>
                  )}
                  <ul className={styles.list}>
                    {page.items.map((lesson) => (
                      <li key={lesson.id} className={styles.row}>
                        <Link to={`/student/lessons/${lesson.id}`}>
                          {lesson.title}
                        </Link>
                        <p>
                          {dateLabel(lesson.scheduled_at)} ·{' '}
                          {lessonStatus(lesson.status)}
                        </p>
                        <ReadOnly
                          mode={lesson.access_mode}
                          reason={lesson.read_only_reason}
                        />
                      </li>
                    ))}
                  </ul>
                  <Pages total={page.total} state={state} />
                </>
              )}
            </ReadState>
          </>
        )}
      </ReadState>
    </>
  );
}
