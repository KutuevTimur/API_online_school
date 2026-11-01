import { useContext, useEffect, useState, useRef } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import { Button, Stack } from '@mantine/core';
import { flushSync } from 'react-dom';
import { useQueryClient } from '@tanstack/react-query';
import { CourseHistory } from './CourseHistory';
import { usePageTitle } from '../../app/router';
import { DraftContext } from '../../app/DraftProvider';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import { FormField, TextAreaField } from '../../shared/ui/FormField';
import { OwnStudentSelect } from '../students/OwnStudentSelect';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { ErrorSummary, focusFirstError } from '../../shared/ui/ErrorSummary';
import { AvatarEditor } from '../../shared/ui/AvatarEditor';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { type Course, type Page, useRead } from './queries';
import { Pages, ReadOnly, ReadState, useListState, Views } from './ReadUI';
import { courseSlug, activeMembership, type Membership } from '../students/api';
import styles from './read.module.css';
export function TeacherCoursesPage({
  studentId,
  excludeId,
  archiveOnly = false,
}: {
  studentId?: string;
  excludeId?: number;
  archiveOnly?: boolean;
}) {
  const state = useListState();
  const query = useRead<Page<Course>>('/courses', {
    student_user_id: studentId,
    view: archiveOnly ? 'archive' : state.view,
    limit: state.limit,
    offset: state.offset,
  });
  usePageTitle(studentId ? 'Карточка ученика' : 'Архив обучения');
  return (
    <>
      {!studentId && (
        <>
          <Link to="/teacher/students">К ученикам</Link>
          <h1>Архив обучения</h1>
        </>
      )}
      {!archiveOnly && (
        <Views
          value={state.view}
          onChange={(view) => state.update({ view, offset: 0 })}
        />
      )}
      <ReadState query={query}>
        {(data) => (
          <>
            {!data.items.filter((c) => c.id !== excludeId).length && (
              <p>
                {archiveOnly || state.view === 'archive'
                  ? 'Архивных курсов пока нет.'
                  : 'В этом разделе пока нет других курсов.'}
              </p>
            )}
            <ul className={styles.list}>
              {data.items
                .filter((c) => c.id !== excludeId)
                .map((course) => (
                  <li className={styles.row} key={course.id}>
                    <Link to={`/teacher/courses/${course.id}`}>
                      {course.name}
                    </Link>
                    <p>{course.description}</p>
                    <ReadOnly
                      mode={course.access_mode}
                      reason={course.read_only_reason}
                    />
                  </li>
                ))}
            </ul>
            {data.total > state.limit && (
              <Pages total={data.total} state={state} />
            )}
          </>
        )}
      </ReadState>
    </>
  );
}
function CourseForm({
  course,
  personal = false,
}: {
  course?: Course;
  personal?: boolean;
}) {
  const operation = useRef<AbortController | null>(null);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      operation.current?.abort();
    };
  }, []);
  const [params] = useSearchParams();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const feedback = useFeedback();
  const drafts = useContext(DraftContext);
  const [values, setValues] = useState({
    name: course?.name || '',
    description: course?.description || '',
    call_url: course?.call_url || '',
    slug: course?.slug || '',
  });
  const [version, setVersion] = useState(course?.updated_at);
  const [conflict, setConflict] = useState<Course | null>(null);
  const [baseline, setBaseline] = useState(JSON.stringify(values));
  const [studentId, setStudentId] = useState(params.get('student') || '');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState('');
  const [pending, busy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [checked, setChecked] = useState(false);
  const [recovered, setRecovered] = useState<Course | null>(null);
  const [completed, setCompleted] = useState(false);
  const dirty =
    !completed &&
    (JSON.stringify(values) !== baseline || (!course && !!studentId));
  useEffect(() => {
    drafts.set('teacher-course', { dirty });
    return () => {
      drafts.delete('teacher-course');
    };
  }, [drafts, dirty]);
  async function save() {
    if (pending || conflict || (uncertain && !checked)) return;
    const invalid: Record<string, string> = {};
    if (!values.name.trim()) invalid.name = 'Введите название курса';
    if (!course && !studentId) invalid.student = 'Выберите своего ученика';
    if (values.call_url) {
      try {
        const url = new URL(values.call_url);
        if (
          !['http:', 'https:'].includes(url.protocol) ||
          url.username ||
          url.password
        )
          invalid.call_url = 'Укажите полную ссылку http или https';
      } catch {
        invalid.call_url = 'Укажите полную ссылку http или https';
      }
    }
    setErrors(invalid);
    focusFirstError(invalid);
    if (Object.keys(invalid).length) return;
    busy(true);
    operation.current = new AbortController();
    setMessage('');
    const slug = values.slug || courseSlug(values.name);
    setValues((v) => ({ ...v, slug }));
    try {
      const result = await request<Course>(
        course ? `/courses/${course.id}` : '/courses',
        {
          signal: operation.current.signal,
          method: course ? 'PATCH' : 'POST',
          body: {
            ...values,
            slug,
            call_url: values.call_url || null,
            ...(course ? { expected_updated_at: version } : {}),
          },
        },
      );
      if (!alive.current) return;
      setVersion(result.updated_at);
      setBaseline(JSON.stringify({ ...values, slug }));
      // Enrolment has its own commit; never repeat course creation after its failure.
      if (!course) {
        try {
          await request(`/courses/${result.id}/students`, {
            method: 'POST',
            signal: operation.current.signal,
            body: { student_user_id: Number(studentId) },
          });
        } catch {
          if (!alive.current) return;
          setBaseline(JSON.stringify({ ...values, slug }));
          flushSync(() => {
            setCompleted(true);
            busy(false);
          });
          drafts.delete('teacher-course');
          navigate(`/teacher/courses/${result.id}?attach=${studentId}`, {
            state: { created: true },
          });
          return;
        }
      }
      if (!course) setCompleted(true);
      drafts.delete('teacher-course');
      await queryClient.invalidateQueries({
        predicate: (query) =>
          query.queryKey[1] === '/courses' ||
          query.queryKey[1] === `/courses/${result.id}` ||
          (personal &&
            typeof query.queryKey[1] === 'string' &&
            query.queryKey[1].startsWith('/courses/personal/')),
      });
      flushSync(() => {
        busy(false);
        setBaseline(JSON.stringify({ ...values, slug }));
      });
      feedback(course ? 'Курс сохранён' : 'Курс создан');
      if (!personal)
        navigate(`/teacher/courses/${result.id}`, { state: { saved: true } });
    } catch (e) {
      if (!alive.current) return;
      if (e instanceof ApiError) {
        setErrors(e.fields);
        focusFirstError(e.fields);
        if (e.status === 409) {
          if (course) {
            setConflict(
              await request<Course>(`/courses/${course.id}`).catch(() => null),
            );
          }
          setMessage(
            course
              ? 'Курс изменился. Проверьте актуальную версию перед сохранением; введённый текст сохранён.'
              : 'Название или адрес курса уже используются. Измените название или адрес в дополнительных настройках.',
          );
          if (!course) setErrors({ slug: 'Укажите другой адрес курса' });
        } else if (!e.status || e.status >= 500 || e.status === 401) {
          setUncertain(true);
          setChecked(false);
          setMessage(
            'Не удалось подтвердить сохранение. Сначала проверьте уже сохранённые курсы.',
          );
        } else setMessage(e.message);
      }
    } finally {
      busy(false);
    }
  }
  return (
    <>
      <DirtyFormGuard dirty={dirty || pending} />
      <form
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <fieldset
          disabled={pending}
          style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}
        >
          <Stack>
            <ErrorSummary errors={errors} />
            {!personal && (
              <>
                <FormField
                  id="name"
                  name="name"
                  label="Название курса"
                  value={values.name}
                  maxLength={500}
                  error={errors.name}
                  onChange={(e) =>
                    setValues({ ...values, name: e.currentTarget.value })
                  }
                />
              </>
            )}
            {!course && (
              <OwnStudentSelect
                value={studentId}
                onChange={setStudentId}
                error={errors.student}
              />
            )}
            <TextAreaField
              label="Описание"
              value={values.description}
              onChange={(e) =>
                setValues({ ...values, description: e.currentTarget.value })
              }
            />
            <FormField
              id="call_url"
              name="call_url"
              label="Ссылка встречи"
              description="Если ссылка не задана для занятия, используется ссылка курса."
              value={values.call_url}
              error={errors.call_url}
              onChange={(e) =>
                setValues({ ...values, call_url: e.currentTarget.value })
              }
            />
            {!personal && (
              <>
                <details open={!!errors.slug}>
                  <summary>Дополнительные настройки</summary>
                  <FormField
                    id="slug"
                    name="slug"
                    label="Адрес курса"
                    description="Создаётся автоматически. Меняйте только при необходимости."
                    value={values.slug}
                    error={errors.slug}
                    onChange={(e) =>
                      setValues({ ...values, slug: e.currentTarget.value })
                    }
                  />
                </details>
              </>
            )}
            <p role="status">{message}</p>
            {conflict && (
              <section aria-label="Серверная версия курса">
                <h3>На сервере</h3>
                <p>{conflict.name}</p>
                <p>{conflict.description}</p>
                <p>{conflict.call_url}</p>
                <Button
                  variant="default"
                  onClick={() => {
                    setVersion(conflict.updated_at);
                    setConflict(null);
                    setMessage(
                      'Версия обновлена. Проверьте введённые поля перед сохранением.',
                    );
                  }}
                >
                  Использовать актуальную версию для сохранения
                </Button>
              </section>
            )}
            {recovered && (
              <Button
                variant="default"
                onClick={() => {
                  flushSync(() => {
                    if (course) {
                      const restored = {
                        name: recovered.name,
                        description: recovered.description || '',
                        call_url: recovered.call_url || '',
                        slug: recovered.slug,
                      };
                      setValues(restored);
                      setBaseline(JSON.stringify(restored));
                      setVersion(recovered.updated_at);
                      setUncertain(false);
                      setRecovered(null);
                      setCompleted(false);
                    } else {
                      setCompleted(true);
                      setBaseline(JSON.stringify(values));
                    }
                  });
                  navigate(
                    `/teacher/courses/${recovered.id}` +
                      (!course && studentId ? `?attach=${studentId}` : ''),
                  );
                }}
              >
                Открыть сохранённый курс
              </Button>
            )}
            {uncertain && (
              <>
                <Button
                  variant="default"
                  onClick={() => {
                    void request<Page<Course>>('/courses', {
                      params: { view: 'all', limit: 50 },
                    })
                      .then((data) => {
                        const match = data.items.find(
                          (c) => c.slug === values.slug,
                        );
                        if (match) {
                          setRecovered(match);
                          setMessage(
                            `Найден сохранённый курс «${match.name}». Откройте его перед повтором.`,
                          );
                        } else
                          setMessage(
                            'В первых 50 курсах совпадений нет. Проверьте полный список курсов перед осознанным повтором.',
                          );
                        setChecked(!match);
                      })
                      .catch(() => {
                        setChecked(false);
                        setMessage(
                          'Проверка не удалась. Повтор сохранения заблокирован.',
                        );
                      });
                  }}
                >
                  Проверить сохранённые курсы
                </Button>
                <Link to="/teacher/courses?view=all">
                  Открыть список курсов
                </Link>
              </>
            )}
            <Button
              type="submit"
              loading={pending}
              disabled={!!conflict || (uncertain && !checked)}
            >
              {course
                ? personal
                  ? 'Сохранить настройки'
                  : 'Сохранить курс'
                : uncertain
                  ? 'Создать ещё раз после проверки'
                  : 'Создать курс и прикрепить ученика'}
            </Button>
          </Stack>
        </fieldset>
      </form>
    </>
  );
}
export function NewCoursePage() {
  usePageTitle('Новый персональный курс');
  return (
    <section className={styles.row}>
      <Link to="/teacher/students">К ученикам</Link>
      <h1>Новый персональный курс</h1>
      <CourseForm />
    </section>
  );
}
export function CourseDetail({
  course,
  refresh,
  studentId,
  showHistory = true,
}: {
  course: Course;
  refresh: () => Promise<unknown>;
  studentId?: string;
  showHistory?: boolean;
}) {
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const memberState = useListState('members-');
  const members = useRead<Page<Membership>>(`/courses/${course.id}/students`, {
    limit: memberState.limit,
    offset: memberState.offset,
  });
  const [confirm, setConfirm] = useState<'archive' | number | null>(null);
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [needsRead, setNeedsRead] = useState(false);
  const readonly =
    !course.can_manage ||
    course.access_mode === 'read_only' ||
    course.is_deleted;
  async function mutate(path: string, method: string, body?: unknown) {
    if (pending || needsRead) return;
    busy(true);
    setError('');
    try {
      await request(path, { method, body });
      await refresh();
      await members.refetch();
      setConfirm(null);
      await queryClient.invalidateQueries({
        queryKey: ['student-read', '/courses'],
      });
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message +
              '. Состояние перечитано; проверьте результат перед повтором.'
          : 'Не удалось сохранить',
      );
      try {
        await refresh();
        const result = await members.refetch();
        if (result.error) throw result.error;
      } catch {
        setNeedsRead(true);
        setError('Результат неизвестен. Проверьте состояние перед повтором.');
      }
    } finally {
      busy(false);
    }
  }
  const [chosenStudent, setChosenStudent] = useState('');
  const attach = params.get('attach');
  return (
    <>
      <ReadOnly mode={course.access_mode} reason={course.read_only_reason} />
      {showHistory && (
        <CourseHistory courseId={course.id} studentId={studentId} />
      )}
      {!studentId && (
        <details
          className={`${styles.row} ${styles.secondaryDisclosure}`}
          open={attach && !readonly ? true : undefined}
        >
          <summary>Участие в курсе</summary>
          {attach && !readonly && (
            <section className={styles.row}>
              <h2>Проверьте прикрепление ученика</h2>
              <p>
                Курс создан. Подтверждение прикрепления не получено. Повторяется
                только прикрепление.
              </p>
              <Button
                loading={pending}
                disabled={needsRead || !members.data || members.isError}
                onClick={() => {
                  const existing = members.data?.items.find(
                    (m) =>
                      m.student_user_id === Number(attach) && !m.is_deleted,
                  );
                  if (existing) {
                    setParams({});
                    return;
                  }
                  void mutate(`/courses/${course.id}/students`, 'POST', {
                    student_user_id: Number(attach),
                  }).then(() => void members.refetch());
                }}
              >
                Повторить прикрепление
              </Button>
            </section>
          )}
          {!readonly &&
            members.data &&
            !members.isError &&
            members.data.total <= memberState.limit &&
            !members.data.items.some((m) => activeMembership(m)) && (
              <section className={styles.row}>
                <h2>Прикрепить своего ученика</h2>
                <OwnStudentSelect
                  value={chosenStudent}
                  onChange={setChosenStudent}
                />
                <Button
                  loading={pending}
                  disabled={needsRead || !chosenStudent}
                  onClick={() =>
                    void mutate(`/courses/${course.id}/students`, 'POST', {
                      student_user_id: Number(chosenStudent),
                    })
                  }
                >
                  Прикрепить ученика
                </Button>
              </section>
            )}
          <ReadState query={members}>
            {(data) => (
              <>
                {!data.items.length && <p>Ученик не прикреплён.</p>}
                <ul>
                  {data.items.map((m) => (
                    <li key={m.id}>
                      <Link to={`/teacher/students/${m.student_user_id}`}>
                        {m.student
                          ? `${m.student.first_name} ${m.student.last_name}`.trim() ||
                            `Ученик №${m.student_user_id}`
                          : `Ученик №${m.student_user_id}`}
                        {m.student?.school_grade
                          ? ` · ${m.student.school_grade}`
                          : ''}
                      </Link>
                      <p>
                        {readonly || !activeMembership(m)
                          ? 'История, только чтение'
                          : 'Активное участие'}
                      </p>
                      {!readonly && activeMembership(m) && (
                        <Button
                          variant="default"
                          disabled={needsRead}
                          onClick={() => setConfirm(m.student_user_id)}
                        >
                          Открепить от курса
                        </Button>
                      )}
                    </li>
                  ))}
                </ul>
                <Pages
                  label="Страницы участников"
                  state={memberState}
                  total={data.total}
                />
              </>
            )}
          </ReadState>
        </details>
      )}
      {readonly ? (
        <>
          <p>{course.description}</p>
          <p>
            Архив сохраняет историю и скачивание материалов. Восстановление
            выполняет администратор.
          </p>
        </>
      ) : (
        <>
          <details className={`${styles.row} ${styles.secondaryDisclosure}`}>
            <summary>Настройки обучения</summary>
            <CourseForm course={course} personal={!!studentId} />
            <AvatarEditor
              profile={{
                avatar_path: course.avatar_path,
                first_name: course.name,
                last_name: '',
              }}
              path={`/courses/${course.id}/avatar`}
              allowDelete={false}
              variant="cover"
              onRefresh={refresh}
            />
            <Button
              variant="default"
              disabled={needsRead}
              onClick={() => setConfirm('archive')}
            >
              Архивировать курс
            </Button>
          </details>
        </>
      )}
      {needsRead && (
        <Button
          variant="default"
          onClick={() => {
            void (async () => {
              try {
                await refresh();
                const result = await members.refetch();
                if (result.error) throw result.error;
                setNeedsRead(false);
                setError(
                  'Состояние обновлено. Проверьте результат перед повтором.',
                );
              } catch {
                setError('Проверка не удалась. Повтор изменений заблокирован.');
              }
            })();
          }}
        >
          Проверить состояние курса
        </Button>
      )}

      <p role="alert">{error}</p>
      <ConfirmDialog
        opened={confirm !== null}
        title={
          confirm === 'archive'
            ? `Архивировать «${course.name}»?`
            : 'Открепить ученика от курса?'
        }
        confirmLabel={confirm === 'archive' ? 'Архивировать курс' : 'Открепить'}
        pending={pending}
        error={error}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          void mutate(
            confirm === 'archive'
              ? `/courses/${course.id}`
              : `/courses/${course.id}/students/${confirm}`,
            'DELETE',
          );
        }}
      >
        История и файлы останутся доступны для чтения и скачивания. Новые
        занятия и изменения станут недоступны. Аккаунт и связь с другими
        преподавателями сохранятся.
      </ConfirmDialog>
    </>
  );
}
export function TeacherCoursePage() {
  const { courseId = '' } = useParams();
  const query = useRead<Course>(`/courses/${encodeURIComponent(courseId)}`);
  usePageTitle(query.data?.name || 'Курс');
  return (
    <>
      <Link to="/teacher/students">К ученикам</Link>
      <ReadState query={query}>
        {(course) => (
          <>
            <h1>{course.name}</h1>
            <CourseDetail
              course={course}
              refresh={async () => {
                const result = await query.refetch();
                if (result.error) throw result.error;
                return result.data;
              }}
            />
          </>
        )}
      </ReadState>
    </>
  );
}
