import { moscowToUtc } from '../../shared/lib/time';
import { ErrorSummary, focusFirstError } from '../../shared/ui/ErrorSummary';
import { Pagination } from '../../shared/ui/Pagination';
import { flushSync } from 'react-dom';
import { useEffect, useState } from 'react';
import { Button, Checkbox, Stack } from '@mantine/core';
import { useNavigate, useLocation } from 'react-router';
import { useQueryClient } from '@tanstack/react-query';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { FormField } from '../../shared/ui/FormField';
import { DateField, DateTimeField } from '../../shared/ui/DateTimeField';
import { calendarHours, changeLesson } from './lessonChanges';
import { SelectField } from '../../shared/ui/SelectField';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import {
  useRead,
  type Page,
  type Course,
  type Lesson,
} from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { moscow, weekStart, dateLabel } from '../../shared/lib/datetime';
import {
  normLabel,
  type PlanningStudent,
  type RegularOperation,
  planningRefresh,
} from './planning';
import { RegularDialog } from './RegularDialog';
import styles from './teacherCalendar.module.css';
export function LessonEditor({
  initial,
  onClose,
  lesson,
  calendarMode = false,
  onSaved,
}: {
  initial: string;
  onClose: () => void;
  lesson?: Lesson;
  calendarMode?: boolean;
  onSaved?: (before: Lesson, after: Lesson) => void;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const client = useQueryClient();
  // This editor is conditionally mounted; restore its opener after unmount,
  // when the shared Dialog has released the app's modal isolation.
  const [opener] = useState(() =>
    document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null,
  );
  const dismiss = () => {
    flushSync(() => onClose());
    if (opener?.isConnected) opener.focus({ preventScroll: true });
  };
  const returnTo =
    lesson &&
    typeof location.state?.returnTo === 'string' &&
    /^\/teacher(?:\/|$)/.test(location.state.returnTo)
      ? location.state.returnTo
      : location.pathname + location.search;
  const [baseline] = useState(() => ({
    date: moscow(initial).format('YYYY-MM-DD'),
    time: moscow(initial).format('HH:mm'),
    title: lesson?.title || 'Занятие',
    topic: lesson?.topic || '',
    duration: String(lesson?.duration_minutes || 55),
    override: lesson?.call_url_override || '',
  }));
  const [date, setDate] = useState<string | null>(
    moscow(initial).format('YYYY-MM-DD'),
  );
  const [time, setTime] = useState(moscow(initial).format('HH:mm'));
  const [title, setTitle] = useState(lesson?.title || 'Занятие');
  const [topic, setTopic] = useState(lesson?.topic || '');
  const [duration, setDuration] = useState(
    String(lesson?.duration_minutes || 55),
  );
  const [override, setOverride] = useState(lesson?.call_url_override || '');
  const [student, setStudent] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<{
    value: string;
    label: string;
  } | null>(null);
  const [course, setCourse] = useState('');
  const [q, setQ] = useState('');
  const [search, setSearch] = useState('');
  const [composing, setComposing] = useState(false);
  const [regular, setRegular] = useState(false);
  const [weeks, setWeeks] = useState('4');
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [unknown, setUnknown] = useState(false);
  const [recovered, setRecovered] = useState<Lesson[] | null>(null);
  const [expected, setExpected] = useState(lesson?.updated_at);
  const [serverBefore, setServerBefore] = useState(lesson);
  const [discard, setDiscard] = useState(false);
  const [confirmMove, setConfirmMove] = useState(
    !!lesson && calendarMode && initial !== lesson.scheduled_at,
  );
  const [operation, setOperation] = useState<RegularOperation | null>(null);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState<20 | 50>(20);
  useEffect(() => {
    if (composing) return;
    const timer = setTimeout(
      () => setQ(search === selectedStudent?.label ? '' : search.trim()),
      300,
    );
    return () => clearTimeout(timer);
  }, [search, composing, selectedStudent]);
  const students = useRead<Page<PlanningStudent>>(
    '/teacher-planning/students',
    {
      week: weekStart(date).format('YYYY-MM-DD'),
      q: q || undefined,
      limit,
      offset,
    },
    !lesson,
  );
  const courses = useRead<Page<Course>>(
    '/courses',
    {
      student_user_id: student || undefined,
      view: 'active',
      limit: 1000,
      offset: 0,
    },
    !!student && !lesson,
  );
  const available =
    courses.data?.items.filter((c) => c.can_create_lesson) || [];
  const selectedCourse =
    course || (available.length === 1 ? String(available[0].id) : '');
  const iso = moscowToUtc(date || '', time) || '';
  async function save() {
    if (pending || unknown) return;
    const invalid: Record<string, string> = {};
    if (!iso) invalid['lesson-time'] = 'Выберите дату и укажите время ЧЧ:ММ';
    if (calendarMode && !calendarHours.includes(time))
      invalid['lesson-time'] = 'Выберите целый час с 08:00 до 21:00';
    if (!title.trim()) invalid['lesson-title'] = 'Укажите название занятия';
    if (
      !Number.isInteger(Number(duration)) ||
      Number(duration) < 1 ||
      Number(duration) > 2147483647
    )
      invalid['lesson-duration'] = 'Длительность — положительное целое число';
    if (!lesson && !student) invalid['lesson-student'] = 'Выберите ученика';
    if (!lesson && student && !selectedCourse)
      invalid['lesson-course'] = 'Выберите доступный курс';
    if (
      regular &&
      (!Number.isInteger(Number(weeks)) ||
        Number(weeks) < 1 ||
        Number(weeks) > 12)
    )
      invalid['lesson-weeks'] = 'Укажите 1–12 недель';
    if (override && !/^https?:\/\//i.test(override))
      invalid['lesson-override'] =
        'Ссылка встречи должна начинаться с http:// или https://';
    setErrors(invalid);
    focusFirstError(invalid);
    if (Object.keys(invalid).length) return;
    if (lesson && !confirmMove) {
      setConfirmMove(true);
      return;
    }
    busy(true);
    setError('');
    const body = {
      title: title.trim(),
      topic: topic || null,
      scheduled_at: iso,
      duration_minutes: Number(duration),
      call_url_override: override || null,
    };
    try {
      if (regular && !lesson) {
        const op = await request<RegularOperation>(
          '/lessons/regular/previews',
          {
            method: 'POST',
            body: {
              operation_id: crypto.randomUUID(),
              action: 'create',
              weeks: Number(weeks),
              lesson: {
                ...body,
                course_id: Number(selectedCourse),
                student_user_id: Number(student),
              },
            },
          },
        );
        setOperation(op);
      } else {
        const result = lesson
          ? await changeLesson(
              { ...lesson, updated_at: expected ?? lesson.updated_at },
              calendarMode ? { scheduled_at: iso } : body,
            )
          : await request<Lesson>('/lessons', {
              method: 'POST',
              body: {
                ...body,
                course_id: Number(selectedCourse),
                student_user_id: Number(student),
              },
            });
        await client.invalidateQueries(planningRefresh);
        if (lesson && onSaved) {
          onSaved(serverBefore || lesson, result);
          dismiss();
          return;
        }
        flushSync(() => onClose());
        navigate(`/teacher/lessons/${result.id}`, {
          state: {
            returnTo,
            studentListSearch: location.state?.studentListSearch,
            savedWarnings: result.warnings,
          },
        });
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Не удалось сохранить');
      setUnknown(
        !(e instanceof ApiError) ||
          !e.status ||
          e.status === 401 ||
          e.status === 409 ||
          e.status >= 500,
      );
    } finally {
      busy(false);
    }
  }
  const dirty =
    date !== baseline.date ||
    time !== baseline.time ||
    title !== baseline.title ||
    topic !== baseline.topic ||
    duration !== baseline.duration ||
    override !== baseline.override ||
    !!student ||
    !!course ||
    regular ||
    weeks !== '4';
  const protectedForm = dirty || unknown || pending;
  const close = () => {
    if (pending) return;
    if (protectedForm) setDiscard(true);
    else dismiss();
  };
  if (operation)
    return (
      <RegularDialog
        operation={operation}
        onClose={() => setOperation(null)}
        onSaved={async (op) => {
          await client.invalidateQueries(planningRefresh);
          onClose();
          const id = op.result?.lesson_ids[0];
          if (id)
            navigate(`/teacher/lessons/${id}`, {
              state: {
                returnTo,
                studentListSearch: location.state?.studentListSearch,
              },
            });
        }}
      />
    );
  return (
    <>
      <DirtyFormGuard dirty={protectedForm} />
      <ConfirmDialog
        opened
        title={
          discard
            ? 'Закрыть форму занятия?'
            : lesson
              ? 'Перенести занятие'
              : 'Добавить занятие'
        }
        confirmLabel={
          discard
            ? 'Закрыть форму'
            : regular
              ? 'Предпросмотр записи'
              : lesson
                ? confirmMove
                  ? 'Подтвердить перенос'
                  : 'Проверить перенос'
                : 'Добавить занятие'
        }
        pending={pending}
        error={error}
        confirmDisabled={!discard && unknown}
        onCancel={() => (discard ? setDiscard(false) : close())}
        onConfirm={() => (discard ? dismiss() : void save())}
      >
        {discard ? (
          <p>
            Введённые данные не сохранятся. Проверьте расписание, если результат
            запроса неизвестен.
          </p>
        ) : (
          <Stack>
            <ErrorSummary errors={errors} />
            {calendarMode ? (
              <>
                <DateField
                  label="Дата занятия"
                  value={date}
                  onChange={(v) => {
                    setDate(v);
                    setConfirmMove(false);
                  }}
                />
                <SelectField
                  id="lesson-time"
                  label="Время начала, МСК"
                  error={errors['lesson-time']}
                  value={calendarHours.includes(time) ? time : null}
                  data={calendarHours}
                  onChange={(v) => {
                    setTime(v || '');
                    setConfirmMove(false);
                  }}
                />
              </>
            ) : (
              <DateTimeField
                timeId="lesson-time"
                error={errors['lesson-time']}
                date={date}
                time={time}
                onDateChange={(v) => {
                  setDate(v);
                  setConfirmMove(false);
                }}
                onTimeChange={(v) => {
                  setTime(v);
                  setConfirmMove(false);
                }}
              />
            )}
            {!lesson && (
              <>
                <SelectField
                  id="lesson-student"
                  error={errors['lesson-student']}
                  label="Ученик"
                  placeholder="Выберите или найдите по имени"
                  searchable
                  searchValue={search}
                  onSearchChange={(value) => {
                    setSearch(value);
                    setOffset(0);
                  }}
                  onCompositionStart={() => setComposing(true)}
                  onCompositionEnd={() => setComposing(false)}
                  filter={({ options }) => options}
                  value={student || null}
                  data={[
                    ...(students.data?.items || []).map((s) => ({
                      value: String(s.user_id),
                      label: `${s.first_name} ${s.last_name} · ${normLabel(s)} · ${s.username}`,
                    })),
                    ...(selectedStudent &&
                    !students.data?.items.some(
                      (s) => String(s.user_id) === selectedStudent.value,
                    )
                      ? [selectedStudent]
                      : []),
                  ]}
                  renderOption={({ option }) => {
                    const item = students.data?.items.find(
                      (s) => String(s.user_id) === option.value,
                    );
                    return item ? (
                      <span className={styles.studentOption}>
                        <strong>
                          {item.first_name} {item.last_name}
                        </strong>
                        <span>
                          {normLabel(item)} · {item.username}
                        </span>
                      </span>
                    ) : (
                      option.label
                    );
                  }}
                  onChange={(v) => {
                    const found = students.data?.items.find(
                      (s) => String(s.user_id) === v,
                    );
                    if (found)
                      setSelectedStudent({
                        value: String(found.user_id),
                        label: `${found.first_name} ${found.last_name} · ${normLabel(found)} · ${found.username}`,
                      });
                    setStudent(v || '');
                    setCourse('');
                  }}
                />
                <ReadState query={students}>
                  {(data) => (
                    <>
                      {data.total > limit && (
                        <Pagination
                          total={data.total}
                          offset={offset}
                          limit={limit}
                          onChange={(offset, limit) => {
                            setOffset(offset);
                            setLimit(limit);
                          }}
                        />
                      )}
                      {!data.total && (
                        <p>Ученики не найдены. Попробуйте другое имя.</p>
                      )}
                    </>
                  )}
                </ReadState>
                {student && (
                  <ReadState query={courses}>
                    {() =>
                      available.length ? (
                        <SelectField
                          id="lesson-course"
                          error={errors['lesson-course']}
                          label="Курс ученика"
                          value={selectedCourse || null}
                          data={available.map((c) => ({
                            value: String(c.id),
                            label: c.name,
                          }))}
                          onChange={(v) => setCourse(v || '')}
                        />
                      ) : (
                        <p>
                          Нет курса с одним активным участником. Откройте
                          ученика и проверьте обучение.
                        </p>
                      )
                    }
                  </ReadState>
                )}
              </>
            )}
            {(!calendarMode || !lesson) && (
              <>
                <FormField
                  id="lesson-title"
                  error={errors['lesson-title']}
                  label="Название занятия"
                  value={title}
                  onChange={(e) => setTitle(e.currentTarget.value)}
                />
                <details
                  open={
                    !!(
                      errors['lesson-duration'] || errors['lesson-override']
                    ) || undefined
                  }
                >
                  <summary>Дополнительно</summary>
                  <Stack mt="sm">
                    <FormField
                      label="Тема (необязательно)"
                      value={topic}
                      onChange={(e) => setTopic(e.currentTarget.value)}
                    />
                    <FormField
                      id="lesson-duration"
                      error={errors['lesson-duration']}
                      label="Длительность, минут"
                      inputMode="numeric"
                      value={duration}
                      onChange={(e) => setDuration(e.currentTarget.value)}
                    />
                    <FormField
                      id="lesson-override"
                      error={errors['lesson-override']}
                      label="Ссылка встречи (замена ссылки курса)"
                      description="Пустое поле возвращает текущую ссылку курса"
                      value={override}
                      onChange={(e) => setOverride(e.currentTarget.value)}
                    />
                  </Stack>
                </details>
              </>
            )}
            {!lesson && (
              <>
                <Checkbox
                  label="Закрепить время еженедельно"
                  checked={regular}
                  onChange={(e) => setRegular(e.currentTarget.checked)}
                />
                {regular && (
                  <FormField
                    id="lesson-weeks"
                    error={errors['lesson-weeks']}
                    label="Количество недель, 1–12"
                    inputMode="numeric"
                    value={weeks}
                    onChange={(e) => setWeeks(e.currentTarget.value)}
                  />
                )}
              </>
            )}
            {confirmMove && lesson && (
              <p>
                Было: {dateLabel(lesson.scheduled_at)} → станет:{' '}
                {dateLabel(iso)}. Меняется только эта встреча.
              </p>
            )}
            {unknown && (
              <>
                <p role="alert">
                  Форма сохранена в этой вкладке. Сначала прочитайте результат;
                  повтор записи возможен только после проверки.
                </p>
                <Button
                  variant="default"
                  disabled={pending}
                  onClick={() => {
                    busy(true);
                    const read = lesson
                      ? request<Lesson>(`/lessons/${lesson.id}`).then(
                          (item) => [item],
                        )
                      : request<Page<Lesson>>('/lessons', {
                          params: {
                            course_id: selectedCourse,
                            student_user_id: student,
                            view: 'all',
                            from_date: iso,
                            to_date: iso,
                            limit: 1000,
                          },
                        }).then((page) => {
                          if (page.total > 1000)
                            throw new Error('Too many results');
                          return page.items;
                        });
                    void read
                      .then((items) => {
                        setRecovered(items);
                        if (lesson && items[0]) {
                          setExpected(items[0].updated_at);
                          setServerBefore(items[0]);
                        }
                        setError(
                          'Состояние прочитано. Сравните его со своей формой.',
                        );
                      })
                      .catch(() =>
                        setError(
                          'Не удалось прочитать результат. Повтор остаётся заблокирован.',
                        ),
                      )
                      .finally(() => busy(false));
                  }}
                >
                  Проверить результат сохранения
                </Button>
              </>
            )}
            {recovered && (
              <>
                <h3>Сейчас на сервере</h3>
                {!recovered.length && (
                  <p>В выбранное время занятий не найдено.</p>
                )}
                {recovered.map((item) => (
                  <p key={item.id}>
                    {item.title} · {dateLabel(item.scheduled_at)} ·{' '}
                    {item.duration_minutes} мин
                  </p>
                ))}
                <Button
                  variant="default"
                  disabled={pending}
                  onClick={() => {
                    setUnknown(false);
                    setRecovered(null);
                    setConfirmMove(false);
                    setError(
                      'Сравнение подтверждено. Повторите сохранение только если нужного результата ещё нет.',
                    );
                  }}
                >
                  Сравнение выполнено, разрешить осознанный повтор
                </Button>
              </>
            )}
          </Stack>
        )}
      </ConfirmDialog>
    </>
  );
}
