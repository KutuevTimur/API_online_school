import { useEffect, useId, useRef, useState } from 'react';
import { useMediaQuery } from '@mantine/hooks';
import { Button, Group } from '@mantine/core';
import {
  CalendarDays,
  FileText,
  NotebookPen,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router';
import {
  useInfiniteQuery,
  useIsFetching,
  useQueryClient,
} from '@tanstack/react-query';
import { usePageTitle } from '../../app/router';
import { request } from '../../shared/api/client';
import { dateLabel, lessonStatus, moscow } from '../../shared/lib/datetime';
import { SelectField } from '../../shared/ui/SelectField';
import { Pagination } from '../../shared/ui/Pagination';
import { LinkButton } from '../../shared/ui/LinkButton';
import { useSession } from '../auth/session';
import {
  useRead,
  type Course,
  type Lesson,
  type Lecture,
  type Homework,
  type Page,
} from './queries';
import { Pages, ReadFiles, ReadOnly, ReadState, useListState } from './ReadUI';
import { historyMonth, historyMonthWindow } from './studentHistoryDates';
import styles from './read.module.css';

function HistoryLink({
  to,
  children,
  variant,
}: {
  to: string;
  children: React.ReactNode;
  variant?: 'secondary' | 'homework';
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const origin = {
    studentHistoryReturnTo: location.pathname + location.search,
    studentHistoryScroll: 0,
  };
  return (
    <LinkButton
      to={to}
      navigation={!!variant}
      variant={variant ? 'default' : undefined}
      className={variant === 'secondary' ? styles.latestLessonLink : undefined}
      aria-label={variant === 'secondary' ? 'Открыть занятие' : undefined}
      title={variant === 'secondary' ? 'Открыть занятие' : undefined}
      leftSection={
        variant === 'homework' ? (
          <NotebookPen size={18} aria-hidden="true" />
        ) : undefined
      }
      state={origin}
      onClick={(event) => {
        if (
          event.button !== 0 ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        )
          return;
        event.preventDefault();
        void navigate(to, {
          state: { ...origin, studentHistoryScroll: window.scrollY },
        });
      }}
    >
      {children}
    </LinkButton>
  );
}

function LessonFiles({
  lesson,
  owner,
  compact = false,
}: {
  lesson: Lesson;
  owner: string;
  compact?: boolean;
}) {
  const [lecturesOpen, setLecturesOpen] = useState(false);
  const [homeworksOpen, setHomeworksOpen] = useState(false);
  const lectureRegion = useId();
  const homeworkRegion = useId();
  const auth = useSession();
  const state = useListState(`${owner}-files-`);
  const params = { lesson_id: lesson.id, student_user_id: auth.user?.id };
  const lectures = useRead<Page<Lecture>>(
    '/lectures',
    { ...params, limit: state.limit, offset: state.offset },
    !!auth.user,
  );
  const homeworks = useRead<Homework[]>('/homeworks', params, !!auth.user);
  if (compact)
    return (
      <div className={styles.latestActions}>
        <section aria-label="Конспекты занятия">
          <ReadState query={lectures}>
            {(data) =>
              !data.total ? (
                <p className={styles.latestHint}>Конспект пока не добавлен.</p>
              ) : data.total === 1 &&
                data.items.length === 1 &&
                data.items[0].file ? (
                <ReadFiles
                  material
                  owner={`${owner}-lectures`}
                  files={[data.items[0].file]}
                  singleFileLabel="Конспект"
                />
              ) : (
                <>
                  <Button
                    variant="default"
                    leftSection={<FileText size={18} aria-hidden="true" />}
                    rightSection={<ChevronDown size={16} aria-hidden="true" />}
                    aria-expanded={lecturesOpen}
                    aria-controls={lectureRegion}
                    onClick={() => setLecturesOpen(!lecturesOpen)}
                  >
                    Конспекты · {data.total}
                  </Button>
                  <div
                    id={lectureRegion}
                    hidden={!lecturesOpen}
                    className={styles.latestChoices}
                  >
                    <ReadFiles
                      material
                      owner={`${owner}-lectures`}
                      files={data.items.flatMap((l) =>
                        l.file ? [l.file] : [],
                      )}
                    />
                    <Pages
                      state={state}
                      total={data.total}
                      label="Страницы конспектов занятия"
                    />
                    {data.items.some((l) => !l.file) && (
                      <p>
                        Файл пока недоступен. Откройте занятие или повторите
                        загрузку страницы.
                      </p>
                    )}
                  </div>
                </>
              )
            }
          </ReadState>
        </section>
        <section aria-label="Домашние задания занятия">
          <ReadState query={homeworks}>
            {(data) =>
              !data.length ? (
                <p className={styles.latestHint}>Д/з пока не выдано.</p>
              ) : data.length === 1 ? (
                <HistoryLink
                  variant="homework"
                  to={`/student/homeworks/${data[0].id}`}
                >
                  Д/з
                </HistoryLink>
              ) : (
                <>
                  <Button
                    variant="default"
                    leftSection={<NotebookPen size={18} aria-hidden="true" />}
                    rightSection={<ChevronDown size={16} aria-hidden="true" />}
                    aria-expanded={homeworksOpen}
                    aria-controls={homeworkRegion}
                    onClick={() => setHomeworksOpen(!homeworksOpen)}
                  >
                    Д/з · {data.length}
                  </Button>
                  <div
                    id={homeworkRegion}
                    hidden={!homeworksOpen}
                    className={styles.latestChoices}
                  >
                    {data.map((h) => (
                      <HistoryLink
                        key={h.placement_id || h.id}
                        variant="homework"
                        to={`/student/homeworks/${h.id}`}
                      >
                        {h.title}
                      </HistoryLink>
                    ))}
                  </div>
                </>
              )
            }
          </ReadState>
        </section>
      </div>
    );
  return (
    <div className={styles.historyFiles}>
      <section aria-label="Конспекты выбранного занятия">
        <h4>Конспекты</h4>
        <ReadState query={lectures}>
          {(data) => (
            <>
              {!data.total && <p>Конспект пока не добавлен.</p>}
              <ReadFiles
                owner={`${owner}-lectures`}
                material
                files={data.items.flatMap((l) => (l.file ? [l.file] : []))}
              />
              <Pages
                state={state}
                total={data.total}
                label="Страницы конспектов занятия"
              />
              {data.items.some((l) => !l.file) && (
                <p>
                  Файл пока недоступен. Откройте занятие или повторите загрузку
                  страницы.
                </p>
              )}
            </>
          )}
        </ReadState>
      </section>
      <section aria-label="Домашние задания выбранного занятия">
        <h4>Домашнее задание</h4>
        <ReadState query={homeworks}>
          {(data) => (
            <>
              {!data.length && <p>Домашнее задание пока не выдано.</p>}
              {data.map((h) => (
                <div
                  key={h.placement_id || h.id}
                  className={styles.historyHomework}
                >
                  <p>{h.title}</p>
                  <Group gap="xs">
                    <ReadFiles
                      owner={`${owner}-homework-${h.id}`}
                      condition
                      files={h.file ? [h.file] : []}
                    />
                    <HistoryLink to={`/student/homeworks/${h.id}`}>
                      Открыть домашнее задание
                    </HistoryLink>
                  </Group>
                </div>
              ))}
            </>
          )}
        </ReadState>
      </section>
    </div>
  );
}

function LessonContext({
  lesson,
  courses,
  teacherOnly = false,
}: {
  lesson: Lesson;
  courses: Course[];
  teacherOnly?: boolean;
}) {
  const course = courses.find((c) => c.id === lesson.course_id);
  // A course outside the selector's loaded pages still gets an authorized label.
  const detail = useRead<Course>(`/courses/${lesson.course_id}`, {}, !course);
  if (teacherOnly)
    return (
      <span>
        {course || detail.data
          ? (course || detail.data)?.teacher_name || 'Преподаватель не указан'
          : detail.isError
            ? 'Имя преподавателя недоступно'
            : 'Уточняем преподавателя…'}
        {detail.isError && !course && (
          <Button variant="subtle" onClick={() => void detail.refetch()}>
            Повторить
          </Button>
        )}
      </span>
    );
  return (
    <span>
      {course
        ? `${course.name} · ${course.teacher_name}`
        : detail.data
          ? `${detail.data.name} · ${detail.data.teacher_name}`
          : lesson.course_name || 'Курс'}
      {detail.isError && !course ? ' · имя преподавателя недоступно' : ''}
    </span>
  );
}

function LessonRows({
  lessons,
  courses,
  singleCourse,
}: {
  lessons: Lesson[];
  courses: Course[];
  singleCourse: boolean;
}) {
  const [params, set] = useSearchParams();
  const location = useLocation();
  return (
    <ul
      className={styles.studentLessonList}
      aria-label="Занятия выбранного месяца"
    >
      {lessons.map((lesson) => {
        const open = params.get('history-lesson') === String(lesson.id);
        return (
          <li key={lesson.id} className={styles.studentLessonRow}>
            <button
              type="button"
              className={styles.studentLessonToggle}
              aria-expanded={open}
              aria-controls={`student-history-${lesson.id}`}
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
                <span>
                  {lesson.is_deleted
                    ? 'В архиве · '
                    : lesson.access_mode === 'read_only'
                      ? 'Только просмотр · '
                      : ''}
                  {lessonStatus(lesson.status)}
                </span>
              </span>
              <span className={styles.studentLessonTitle}>
                {lesson.topic || lesson.title}
                {lesson.topic &&
                  lesson.topic !== lesson.title &&
                  lesson.title?.trim() !== 'Занятие' && (
                    <span>{lesson.title}</span>
                  )}
                {!singleCourse && (
                  <LessonContext lesson={lesson} courses={courses} />
                )}
              </span>
              <span className={styles.studentHistoryAction}>
                <span>Материалы</span>
                <ChevronDown
                  size={18}
                  aria-hidden="true"
                  style={{ transform: open ? 'rotate(180deg)' : undefined }}
                />
              </span>
            </button>
            {open && (
              <div
                id={`student-history-${lesson.id}`}
                className={styles.studentLessonBody}
              >
                <ReadOnly
                  mode={lesson.access_mode}
                  reason={lesson.read_only_reason}
                />
                <LessonFiles lesson={lesson} owner={`history-${lesson.id}`} />
                <HistoryLink to={`/student/lessons/${lesson.id}`}>
                  Открыть занятие
                </HistoryLink>
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

function LessonHistory({
  courses,
  courseId,
  singleCourse,
}: {
  courses: Course[];
  courseId?: number;
  singleCourse: boolean;
}) {
  // This SPA has no SSR: restore scroll against the correct first-frame layout,
  // not the desktop strip that would shrink after the media-query effect.
  const narrow = useMediaQuery('(max-width: 767px)', undefined, {
    getInitialValueInEffect: false,
  });
  const [now] = useState(() => {
    const second = Math.floor(Date.now() / 1000) * 1000;
    return {
      month: moscow(new Date(second).toISOString()).format('YYYY-MM'),
      instant: new Date(second).toISOString(),
      past: new Date(second - 1).toISOString().replace('.999Z', '.999999Z'),
    };
  });
  const state = useListState('history-');
  const location = useLocation();
  const [params, set] = useSearchParams();
  const month = historyMonth(params.get('history-month'), now.month);
  const count = narrow ? 3 : 5;
  const lastStrip = narrow ? '9998-10' : '9998-08';
  const clamp = (s: string) =>
    s < '1900-01' ? '1900-01' : s > lastStrip ? lastStrip : s;
  const center = (s: string) =>
    clamp(
      moscow(`${s}-01T00:00:00+03:00`)
        .subtract(narrow ? 1 : 2, 'month')
        .format('YYYY-MM'),
    );
  const strip = clamp(historyMonth(params.get('history-strip'), center(month)));
  const stripStart = moscow(`${strip}-01T00:00:00+03:00`);
  const window = historyMonthWindow(month);
  const current = month === now.month;
  const future = month > now.month;
  const upcomingState = useListState('upcoming-');
  const latest = useRead<Page<Lesson>>('/lessons', {
    course_id: courseId,
    status: 'completed',
    view: 'all',
    sort_date: 'desc',
    limit: 1,
    offset: 0,
  });
  const history = useRead<Page<Lesson>>('/lessons', {
    course_id: courseId,
    view: 'all',
    from_date: window.from_date,
    to_date: current ? now.past : window.to_date,
    sort_date: future ? 'asc' : 'desc',
    limit: state.limit,
    offset: state.offset,
  });
  const upcoming = useRead<Page<Lesson>>(
    '/lessons',
    {
      course_id: courseId,
      view: 'all',
      from_date: now.instant,
      to_date: window.to_date,
      sort_date: 'asc',
      limit: upcomingState.limit,
      offset: upcomingState.offset,
    },
    current,
  );
  const restored = useRef(false);
  const navigate = useNavigate();
  const client = useQueryClient();
  const pendingReads = useIsFetching({ queryKey: ['student-read'] });
  // Child observers subscribe before the passive effect; the live client count
  // also covers the commit before useIsFetching publishes its updated count.
  useEffect(() => {
    if (
      client.isFetching({ queryKey: ['student-read'] }) > 0 ||
      pendingReads > 0 ||
      latest.isPending ||
      history.isPending ||
      (current && upcoming.isPending)
    )
      return;
    const scroll = location.state?.restoreHistoryScroll;
    if (
      !restored.current &&
      typeof scroll === 'number' &&
      Number.isFinite(scroll) &&
      scroll >= 0
    ) {
      restored.current = true;
      globalThis.window.scrollTo(0, scroll);
      // Consume the explicit-return hint in this entry. A later browser Back
      // must use ScrollRestoration's newer position, not this old hint again.
      void navigate(location.pathname + location.search + location.hash, {
        replace: true,
        preventScrollReset: true,
        state: { ...location.state, restoreHistoryScroll: undefined },
      });
    }
  }, [
    client,
    navigate,
    pendingReads,
    latest.isPending,
    history.isPending,
    upcoming.isPending,
    current,
    location,
  ]);
  function change(values: Record<string, string | number>, reset = false) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(values)) next.set(k, String(v));
    if (reset) {
      next.set('history-offset', '0');
      next.set('upcoming-offset', '0');
      next.delete('history-lesson');
    } else if ('history-offset' in values || 'upcoming-offset' in values)
      next.delete('history-lesson');
    set(next, {
      state: { ...location.state, restoreHistoryScroll: undefined },
      preventScrollReset: true,
    });
  }
  function selectMonth(value: string, resetStrip = false) {
    change(
      {
        'history-month': value,
        'history-strip': resetStrip ? center(value) : strip,
      },
      true,
    );
  }
  const year = Number(month.slice(0, 4));
  const years = [
    ...new Set([year - 1, year, year + 1, Number(now.month.slice(0, 4))]),
  ]
    .filter((y) => y >= 1900 && y <= 9998)
    .sort((a, b) => b - a);
  const rows = (data: Page<Lesson>, upcomingGroup = false) => {
    const paging = upcomingGroup ? upcomingState : state;
    const prefix = upcomingGroup ? 'upcoming-' : 'history-';
    return (
      <>
        <div className={styles.historyGroupHeading}>
          <h4>
            {current
              ? upcomingGroup
                ? 'Предстоящие'
                : 'Прошедшие'
              : 'Занятия'}{' '}
            <span>· {data.total}</span>
          </h4>
          {data.items.length > 0 &&
            (paging.offset > 0 || data.total > data.items.length) && (
              <p>
                Показано {Math.min(paging.offset + 1, data.total)}–
                {Math.min(paging.offset + data.items.length, data.total)}
              </p>
            )}
        </div>
        {!data.items.length && (
          <p>
            {paging.offset
              ? 'На этой странице занятий нет. Вернитесь на первую страницу.'
              : upcomingGroup
                ? 'Предстоящих занятий в этом месяце пока нет.'
                : current
                  ? 'Прошедших занятий в этом месяце пока нет.'
                  : 'Занятий в этом месяце пока нет.'}{' '}
            {paging.offset > 0 ? (
              <Button
                variant="default"
                onClick={() => change({ [prefix + 'offset']: 0 })}
              >
                На первую страницу
              </Button>
            ) : (
              <Link to="/student/schedule">К расписанию</Link>
            )}
          </p>
        )}
        <LessonRows
          lessons={data.items}
          courses={courses}
          singleCourse={singleCourse}
        />
        <Pagination
          total={data.total}
          offset={paging.offset}
          limit={paging.limit}
          label={
            upcomingGroup
              ? 'Страницы предстоящих занятий'
              : 'Страницы истории занятий'
          }
          onChange={(offset, limit) =>
            change({ [prefix + 'offset']: offset, [prefix + 'limit']: limit })
          }
        />
      </>
    );
  };
  const last = latest.data?.items[0];
  return (
    <div className={`${styles.studentHistory} ${styles.studentHistoryPage}`}>
      <section
        className={`${styles.lastLesson} ${styles.compactLatest}`}
        aria-label="Последнее проведённое занятие"
        data-read-only={
          last?.access_mode === 'read_only' || last?.is_deleted || undefined
        }
      >
        <div className={styles.latestHeader}>
          <h2>Последнее занятие</h2>
        </div>
        <ReadState query={latest}>
          {(data) =>
            data.items[0] ? (
              <>
                <p className={styles.latestDate}>
                  <CalendarDays size={18} aria-hidden="true" />
                  {dateLabel(data.items[0].scheduled_at)}
                  {data.items[0].is_deleted ? ' · В архиве' : ''}
                </p>
                {(data.items[0].topic?.trim() ||
                  (data.items[0].title?.trim() !== 'Занятие' &&
                    data.items[0].title?.trim())) && (
                  <h3 className={styles.latestTopic}>
                    {data.items[0].topic || data.items[0].title}
                  </h3>
                )}
                <p className={styles.latestContext}>
                  <LessonContext
                    lesson={data.items[0]}
                    courses={courses}
                    teacherOnly={singleCourse}
                  />
                </p>
                <ReadOnly
                  mode={data.items[0].access_mode}
                  reason={data.items[0].read_only_reason}
                />
                <LessonFiles
                  key={data.items[0].id}
                  lesson={data.items[0]}
                  owner="latest"
                  compact
                />
                <div className={styles.latestOpenAction}>
                  <HistoryLink
                    variant="secondary"
                    to={`/student/lessons/${data.items[0].id}`}
                  >
                    Открыть занятие
                  </HistoryLink>
                </div>
              </>
            ) : (
              <p>Проведённых занятий пока нет.</p>
            )
          }
        </ReadState>
      </section>
      <section
        className={`${styles.monthHistory} ${styles.studentMonthlyHistory}`}
        aria-label="История занятий"
      >
        <div className={styles.historyHeader}>
          <h2>История занятий</h2>
          <div className={styles.historyControls}>
            <SelectField
              label="Год"
              allowDeselect={false}
              value={String(year)}
              data={years.map((y) => ({ value: String(y), label: String(y) }))}
              onChange={(v) => {
                if (v) selectMonth(`${v}-${month.slice(5)}`, true);
              }}
            />
            <Button
              variant="default"
              className={styles.historyCurrent}
              onClick={() => selectMonth(now.month, true)}
            >
              Текущий месяц
            </Button>
          </div>
        </div>
        <div
          className={styles.monthStrip}
          role="group"
          aria-label="Месяцы занятий"
        >
          <Button
            variant="default"
            aria-label="Предыдущие месяцы"
            disabled={strip === '1900-01'}
            onClick={() =>
              change({
                'history-strip': clamp(
                  stripStart.subtract(count, 'month').format('YYYY-MM'),
                ),
              })
            }
          >
            <ChevronLeft size={20} aria-hidden />
          </Button>
          {Array.from({ length: count }, (_, i) => {
            const d = stripStart.add(i, 'month');
            return (
              <Button
                key={d.format('YYYY-MM')}
                variant={d.format('YYYY-MM') === month ? 'filled' : 'default'}
                aria-pressed={d.format('YYYY-MM') === month}
                aria-label={
                  narrow
                    ? `${d.format('MMMM').slice(0, 3)}${d.year() !== year ? ` ${d.year()}` : ''} — ${d.format('MMMM YYYY')}`
                    : d.format('MMMM YYYY')
                }
                onClick={() => selectMonth(d.format('YYYY-MM'))}
              >
                {narrow ? d.format('MMMM').slice(0, 3) : d.format('MMMM')}
                {d.year() !== year ? ` ${d.year()}` : ''}
              </Button>
            );
          })}
          <Button
            variant="default"
            aria-label="Следующие месяцы"
            disabled={strip === lastStrip}
            onClick={() =>
              change({
                'history-strip': clamp(
                  stripStart.add(count, 'month').format('YYYY-MM'),
                ),
              })
            }
          >
            <ChevronRight size={20} aria-hidden />
          </Button>
        </div>
        <h3 className={styles.monthTitle}>
          {moscow(`${month}-01T00:00:00+03:00`).format('MMMM YYYY')}
        </h3>
        <ReadState query={history}>{(data) => rows(data)}</ReadState>
        {current && (
          <>
            <ReadState query={upcoming}>{(data) => rows(data, true)}</ReadState>
          </>
        )}
      </section>
    </div>
  );
}

export function StudentLessonsPage() {
  usePageTitle('Мои занятия');
  const location = useLocation();
  const [params, set] = useSearchParams();
  const courses = useInfiniteQuery({
    queryKey: ['student-read', 'history-courses'],
    initialPageParam: 0,
    networkMode: 'always',
    queryFn: ({ signal, pageParam }) =>
      request<Page<Course>>('/courses', {
        params: { view: 'all', limit: 20, offset: pageParam },
        signal,
      }),
    getNextPageParam: (last, pages) => {
      const loaded = pages.reduce((n, p) => n + p.items.length, 0);
      return loaded < last.total && last.items.length ? loaded : undefined;
    },
  });
  const loaded = courses.data?.pages.flatMap((p) => p.items) || [];
  const rawCourse = params.get('course_id');
  const validCourse =
    rawCourse !== null &&
    /^[1-9]\d*$/.test(rawCourse) &&
    Number.isSafeInteger(Number(rawCourse));
  const selectedCourse = useRead<Course>(
    `/courses/${validCourse ? rawCourse : '0'}`,
    {},
    validCourse,
  );
  const invalid = !!rawCourse && !validCourse;
  const singleCourse = courses.data?.pages[0].total === 1;
  function select(value: string | null) {
    const next = new URLSearchParams(params);
    if (value) next.set('course_id', value);
    else next.delete('course_id');
    next.set('history-offset', '0');
    next.set('upcoming-offset', '0');
    next.delete('history-lesson');
    set(next, {
      state: { ...location.state, restoreHistoryScroll: undefined },
      preventScrollReset: true,
    });
  }
  return (
    <>
      <header className={`${styles.heading} ${styles.compactHistoryHeading}`}>
        <h1>Мои занятия</h1>
      </header>
      <ReadState query={courses}>
        {() => (
          <>
            {!loaded.length ? (
              <section className={styles.panel}>
                <h2>Курсов пока нет</h2>
                <p>Здесь появятся ваши занятия после подключения курса.</p>
                <Link to="/student/schedule">К расписанию</Link>
              </section>
            ) : (
              <>
                {singleCourse && loaded[0].is_deleted && (
                  <p className={styles.historyCourse}>
                    Курс: {loaded[0].name} · {loaded[0].teacher_name} · Архив
                  </p>
                )}
                {!singleCourse && (
                  <div className={styles.historyCourse}>
                    <SelectField
                      label="Курс"
                      placeholder="Все курсы"
                      value={validCourse ? rawCourse : null}
                      clearable
                      data={[
                        ...loaded,
                        ...(selectedCourse.data &&
                        !loaded.some((c) => c.id === selectedCourse.data.id)
                          ? [selectedCourse.data]
                          : []),
                      ].map((c) => ({
                        value: String(c.id),
                        label: `${c.name} · ${c.teacher_name}${c.is_deleted ? ' · Архив' : ''}`,
                      }))}
                      onChange={select}
                    />
                    {courses.hasNextPage && (
                      <Button
                        variant="default"
                        loading={courses.isFetchingNextPage}
                        onClick={() => void courses.fetchNextPage()}
                      >
                        Ещё курсы
                      </Button>
                    )}
                  </div>
                )}
                {invalid ? (
                  <section role="alert">
                    <p>Некорректный курс в адресе.</p>
                    <Button variant="default" onClick={() => select(null)}>
                      Все курсы
                    </Button>
                  </section>
                ) : validCourse ? (
                  <ReadState query={selectedCourse}>
                    {(course) => (
                      <>
                        <ReadOnly
                          mode={course.access_mode}
                          reason={course.read_only_reason}
                        />
                        <LessonHistory
                          courses={loaded}
                          courseId={course.id}
                          singleCourse
                        />
                      </>
                    )}
                  </ReadState>
                ) : (
                  <>
                    {singleCourse && (
                      <ReadOnly
                        mode={loaded[0].access_mode}
                        reason={loaded[0].read_only_reason}
                      />
                    )}
                    <LessonHistory
                      courses={loaded}
                      courseId={singleCourse ? loaded[0].id : undefined}
                      singleCourse={singleCourse}
                    />
                  </>
                )}
                {validCourse && selectedCourse.isError && (
                  <Button variant="default" onClick={() => select(null)}>
                    Все курсы
                  </Button>
                )}
              </>
            )}
          </>
        )}
      </ReadState>
    </>
  );
}
