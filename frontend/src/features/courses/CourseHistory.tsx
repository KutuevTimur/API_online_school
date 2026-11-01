import { useState } from 'react';
import { PlainTextLinks } from '../../shared/ui/PlainTextLinks';
import { Link, useLocation } from 'react-router';
import { Button } from '@mantine/core';
import styles from './read.module.css';
import { SelectField } from '../../shared/ui/SelectField';
import { dateLabel, lessonStatus } from '../../shared/lib/datetime';
import {
  useRead,
  type Page,
  type Lesson,
  type Recipient,
  type Lecture,
  type Homework,
} from './queries';
import { ReadState, ReadFiles, Pages, useListState } from './ReadUI';
export function CourseHistory({
  courseId,
  studentId,
}: {
  courseId: number;
  studentId?: string;
}) {
  // One boundary for both inclusive API ranges, stable across paging/preview.
  const [boundary] = useState(() => {
    const second = Math.floor(Date.now() / 1000) * 1000;
    return {
      future: new Date(second).toISOString(),
      past: new Date(second - 1).toISOString().replace('.999Z', '.999999Z'),
    };
  });
  const next = useRead<Page<Lesson>>('/lessons', {
    course_id: courseId,
    ...(studentId ? { student_user_id: Number(studentId) } : {}),
    view: 'active',
    status: 'scheduled',
    from_date: boundary.future,
    sort_date: 'asc',
    limit: 1,
    offset: 0,
  });
  const location = useLocation();
  const linkState = {
    returnTo: location.pathname + location.search,
    studentListSearch: location.state?.studentListSearch,
  };
  return (
    <section className={styles.workspaceHistory}>
      <section className={styles.lesson} aria-label="Ближайшее занятие">
        <h2>Ближайшее занятие</h2>
        <ReadState query={next}>
          {(data) =>
            data.items[0] ? (
              <>
                <p className={styles.meetingTime}>
                  {dateLabel(data.items[0].scheduled_at)}
                </p>
                <p>{data.items[0].title}</p>
                <Link
                  className={styles.studentLink}
                  to={`/teacher/lessons/${data.items[0].id}${studentId ? `?student=${studentId}` : ''}`}
                  state={linkState}
                >
                  Открыть занятие
                </Link>
              </>
            ) : (
              <p>
                Ближайших запланированных занятий нет.{' '}
                <Link to="/teacher/schedule">Открыть расписание</Link>
              </p>
            )
          }
        </ReadState>
      </section>
      <HistoryLessons
        courseId={courseId}
        studentId={studentId}
        before={boundary.past}
      />
      <details
        open={
          new URLSearchParams(location.search).has('next-offset') || undefined
        }
      >
        <summary>Следующие занятия</summary>
        <HistoryLessons
          courseId={courseId}
          studentId={studentId}
          after={boundary.future}
        />
      </details>
    </section>
  );
}
function HistoryLessons({
  courseId,
  studentId,
  before,
  after,
}: {
  courseId: number;
  studentId?: string;
  before?: string;
  after?: string;
}) {
  const future = !!after;
  const state = useListState(future ? 'next-' : 'history-');
  const location = useLocation();
  const [lessonId, setLessonId] = useState('');
  const lessons = useRead<Page<Lesson>>('/lessons', {
    course_id: courseId,
    ...(studentId ? { student_user_id: Number(studentId) } : {}),
    view: 'all',
    ...(future
      ? { from_date: after, sort_date: 'asc' }
      : { to_date: before, sort_date: 'desc' }),
    limit: state.limit,
    offset: state.offset,
  });
  return (
    <section>
      <h2>
        {future
          ? 'Будущие встречи, включая отменённые и архивные'
          : 'Прошедшие занятия'}
      </h2>
      <ReadState query={lessons}>
        {(data) => (
          <>
            {!data.items.length && (
              <p>
                {state.offset
                  ? 'На этой странице занятий нет. Вернитесь на предыдущую страницу.'
                  : future
                    ? 'Будущих встреч пока нет.'
                    : 'Прошедших занятий пока нет.'}
              </p>
            )}
            <ul
              className={styles.list}
              aria-label={
                future
                  ? 'Следующие занятия ученика'
                  : 'Прошедшие занятия ученика'
              }
            >
              {data.items.map((lesson) => (
                <li className={styles.historyLesson} key={lesson.id}>
                  <div className={styles.historySummary}>
                    <Link
                      to={`/teacher/lessons/${lesson.id}${studentId ? `?student=${studentId}` : ''}`}
                      state={{
                        returnTo: location.pathname + location.search,
                        studentListSearch: location.state?.studentListSearch,
                      }}
                    >
                      <time dateTime={lesson.scheduled_at}>
                        {dateLabel(lesson.scheduled_at)}
                      </time>
                      <span>{lesson.title}</span>
                    </Link>
                    <p>
                      {lesson.is_deleted
                        ? `В архиве · ${lessonStatus(lesson.status)}`
                        : lessonStatus(lesson.status)}
                    </p>
                    {lesson.recipient_materials
                      ?.filter(
                        (r) =>
                          !studentId || String(r.student_user_id) === studentId,
                      )
                      .map((r) => (
                        <p className={styles.attention} key={r.student_user_id}>
                          {[
                            r.needs_homework ? 'ДЗ не выдано' : '',
                            r.needs_lecture ? 'Конспект не загружен' : '',
                          ]
                            .filter(Boolean)
                            .join(' · ')}
                        </p>
                      ))}
                  </div>
                  <Button
                    className={styles.action}
                    variant="default"
                    aria-expanded={lessonId === String(lesson.id)}
                    onClick={() =>
                      setLessonId(
                        lessonId === String(lesson.id) ? '' : String(lesson.id),
                      )
                    }
                  >
                    {lessonId === String(lesson.id)
                      ? 'Скрыть материалы'
                      : 'Открыть материалы'}
                  </Button>
                  {lessonId === String(lesson.id) && (
                    <div className={styles.historyMaterials}>
                      {studentId ? (
                        <HistoryFiles
                          key={lessonId}
                          lessonId={lessonId}
                          studentId={studentId}
                          embedded
                        />
                      ) : (
                        <HistoryRecipients key={lessonId} lessonId={lessonId} />
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
            <Pages
              label={
                future
                  ? 'Страницы следующих занятий'
                  : 'Страницы прошедших занятий'
              }
              state={state}
              total={data.total}
            />
          </>
        )}
      </ReadState>
    </section>
  );
}

function HistoryRecipients({ lessonId }: { lessonId: string }) {
  const state = useListState('recipients-');
  const [recipient, setRecipient] = useState('');
  const recipients = useRead<Page<Recipient>>(`/lessons/${lessonId}/students`, {
    limit: state.limit,
    offset: state.offset,
  });
  return (
    <ReadState query={recipients}>
      {(data) => (
        <>
          <SelectField
            label="Ученик — получатель материалов"
            value={recipient || null}
            clearable
            data={data.items.map((r) => ({
              value: String(r.student_user_id),
              label: `${r.display_name}${r.school_grade ? ` · ${r.school_grade}` : ''} · ${r.username}`,
            }))}
            onChange={(v) => setRecipient(v || '')}
          />
          <Pages
            label="Страницы получателей"
            state={state}
            total={data.total}
          />
          {recipient && (
            <HistoryFiles lessonId={lessonId} studentId={recipient} />
          )}
        </>
      )}
    </ReadState>
  );
}
function HistoryFiles({
  lessonId,
  studentId,
  embedded = false,
}: {
  embedded?: boolean;
  lessonId: string;
  studentId: string;
}) {
  const state = useListState('files-');
  const params = { lesson_id: lessonId, student_user_id: studentId };
  const lectures = useRead<Page<Lecture>>('/lectures', {
    ...params,
    limit: state.limit,
    offset: state.offset,
  });
  const homeworks = useRead<Homework[]>('/homeworks', params);
  return (
    <>
      <h3>Конспекты</h3>
      <ReadState query={lectures}>
        {(data) => (
          <>
            {!data.items.length && <p>Конспектов пока нет.</p>}
            <ReadFiles
              files={data.items.flatMap((l) => (l.file ? [l.file] : []))}
            />
            {data.total > state.limit && (
              <Pages
                label="Страницы конспектов"
                state={state}
                total={data.total}
              />
            )}
          </>
        )}
      </ReadState>
      <h3>Условия заданий</h3>
      <ReadState query={homeworks}>
        {(data) => (
          <>
            {!data.length && <p>Заданий пока нет.</p>}
            {data.map((h) => (
              <article key={h.id}>
                <h4>{h.title}</h4>
                <p>
                  <PlainTextLinks text={h.description} />
                </p>
                <ReadFiles files={h.file ? [h.file] : []} />
              </article>
            ))}
          </>
        )}
      </ReadState>
      {!embedded && (
        <Link to={`/teacher/students/${studentId}`}>К ученику</Link>
      )}
    </>
  );
}
