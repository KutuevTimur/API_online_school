import { accessLabel, provisional, type Booking } from '../booking/api';
import { BookingPanel } from '../booking/BookingPanel';
import { WeeklyNeeds } from './WeeklyNeeds';
import { WeeklyEarnings } from './WeeklyEarnings';
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type DragEvent,
} from 'react';
import { Link, useLocation, useSearchParams } from 'react-router';
import { ActionIcon, Button, Checkbox, Menu, Modal } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import {
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  CalendarClock,
  CalendarX,
} from 'lucide-react';
import { usePageTitle } from '../../app/router';
import { useRead, type Page, type Lesson } from '../courses/queries';
import { ReadState, Views } from '../courses/ReadUI';
import {
  moscow,
  weekStart,
  weekWindow,
  lessonStatus,
} from '../../shared/lib/datetime';
import { useModalIsolation } from '../../shared/lib/modalIsolation';
import { LessonEditor } from './LessonEditor';
import { LessonStatusDialog } from './LessonStatusDialog';
import { calendarSlotHeights, droppedHour } from './lessonChanges';
import { useLessonUndo } from './useLessonUndo';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { OverlapWarnings } from './OverlapWarnings';
import { RegularDialog } from './RegularDialog';
import { previewRegularChange, type RegularOperation } from './planning';
import styles from './teacherCalendar.module.css';

export function TeacherSchedulePage() {
  usePageTitle('Расписание преподавателя');
  const desktop = useMediaQuery('(min-width:1024px)');
  const [params, set] = useSearchParams();
  const location = useLocation();
  const weekParam = params.get('week');
  const start = useMemo(() => weekStart(weekParam), [weekParam]);
  const days = Array.from({ length: 7 }, (_, i) => start.add(i, 'day'));
  const raw = Number(params.get('day') ?? (moscow().day() + 6) % 7);
  const day = raw >= 0 && raw <= 6 && Number.isInteger(raw) ? raw : 0;
  const view = ['active', 'archive', 'all'].includes(params.get('view') || '')
    ? params.get('view')!
    : 'active';
  const includeCancelled = view !== 'active' || params.get('cancelled') === '1';
  const update = (values: Record<string, string | number>) => {
    const next = new URLSearchParams(params);
    if (values.week) {
      next.delete('booking_cursor');
      next.delete('window_cursor');
    }
    Object.entries(values).forEach(([k, v]) => next.set(k, String(v)));
    set(next);
  };
  const query = useRead<Page<Lesson>>(
    '/lessons',
    {
      ...weekWindow(start.format('YYYY-MM-DD')),
      view,
      sort_date: 'asc',
      limit: 1000,
      offset: 0,
    },
    true,
    60000,
  );
  const bookingQuery = useRead<{
    items: Booking[];
    next_cursor?: string | null;
  }>(
    '/teacher-planning/booking-calendar',
    { week_start: start.format('YYYY-MM-DD') },
    true,
    60000,
  );
  const pendingBookings = provisional(
    bookingQuery.data?.items || [],
    query.data?.items.map((l) => l.id) || [],
  );
  const lessons = useMemo(
    () =>
      (query.data?.items || []).filter(
        (l) => includeCancelled || l.status !== 'cancelled',
      ),
    [query.data, includeCancelled],
  );
  const slotHeights = useMemo(
    () =>
      calendarSlotHeights([
        ...lessons.map((l) => moscow(l.scheduled_at).hour()),
        ...pendingBookings.map((b) => moscow(b.start_at).hour()),
      ]),
    [lessons, pendingBookings],
  );
  const slotStyle = (n: number) =>
    ({ '--calendar-slot-height': `${slotHeights[n]}px` }) as CSSProperties;
  const calendar = useRef<HTMLDivElement>(null);
  const positionedWeek = useRef('');
  const weekKey = start.format('YYYY-MM-DD') + view + includeCancelled + day;
  const [adding, setAdding] = useState('');
  const [editing, setEditing] = useState<{
    lesson: Lesson;
    initial: string;
  } | null>(null);
  const [cancelling, setCancelling] = useState<Lesson | null>(null);
  const [restoring, setRestoring] = useState<Lesson | null>(null);
  const [overlapHour, setOverlapHour] = useState<string | null>(null);
  const [dragging, setDragging] = useState<number | null>(null);
  const draggingId = useRef<number | null>(null);
  const dragPointer = useRef<number | null>(null);
  const scrollFrame = useRef<number | null>(null);
  const lastScrollFrame = useRef(0);
  const [drop, setDrop] = useState('');
  const [menuOpened, setMenuOpened] = useState<number | null>(null);
  const [warnings, setWarnings] = useState<NonNullable<Lesson['warnings']>>([]);
  const [operation, setOperation] = useState<RegularOperation | null>(null);
  const [seriesPending, setSeriesPending] = useState(false);
  const [seriesError, setSeriesError] = useState('');
  const saved = useLessonUndo();
  const feedback = useFeedback();
  const recordChange = (before: Lesson, after: Lesson) => {
    setWarnings(after.warnings || []);
    saved(before, after);
    requestAnimationFrame(() =>
      calendar.current?.focus({ preventScroll: true }),
    );
  };
  const back = location.pathname + location.search;
  useModalIsolation(!!overlapHour);
  useEffect(() => {
    if (
      !query.data ||
      query.isFetching ||
      bookingQuery.isPending ||
      !calendar.current ||
      !desktop ||
      positionedWeek.current === weekKey
    )
      return;
    positionedWeek.current = weekKey;
    const visible = query.data.items.filter(
      (l) => includeCancelled || l.status !== 'cancelled',
    );
    const selectedDate = start.add(day, 'day');
    const selectedItems = visible.filter((l) =>
      moscow(l.scheduled_at).isSame(selectedDate, 'day'),
    );
    const hours = (selectedItems.length ? selectedItems : visible)
      .map((l) => moscow(l.scheduled_at).hour())
      .filter((h) => h >= 8 && h < 22);
    hours.push(
      ...pendingBookings
        .filter((b) => moscow(b.start_at).isSame(selectedDate, 'day'))
        .map((b) => moscow(b.start_at).hour())
        .filter((h) => h >= 8 && h < 22),
    );
    const hour = hours.length ? Math.max(8, Math.min(...hours) - 1) : 8;
    const row = calendar.current.querySelector<HTMLElement>(
      `[data-time-label="${hour}"]`,
    );
    if (row) calendar.current.scrollTop = row.offsetTop - 52;
  }, [
    query.data,
    query.isFetching,
    bookingQuery.isPending,
    pendingBookings,
    weekKey,
    includeCancelled,
    day,
    start,
    desktop,
  ]);
  const stopDrag = () => {
    draggingId.current = null;
    dragPointer.current = null;
    if (scrollFrame.current !== null) cancelAnimationFrame(scrollFrame.current);
    scrollFrame.current = null;
    lastScrollFrame.current = 0;
    setDragging(null);
    setDrop('');
  };
  useEffect(() => {
    const resize = () => setMenuOpened(null);
    const escape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        draggingId.current = null;
        dragPointer.current = null;
        if (scrollFrame.current !== null)
          cancelAnimationFrame(scrollFrame.current);
        scrollFrame.current = null;
        setDragging(null);
        setDrop('');
      }
    };
    window.addEventListener('keydown', escape);
    window.addEventListener('resize', resize);
    return () => {
      window.removeEventListener('keydown', escape);
      window.removeEventListener('resize', resize);
      if (scrollFrame.current !== null)
        cancelAnimationFrame(scrollFrame.current);
    };
  }, []);
  function scrollWhileDragging(time: number) {
    scrollFrame.current = null;
    const panel = calendar.current;
    const pointer = dragPointer.current;
    if (!panel || pointer === null || draggingId.current === null) return;
    const rect = panel.getBoundingClientRect();
    const speed =
      pointer < rect.top + 96
        ? -Math.min(16, (rect.top + 96 - pointer) / 3)
        : pointer > rect.bottom - 56
          ? Math.min(16, (pointer - rect.bottom + 56) / 3)
          : 0;
    if (!speed) {
      lastScrollFrame.current = 0;
      return;
    }
    const elapsed = lastScrollFrame.current
      ? Math.min(32, time - lastScrollFrame.current)
      : 16;
    lastScrollFrame.current = time;
    const previous = panel.scrollTop;
    panel.scrollTop += (speed * elapsed) / 16;
    if (panel.scrollTop === previous) {
      lastScrollFrame.current = 0;
      return;
    }
    scrollFrame.current = requestAnimationFrame(scrollWhileDragging);
  }
  function beginMove(lesson: Lesson, initial = lesson.scheduled_at) {
    setMenuOpened(null);
    setOverlapHour(null);
    setEditing({ lesson, initial });
  }
  function acceptDrop(e: DragEvent, date: string, hour: number) {
    e.preventDefault();
    const lesson = lessons.find((l) => l.id === draggingId.current);
    const initial = droppedHour(date, hour);
    stopDrag();
    if (
      lesson?.can_manage &&
      lesson.status === 'scheduled' &&
      initial &&
      !moscow(initial).isSame(moscow(lesson.scheduled_at))
    )
      beginMove(lesson, initial);
  }
  function event(lesson: Lesson, list = false) {
    const sourceBooking = bookingQuery.data?.items.find(
      (b) => b.lesson_id === lesson.id,
    );
    const label =
      lesson.student_labels?.map((s) => s.display_name).join(', ') ||
      lesson.course_name ||
      lesson.title;
    const draggable =
      !!lesson.can_manage && lesson.status === 'scheduled' && !list && desktop;
    return (
      <article
        key={sourceBooking?.booking_id || lesson.id}
        data-calendar-booking-id={sourceBooking?.booking_id}
        className={`${styles.event} ${list ? styles.listEvent : ''}`}
        data-status={lesson.status}
        data-dragging={dragging === lesson.id}
        draggable={draggable}
        onDragStart={(e) => {
          if (
            !draggable ||
            (e.target instanceof Element && e.target.closest('button'))
          ) {
            e.preventDefault();
            return;
          }
          draggingId.current = lesson.id;
          setDragging(lesson.id);
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', String(lesson.id));
        }}
        onDragEnd={stopDrag}
      >
        <Link
          draggable={false}
          className={styles.eventLink}
          to={`/teacher/lessons/${lesson.id}`}
          state={{ returnTo: back }}
          aria-label={`Открыть занятие: ${moscow(lesson.scheduled_at).format('HH:mm')} ${label} ${lessonStatus(lesson.status)}`}
        >
          <span className={styles.eventTime}>
            {moscow(lesson.scheduled_at).format('HH:mm')}
          </span>{' '}
          <strong className={styles.eventName}>{label}</strong>{' '}
          <span className={styles.mobileStatus}>
            {lessonStatus(lesson.status)}
          </span>
        </Link>
        <Menu
          withInitialFocusPlaceholder={false}
          portalProps={{ target: '#main' }}
          withinPortal
          width={300}
          position="bottom-end"
          shadow="md"
          returnFocus
          opened={menuOpened === lesson.id}
          onChange={(opened) => setMenuOpened(opened ? lesson.id : null)}
          styles={{
            itemLabel: { whiteSpace: 'normal', overflowWrap: 'anywhere' },
          }}
        >
          <Menu.Target>
            <ActionIcon
              className={styles.eventMenu}
              variant="subtle"
              color="var(--lgg-ink)"
              size={44}
              aria-label={`Управление занятием: ${label}, ${moscow(lesson.scheduled_at).format('HH:mm')}`}
            >
              <MoreHorizontal size={20} aria-hidden="true" />
            </ActionIcon>
          </Menu.Target>
          <Menu.Dropdown style={{ maxWidth: 'calc(100vw - 24px)' }}>
            <Menu.Label className={styles.menuLabel}>
              {label} · {lessonStatus(lesson.status)}
              {lesson.topic ? ` · ${lesson.topic}` : ''}
            </Menu.Label>
            <Menu.Item
              component={Link}
              to={`/teacher/lessons/${lesson.id}`}
              state={{ returnTo: back }}
            >
              Открыть занятие
            </Menu.Item>
            {lesson.can_manage && lesson.status === 'scheduled' && (
              <>
                <Menu.Item
                  leftSection={<CalendarClock size={18} aria-hidden="true" />}
                  onClick={() => beginMove(lesson)}
                >
                  Перенести
                </Menu.Item>
                <Menu.Item
                  color="var(--lgg-danger)"
                  leftSection={<CalendarX size={18} aria-hidden="true" />}
                  onClick={() => {
                    setMenuOpened(null);
                    setOverlapHour(null);
                    setCancelling(lesson);
                  }}
                >
                  Отменить занятие
                </Menu.Item>
                {lesson.regular_series_id && (
                  <Menu.Item
                    disabled={seriesPending}
                    onClick={() => {
                      if (seriesPending) return;
                      setMenuOpened(null);
                      setOverlapHour(null);
                      setSeriesPending(true);
                      setSeriesError('');
                      void previewRegularChange(lesson, 'cancel_future')
                        .then(setOperation)
                        .catch(() =>
                          setSeriesError(
                            'Не удалось загрузить даты серии. Занятия не отменены; откройте занятие для проверки состояния.',
                          ),
                        )
                        .finally(() => setSeriesPending(false));
                    }}
                  >
                    Отменить будущие встречи серии…
                  </Menu.Item>
                )}
              </>
            )}
            {lesson.can_manage && lesson.status === 'cancelled' && (
              <Menu.Item
                onClick={() => {
                  setMenuOpened(null);
                  setOverlapHour(null);
                  setRestoring(lesson);
                }}
              >
                Восстановить занятие
              </Menu.Item>
            )}
            {(lesson.student_labels || []).map((s) => (
              <Menu.Item
                key={s.user_id}
                component={Link}
                to={`/teacher/students/${s.user_id}`}
              >
                К ученику: {s.display_name}
              </Menu.Item>
            ))}
            <Menu.Item
              component={Link}
              to={`/teacher/courses/${lesson.course_id}`}
            >
              {lesson.course_name || 'Курс'}
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </article>
    );
  }
  const overlapItems = lessons.filter(
    (l) => moscow(l.scheduled_at).format('YYYY-MM-DD-HH') === overlapHour,
  );
  return (
    <>
      <header className={styles.heading}>
        <h1>Расписание</h1>
        <Button
          onClick={() =>
            setAdding(droppedHour(days[day].format('YYYY-MM-DD'), 15)!)
          }
        >
          Добавить занятие
        </Button>
      </header>
      <div className={styles.controls}>
        <div className={styles.weekNavigation} aria-label="Выбор недели">
          <ActionIcon
            size={44}
            variant="default"
            aria-label="Предыдущая неделя"
            onClick={() =>
              update({ week: start.subtract(7, 'day').format('YYYY-MM-DD') })
            }
          >
            <ChevronLeft size={20} aria-hidden="true" />
          </ActionIcon>
          <h2 aria-live="polite">
            {start.format('D MMM')} — {start.add(6, 'day').format('D MMM YYYY')}
          </h2>
          <ActionIcon
            size={44}
            variant="default"
            aria-label="Следующая неделя"
            onClick={() =>
              update({ week: start.add(7, 'day').format('YYYY-MM-DD') })
            }
          >
            <ChevronRight size={20} aria-hidden="true" />
          </ActionIcon>
          <Button
            variant="default"
            aria-pressed={start.isSame(weekStart(), 'day')}
            onClick={() =>
              update({
                week: weekStart().format('YYYY-MM-DD'),
                day: (moscow().day() + 6) % 7,
              })
            }
          >
            Текущая неделя
          </Button>
        </div>
        <details className={styles.history}>
          <summary>История и отменённые</summary>
          <div className={styles.filters}>
            <Views value={view} onChange={(v) => update({ view: v })} />
            <Checkbox
              label="Показать отменённые"
              checked={includeCancelled}
              disabled={view !== 'active'}
              onChange={(e) =>
                update({ cancelled: e.currentTarget.checked ? '1' : '0' })
              }
            />
          </div>
        </details>
      </div>
      <p className={styles.caption}>МСК · 08:00–22:00 · по времени начала</p>
      <div className={styles.dayButtons} aria-label="День недели">
        {days.map((d, i) => {
          const count = lessons.filter((l) =>
            moscow(l.scheduled_at).isSame(d, 'day'),
          ).length;
          return (
            <Button
              key={i}
              variant={day === i ? 'filled' : 'default'}
              aria-pressed={day === i}
              aria-label={`${d.format('dd D')} ${count || '—'} · ${d.format('D MMMM')}, занятий: ${count}`}
              onClick={() => update({ day: i })}
            >
              <span>
                {d.format('dd')}
                <br /> {d.format('D')}{' '}
                <span aria-hidden="true" className={styles.dayCount}>
                  {count || '—'}
                </span>
              </span>
            </Button>
          );
        })}
      </div>
      {seriesPending && <p role="status">Загружаем даты серии…</p>}
      {seriesError && <p role="alert">{seriesError}</p>}
      {!!warnings.length && <OverlapWarnings warnings={warnings} />}
      {bookingQuery.isPending && (
        <p role="status">Загружаем подтверждённые брони…</p>
      )}
      {bookingQuery.isError && (
        <p role="alert">
          Не удалось обновить брони. Расписание может быть неполным.{' '}
          <Button variant="default" onClick={() => void bookingQuery.refetch()}>
            Повторить загрузку броней
          </Button>
        </p>
      )}
      {bookingQuery.data?.next_cursor && (
        <p role="alert">
          В неделе больше 100 броней. Проверьте полный список записи ниже.
        </p>
      )}
      <div className={styles.calendarRegion} data-schedule-region>
        <ReadState query={query}>
          {(data) =>
            data.total > 1000 ? (
              <p role="alert">
                Слишком много занятий в одной неделе. Откройте занятия нужного
                ученика.
              </p>
            ) : (
              <div
                ref={calendar}
                tabIndex={-1}
                className={styles.calendar}
                aria-label="Календарь недели"
                onDragOver={(e) => {
                  if (draggingId.current === null) return;
                  dragPointer.current = e.clientY;
                  if (scrollFrame.current === null)
                    scrollFrame.current =
                      requestAnimationFrame(scrollWhileDragging);
                }}
                onDragLeave={(e) => {
                  if (
                    !(e.relatedTarget instanceof Node) ||
                    !e.currentTarget.contains(e.relatedTarget)
                  ) {
                    dragPointer.current = null;
                    setDrop('');
                  }
                }}
              >
                <div className={styles.timeAxis} aria-hidden="true">
                  <div className={styles.axisHeader} />
                  {Array.from({ length: 14 }, (_, n) => (
                    <div
                      key={n}
                      className={styles.timeLabel}
                      style={slotStyle(n)}
                      data-compact={slotHeights[n] === 44}
                      data-time-label={n + 8}
                    >
                      {String(n + 8).padStart(2, '0')}:00
                    </div>
                  ))}
                </div>
                {days.map((d, i) => {
                  const items = lessons.filter(
                    (l) =>
                      moscow(l.scheduled_at).isSame(d, 'day') &&
                      moscow(l.scheduled_at).hour() >= 8 &&
                      moscow(l.scheduled_at).hour() < 22,
                  );
                  return (
                    <section
                      key={i}
                      className={styles.day}
                      data-selected={day === i}
                      data-today={d.isSame(moscow(), 'day')}
                    >
                      <h3>
                        {d.format('dd')} <span>{d.format('D MMM')}</span>
                      </h3>
                      <div className={styles.timeline}>
                        {Array.from({ length: 14 }, (_, n) => n + 8).map(
                          (hour) => {
                            const slot = items.filter(
                              (l) => moscow(l.scheduled_at).hour() === hour,
                            );
                            const initial = droppedHour(
                              d.format('YYYY-MM-DD'),
                              hour,
                            )!;
                            const key =
                              d.format('YYYY-MM-DD-') +
                              String(hour).padStart(2, '0');
                            return (
                              <div
                                key={hour}
                                className={styles.hour}
                                style={slotStyle(hour - 8)}
                                data-compact={slotHeights[hour - 8] === 44}
                                data-hour={hour}
                                data-drop={drop === initial}
                                onDragOver={(e) => {
                                  if (draggingId.current === null) return;
                                  e.preventDefault();
                                  e.dataTransfer.dropEffect = 'move';
                                  if (drop !== initial) setDrop(initial);
                                }}
                                onDrop={(e) =>
                                  acceptDrop(e, d.format('YYYY-MM-DD'), hour)
                                }
                              >
                                <button
                                  type="button"
                                  className={styles.addSlot}
                                  aria-label={`Добавить занятие ${d.format('D MMMM')} ${String(hour).padStart(2, '0')}:00 МСК`}
                                  onClick={() => setAdding(initial)}
                                />
                                {slot.length > 1 ? (
                                  <>
                                    <button
                                      type="button"
                                      className={styles.overlaps}
                                      onClick={() => setOverlapHour(key)}
                                    >
                                      {String(hour).padStart(2, '0')}:00 ·{' '}
                                      {slot.length} занятия
                                      <span>
                                        {slot
                                          .map(
                                            (l) =>
                                              l.student_labels
                                                ?.map((s) => s.display_name)
                                                .join(', ') || l.title,
                                          )
                                          .join(', ')}
                                      </span>
                                    </button>
                                    <div className={styles.mobileOverlap}>
                                      {slot.map((l) => event(l, true))}
                                    </div>
                                  </>
                                ) : (
                                  slot.map((l) => event(l))
                                )}
                                {pendingBookings
                                  .filter(
                                    (b) =>
                                      moscow(b.start_at).isSame(d, 'day') &&
                                      moscow(b.start_at).hour() === hour,
                                  )
                                  .map((b) => (
                                    <article
                                      key={b.booking_id}
                                      data-booking-id={b.booking_id}
                                      data-calendar-booking-id={b.booking_id}
                                      className={styles.bookingEvent}
                                    >
                                      <a
                                        href="#booking-management"
                                        aria-label={`${moscow(b.start_at).format('HH:mm')} ${b.recipient.first_name} ${b.recipient.last_name}. Бронь подтверждена. ${accessLabel(b.access_state)}`}
                                      >
                                        <span className={styles.bookingName}>
                                          {moscow(b.start_at).format('HH:mm')}{' '}
                                          {b.recipient.first_name}{' '}
                                          {b.recipient.last_name}
                                        </span>
                                        <span>Бронь подтверждена</span>
                                      </a>
                                    </article>
                                  ))}
                                {drop === initial && (
                                  <span
                                    className={styles.dropPreview}
                                    aria-hidden="true"
                                  >
                                    {String(hour).padStart(2, '0')}:00
                                  </span>
                                )}
                              </div>
                            );
                          },
                        )}
                      </div>
                      {!items.length &&
                        !pendingBookings.some((b) =>
                          moscow(b.start_at).isSame(d, 'day'),
                        ) && (
                          <p className={styles.empty}>Нет занятий или броней</p>
                        )}
                    </section>
                  );
                })}
              </div>
            )
          }
        </ReadState>
      </div>
      <p role="status" className={styles.dragStatus}>
        {drop
          ? `Новое время: ${moscow(drop).format('D MMMM, HH:mm')} МСК. Отпустите для подтверждения переноса.`
          : 'Нажатие открывает занятие. Действия — в меню ⋯.'}
      </p>
      <div id="booking-management">
        <BookingPanel week={start.format('YYYY-MM-DD')} />
      </div>
      <WeeklyNeeds week={start.format('YYYY-MM-DD')} />
      <WeeklyEarnings week={start.format('YYYY-MM-DD')} />
      {adding && (
        <LessonEditor
          initial={adding}
          calendarMode
          onClose={() => setAdding('')}
        />
      )}
      {editing && (
        <LessonEditor
          lesson={editing.lesson}
          initial={editing.initial}
          calendarMode
          onClose={() => setEditing(null)}
          onSaved={recordChange}
        />
      )}
      {cancelling && (
        <LessonStatusDialog
          lesson={cancelling}
          status="cancelled"
          onClose={() => setCancelling(null)}
          onSaved={recordChange}
        />
      )}
      {restoring && (
        <LessonStatusDialog
          lesson={restoring}
          status="scheduled"
          onClose={() => setRestoring(null)}
          onSaved={() => feedback('Занятие восстановлено.')}
        />
      )}
      {operation && (
        <RegularDialog
          operation={operation}
          onClose={() => setOperation(null)}
          onSaved={() => setOperation(null)}
        />
      )}
      <Modal
        opened={!!overlapHour}
        onClose={() => setOverlapHour(null)}
        title="Занятия в одном часу"
        closeButtonProps={{ 'aria-label': 'Закрыть' }}
      >
        <div className={styles.overlapList}>
          {overlapItems.map((l) => event(l, true))}
        </div>
      </Modal>
    </>
  );
}
