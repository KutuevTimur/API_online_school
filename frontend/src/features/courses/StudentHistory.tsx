import { useState } from 'react';
import { useMediaQuery } from '@mantine/hooks';
import { Button, Group } from '@mantine/core';
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FileText,
  NotebookPen,
  History,
  CheckCheck,
} from 'lucide-react';
import { Link, useLocation, useSearchParams } from 'react-router';
import { dateLabel, lessonStatus, moscow } from '../../shared/lib/datetime';
import { SelectField } from '../../shared/ui/SelectField';
import { LinkButton } from '../../shared/ui/LinkButton';
import { PlainTextLinks } from '../../shared/ui/PlainTextLinks';
import {
  useRead,
  type Page,
  type Lesson,
  type Lecture,
  type Homework,
} from './queries';
import { Pages, ReadFiles, ReadState, useListState } from './ReadUI';
import styles from './read.module.css';
import { historyMonth, historyMonthWindow } from './studentHistoryDates';

function LessonLink({
  lesson,
  studentId,
}: {
  lesson: Lesson;
  studentId: string;
}) {
  const location = useLocation();
  return (
    <LinkButton
      to={`/teacher/lessons/${lesson.id}?student=${studentId}`}
      state={{
        returnTo: location.pathname + location.search,
        studentListSearch: location.state?.studentListSearch,
      }}
      className={styles.action}
    >
      Открыть занятие
    </LinkButton>
  );
}

function MaterialFiles({
  lessonId,
  studentId,
  owner,
}: {
  lessonId: number;
  studentId: string;
  owner: string;
}) {
  const state = useListState(`${owner}-files-`);
  const params = { lesson_id: String(lessonId), student_user_id: studentId };
  const lectures = useRead<Page<Lecture>>('/lectures', {
    ...params,
    limit: state.limit,
    offset: state.offset,
  });
  const homeworks = useRead<Homework[]>('/homeworks', params);
  return (
    <div className={styles.studentMaterials}>
      <section>
        <h3>
          <FileText size={18} aria-hidden="true" />
          Конспекты
        </h3>
        <ReadState query={lectures}>
          {(data) => (
            <>
              {!data.items.length && <p>Конспектов пока нет.</p>}
              <ReadFiles
                owner={`${owner}-lectures`}
                files={data.items.flatMap((l) => (l.file ? [l.file] : []))}
              />
              <Pages
                state={state}
                total={data.total}
                label="Страницы конспектов"
              />
            </>
          )}
        </ReadState>
      </section>
      <section>
        <h3>
          <NotebookPen size={18} aria-hidden="true" />
          Домашнее задание
        </h3>
        <ReadState query={homeworks}>
          {(data) => (
            <>
              {!data.length && <p>Заданий пока нет.</p>}
              {data.map((h) => (
                <article className={styles.studentHomework} key={h.id}>
                  <h4>{h.title}</h4>
                  <p className={styles.materialLabel}>Что сделать</p>
                  {h.description ? (
                    <div className={styles.lessonCopy}>
                      <PlainTextLinks text={h.description} />
                    </div>
                  ) : (
                    <p>Текст условия не добавлен.</p>
                  )}
                  {h.file && (
                    <>
                      <p className={styles.materialLabel}>Файл задания</p>
                      <ReadFiles
                        condition
                        owner={`${owner}-homework-${h.id}`}
                        files={[h.file]}
                      />
                    </>
                  )}
                </article>
              ))}
            </>
          )}
        </ReadState>
      </section>
    </div>
  );
}

function LessonRows({
  lessons,
  studentId,
}: {
  lessons: Lesson[];
  studentId: string;
}) {
  const [params, set] = useSearchParams();
  const location = useLocation();
  const expanded = params.get('history-lesson');
  return (
    <ul
      className={styles.studentLessonList}
      aria-label="Занятия выбранного месяца"
    >
      {lessons.map((lesson) => {
        const open = expanded === String(lesson.id);
        return (
          <li key={lesson.id} className={styles.studentLessonRow}>
            <button
              type="button"
              className={styles.studentLessonToggle}
              aria-expanded={open}
              aria-controls={`history-lesson-${lesson.id}`}
              onClick={() => {
                const next = new URLSearchParams(params);
                if (open) next.delete('history-lesson');
                else next.set('history-lesson', String(lesson.id));
                set(next, { state: location.state, preventScrollReset: true });
              }}
            >
              <span className={styles.studentLessonDate}>
                <time dateTime={lesson.scheduled_at}>
                  {dateLabel(lesson.scheduled_at)}
                </time>
                <span
                  className={styles.historyStatus}
                  data-status={lesson.status}
                >
                  {lesson.is_deleted
                    ? `В архиве · ${lessonStatus(lesson.status)}`
                    : lessonStatus(lesson.status)}
                </span>
              </span>
              <span className={styles.studentLessonTitle}>
                {lesson.title}
                {lesson.topic && lesson.topic !== lesson.title && (
                  <span>{lesson.topic}</span>
                )}
              </span>
              <ChevronDown
                size={20}
                aria-hidden
                style={{ transform: open ? 'rotate(180deg)' : undefined }}
              />
            </button>
            {open && (
              <div
                id={`history-lesson-${lesson.id}`}
                className={styles.studentLessonBody}
              >
                {lesson.access_mode === 'read_only' && (
                  <p>
                    Только просмотр. Материалы доступны для чтения и скачивания.
                  </p>
                )}
                <MaterialFiles
                  lessonId={lesson.id}
                  studentId={studentId}
                  owner={`history-${lesson.id}`}
                />
                <div className={styles.studentLessonFooter}>
                  <LessonLink lesson={lesson} studentId={studentId} />
                </div>
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export function StudentHistory({
  courseId,
  studentId,
}: {
  courseId: number;
  studentId: string;
}) {
  const narrow = useMediaQuery('(max-width: 767px)');
  const [boundary] = useState(() => {
    const second = Math.floor(Date.now() / 1000) * 1000;
    return {
      future: new Date(second).toISOString(),
      past: new Date(second - 1).toISOString().replace('.999Z', '.999999Z'),
      month: moscow().format('YYYY-MM'),
    };
  });
  const location = useLocation();
  const state = useListState('history-');
  const month = historyMonth(state.params.get('history-month'), boundary.month);
  const selected = moscow(`${month}-01T00:00:00+03:00`);
  const monthCount = narrow ? 3 : 5;
  const lastStripMonth = narrow ? '9998-10' : '9998-08';
  const clampStrip = (value: string) =>
    value < '1900-01'
      ? '1900-01'
      : value > lastStripMonth
        ? lastStripMonth
        : value;
  const stripMonth = clampStrip(
    historyMonth(
      state.params.get('history-strip'),
      moscow(`${month}-01T00:00:00+03:00`)
        .subtract(narrow ? 1 : 2, 'month')
        .format('YYYY-MM'),
    ),
  );
  const stripStart = moscow(`${stripMonth}-01T00:00:00+03:00`);
  const window = historyMonthWindow(month);
  const futureMonth = window.from_date > boundary.past;
  const base = { course_id: courseId, student_user_id: Number(studentId) };
  const latest = useRead<Page<Lesson>>('/lessons', {
    ...base,
    status: 'completed',
    view: 'all',
    to_date: boundary.past,
    sort_date: 'desc',
    limit: 1,
    offset: 0,
  });
  const nearest = useRead<Page<Lesson>>('/lessons', {
    ...base,
    status: 'scheduled',
    view: 'active',
    from_date: boundary.future,
    sort_date: 'asc',
    limit: 1,
    offset: 0,
  });
  const history = useRead<Page<Lesson>>(
    '/lessons',
    {
      ...base,
      view: 'all',
      from_date: window.from_date,
      to_date: window.to_date < boundary.past ? window.to_date : boundary.past,
      sort_date: 'desc',
      limit: state.limit,
      offset: state.offset,
    },
    !futureMonth,
  );
  const nextState = useListState('next-');
  const [nextOpen, setNextOpen] = useState(state.params.has('next-offset'));
  const future = useRead<Page<Lesson>>(
    '/lessons',
    {
      ...base,
      view: 'all',
      from_date: boundary.future,
      sort_date: 'asc',
      limit: nextState.limit,
      offset: nextState.offset,
    },
    nextOpen,
  );
  const [params, setParams] = useSearchParams();
  const selectMonth = (value: string, resetStrip = false) => {
    if (historyMonth(value, '') !== value) return;
    const next = new URLSearchParams(params);
    next.set('history-month', value);
    next.set(
      'history-strip',
      resetStrip
        ? clampStrip(
            moscow(`${value}-01T00:00:00+03:00`)
              .subtract(narrow ? 1 : 2, 'month')
              .format('YYYY-MM'),
          )
        : stripMonth,
    );
    next.set('history-offset', '0');
    next.delete('history-lesson');
    for (const key of [...next.keys()])
      if (/^history-\d+-files-/.test(key)) next.delete(key);
    setParams(next, { state: location.state, preventScrollReset: true });
  };
  const moveStrip = (direction: number) => {
    const next = new URLSearchParams(params);
    next.set(
      'history-strip',
      clampStrip(
        stripStart.add(direction * monthCount, 'month').format('YYYY-MM'),
      ),
    );
    setParams(next, { state: location.state, preventScrollReset: true });
  };
  const year = Number(month.slice(0, 4));
  const years = Array.from(
    new Set([year - 1, year, year + 1, Number(boundary.month.slice(0, 4))]),
  )
    .filter((y) => y >= 1900 && y <= 9998)
    .sort((a, b) => b - a);
  return (
    <div
      className={`${styles.studentHistory} ${styles.teacherWorkspaceHistory}`}
    >
      <section
        className={styles.lastLesson}
        aria-label="Последнее проведённое занятие"
        data-read-only={
          latest.data?.items[0]?.is_deleted ||
          latest.data?.items[0]?.access_mode === 'read_only' ||
          undefined
        }
      >
        <h2 className={styles.workspaceSectionTitle}>
          <CheckCheck size={20} aria-hidden="true" />
          Последнее проведённое занятие
        </h2>
        <ReadState query={latest}>
          {(data) =>
            data.items[0] ? (
              <>
                <div className={styles.sectionHeading}>
                  <div>
                    <p className={styles.meetingTime}>
                      {dateLabel(data.items[0].scheduled_at)}
                    </p>
                    <h3>{data.items[0].title}</h3>
                    {data.items[0].topic &&
                      data.items[0].topic !== data.items[0].title && (
                        <p>{data.items[0].topic}</p>
                      )}
                  </div>
                  <LessonLink lesson={data.items[0]} studentId={studentId} />
                </div>
                {(data.items[0].is_deleted ||
                  data.items[0].access_mode === 'read_only') && (
                  <p>Только просмотр · архивная история</p>
                )}
                <MaterialFiles
                  lessonId={data.items[0].id}
                  studentId={studentId}
                  owner="latest"
                />
              </>
            ) : (
              <p>Проведённых занятий пока нет.</p>
            )
          }
        </ReadState>
      </section>
      <section className={styles.monthHistory} aria-label="История занятий">
        <div className={styles.sectionHeading}>
          <h2 className={styles.workspaceSectionTitle}>
            <History size={20} aria-hidden="true" />
            История занятий
          </h2>
          <Group gap="xs" align="flex-end" className={styles.historyControls}>
            <SelectField
              label="Год истории"
              value={String(year)}
              data={years.map((y) => ({ value: String(y), label: String(y) }))}
              onChange={(v) => {
                if (v) selectMonth(`${v}-${month.slice(5)}`, true);
              }}
            />
            <Button
              variant="light"
              onClick={() => selectMonth(boundary.month, true)}
            >
              Текущий месяц
            </Button>
          </Group>
        </div>
        <div
          className={styles.monthStrip}
          role="group"
          aria-label="Месяцы занятий"
        >
          <Button
            variant="default"
            aria-label="Предыдущие месяцы"
            disabled={stripMonth === '1900-01'}
            onClick={() => moveStrip(-1)}
          >
            <ChevronLeft size={20} />
          </Button>
          {Array.from({ length: monthCount }, (_, shift) => {
            const d = stripStart.add(shift, 'month');
            const active = d.format('YYYY-MM') === month;
            return (
              <Button
                key={d.format('YYYY-MM')}
                variant={active ? 'filled' : 'light'}
                aria-pressed={active}
                aria-label={`${narrow ? `${d.format('MMMM').slice(0, 3)} — ` : ''}${d.format('MMMM YYYY')}`}
                onClick={() => selectMonth(d.format('YYYY-MM'))}
              >
                {narrow
                  ? d.format('MMMM').slice(0, 3)
                  : `${d.format('MMMM')}${d.year() !== year ? ` ${d.year()}` : ''}`}
              </Button>
            );
          })}
          <Button
            variant="default"
            aria-label="Следующие месяцы"
            disabled={stripMonth === lastStripMonth}
            onClick={() => moveStrip(1)}
          >
            <ChevronRight size={20} />
          </Button>
        </div>
        <h3 className={styles.monthTitle}>{selected.format('MMMM YYYY')}</h3>
        {futureMonth ? (
          <p>Этот месяц ещё впереди. Будущие встречи доступны ниже.</p>
        ) : (
          <ReadState query={history}>
            {(data) => (
              <>
                <p className={styles.muted}>
                  Занятий за выбранный месяц: {data.total}
                  {data.total > 0
                    ? ` · показано ${Math.min(state.offset + 1, data.total)}–${Math.min(state.offset + data.items.length, data.total)}`
                    : ''}
                </p>
                {!data.items.length && (
                  <p>
                    {state.offset
                      ? 'На этой странице занятий нет. Вернитесь на предыдущую страницу.'
                      : 'Прошедших занятий в этом месяце нет.'}
                  </p>
                )}
                <LessonRows lessons={data.items} studentId={studentId} />
                <Pages
                  label="Страницы занятий месяца"
                  total={data.total}
                  state={state}
                />
              </>
            )}
          </ReadState>
        )}
      </section>
      <section
        className={styles.studentUpcoming}
        aria-label="Ближайшее занятие"
      >
        <h2>Ближайшее занятие</h2>
        <ReadState query={nearest}>
          {(data) =>
            data.items[0] ? (
              <div className={styles.sectionHeading}>
                <p>
                  {dateLabel(data.items[0].scheduled_at)} ·{' '}
                  {data.items[0].title}
                </p>
                <LessonLink lesson={data.items[0]} studentId={studentId} />
              </div>
            ) : (
              <p>
                Ближайших запланированных занятий нет.{' '}
                <Link to="/teacher/schedule">Открыть расписание</Link>
              </p>
            )
          }
        </ReadState>
        <details
          className={styles.secondaryDisclosure}
          open={nextOpen}
          onToggle={(e) => setNextOpen(e.currentTarget.open)}
        >
          <summary>Следующие занятия</summary>
          {nextOpen && (
            <ReadState query={future}>
              {(data) => (
                <>
                  <p className={styles.muted}>
                    Все будущие встречи, включая отменённые и архивные.
                  </p>
                  {!data.items.length && <p>Будущих встреч пока нет.</p>}
                  <ul
                    className={styles.list}
                    aria-label="Следующие занятия ученика"
                  >
                    {data.items.map((l) => (
                      <li className={styles.historyLesson} key={l.id}>
                        <div>
                          <p>
                            {dateLabel(l.scheduled_at)} · {l.title}
                          </p>
                          <small>
                            {l.is_deleted
                              ? `В архиве · ${lessonStatus(l.status)}`
                              : lessonStatus(l.status)}
                          </small>
                        </div>
                        <LessonLink lesson={l} studentId={studentId} />
                      </li>
                    ))}
                  </ul>
                  <Pages
                    label="Страницы следующих занятий"
                    total={data.total}
                    state={nextState}
                  />
                </>
              )}
            </ReadState>
          )}
        </details>
      </section>
    </div>
  );
}
