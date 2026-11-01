import { Settings } from 'lucide-react';
import { Link } from 'react-router';
import type { components } from '../../shared/api/schema';
import { NormEditor } from '../schedule/NormEditor';
import { TeacherReminders } from '../schedule/TeacherReminders';
import { useRef, useState, type ReactNode } from 'react';
import { Button } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { useRead, readKey, type Course } from '../courses/queries';
import { ReadOnly, ReadState } from '../courses/ReadUI';
import { StudentHistory } from '../courses/StudentHistory';
import {
  CourseDetail,
  TeacherCoursesPage,
} from '../courses/TeacherCoursesPage';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { SelectField } from '../../shared/ui/SelectField';
import { FormField } from '../../shared/ui/FormField';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { gradeOptions, type Student } from './api';
import { formatKopecks, kopecksToInput, parseRublesToKopecks } from './pricing';
import styles from '../courses/read.module.css';
function GradeEditor({
  student,
  refresh,
}: {
  student: Student;
  refresh: () => Promise<unknown>;
}) {
  const client = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [grade, setGrade] = useState('');
  const [expected, setExpected] = useState<number | null>(null);
  const [pending, busy] = useState(false);
  const [message, setMessage] = useState('');
  const [conflict, setConflict] = useState(false);
  const [needsRead, setNeedsRead] = useState(false);
  async function save() {
    if (pending || conflict || needsRead) return;
    busy(true);
    setMessage('');
    try {
      await request(`/users/${student.user_id}/school-grade`, {
        method: 'PATCH',
        body: {
          school_grade: grade ? Number(grade) : null,
          expected_school_grade: expected,
        },
      });
      await refresh();
      await client.invalidateQueries({
        predicate: (q) =>
          typeof q.queryKey[1] === 'string' &&
          q.queryKey[1].startsWith('/users'),
      });
      setEditing(false);
      setMessage('Класс сохранён');
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setConflict(true);
        setNeedsRead(true);
        setMessage(
          'Класс уже изменили. Ваш выбор сохранён. Сначала загрузите актуальный класс.',
        );
      } else {
        setNeedsRead(true);
        setMessage(
          'Не удалось подтвердить сохранение. Проверьте актуальный класс перед повтором.',
        );
      }
    } finally {
      busy(false);
    }
  }
  return (
    <>
      <Button
        variant="default"
        onClick={() => {
          setGrade(student.school_grade ? String(student.school_grade) : '');
          setExpected(student.school_grade ?? null);
          setConflict(false);
          setNeedsRead(false);
          setMessage('');
          setEditing(true);
        }}
      >
        Изменить класс
      </Button>
      {!student.school_grade && (
        <p className={styles.muted}>Класс пока не указан</p>
      )}
      {!editing && message && <p role="status">{message}</p>}
      <ConfirmDialog
        opened={editing}
        title="Школьный класс ученика"
        confirmLabel="Сохранить класс"
        pending={pending}
        confirmDisabled={conflict || needsRead}
        error={message}
        onConfirm={() => void save()}
        onCancel={() => setEditing(false)}
      >
        <SelectField
          disabled={pending}
          label="Класс"
          placeholder="Не указан"
          clearable
          data={gradeOptions}
          value={grade || null}
          onChange={(v) => setGrade(v || '')}
        />
        <p>Общий класс ученика. Изменение увидят другие его преподаватели.</p>
        {(conflict || needsRead) && (
          <Button
            variant="default"
            onClick={() => {
              busy(true);
              void refresh()
                .then(() => {
                  setNeedsRead(false);
                  setMessage(
                    'Актуальный класс загружен. Сравните его со своим выбором.',
                  );
                  setConflict(true);
                })
                .catch(() =>
                  setMessage(
                    'Не удалось загрузить класс. Повтор сохранения заблокирован.',
                  ),
                )
                .finally(() => busy(false));
            }}
          >
            Загрузить актуальный класс
          </Button>
        )}
        {conflict && !needsRead && (
          <>
            <p>
              Сейчас в профиле: {student.school_grade ?? 'не указан'}. Ваш
              выбор: {grade || 'не указан'}.
            </p>
            <Button
              variant="default"
              onClick={() => {
                setExpected(student.school_grade ?? null);
                setConflict(false);
                setMessage('Проверьте выбранное значение и сохраните класс.');
              }}
            >
              Использовать актуальную версию
            </Button>
          </>
        )}
      </ConfirmDialog>
    </>
  );
}

type StudentPrice = components['schemas']['LessonPriceDTO'];

function PriceEditor({ studentId }: { studentId: number }) {
  const path = `/teacher-planning/students/${studentId}/price`;
  const client = useQueryClient();
  const query = useRead<StudentPrice>(path);
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState('');
  const [expected, setExpected] = useState<number | null>(null);
  const priceInput = useRef<HTMLInputElement>(null);
  const [fieldError, setFieldError] = useState('');
  const [pending, busy] = useState(false);
  const [message, setMessage] = useState('');
  const [needsRead, setNeedsRead] = useState(false);
  const [conflict, setConflict] = useState(false);
  const dirty =
    editing &&
    value !== kopecksToInput(query.data?.lesson_price_kopecks ?? null);

  async function save() {
    if (pending || needsRead || conflict) return;
    let price: number | null;
    try {
      price = parseRublesToKopecks(value);
    } catch (e) {
      setFieldError(e instanceof Error ? e.message : 'Проверьте цену занятия');
      priceInput.current?.focus();
      return;
    }
    busy(true);
    setMessage('');
    try {
      const result = await request<StudentPrice>(path, {
        method: 'PUT',
        body: {
          lesson_price_kopecks: price,
          expected_price_kopecks: expected,
        },
      });
      client.setQueryData(readKey(path), result);
      await client.invalidateQueries({
        predicate: (q) =>
          q.queryKey[0] === 'student-read' &&
          (q.queryKey[1] === '/users/students' ||
            (typeof q.queryKey[1] === 'string' &&
              q.queryKey[1].startsWith('/users/'))),
      });
      setEditing(false);
      setNeedsRead(false);
      setConflict(false);
      setMessage('Цена занятия сохранена');
    } catch (e) {
      if (
        e instanceof ApiError &&
        e.status !== 409 &&
        e.status > 0 &&
        e.status < 500 &&
        e.status !== 401
      ) {
        setMessage(e.message);
      } else {
        setNeedsRead(true);
        setConflict(e instanceof ApiError && e.status === 409);
        setMessage(
          e instanceof ApiError && e.status === 409
            ? 'Цену уже изменили. Загрузите актуальную цену, чтобы выбрать версию для сохранения.'
            : 'Не удалось подтвердить сохранение. Загрузите актуальную цену перед повтором.',
        );
      }
    } finally {
      busy(false);
    }
  }

  return (
    <section className={styles.studentSetting}>
      <h3>Цена занятия</h3>
      <ReadState query={query}>
        {(price) => (
          <div>
            {!editing ? (
              <>
                <p>
                  {price.lesson_price_kopecks === null
                    ? 'Цена пока не указана'
                    : formatKopecks(price.lesson_price_kopecks)}
                </p>
                <Button
                  variant="default"
                  onClick={() => {
                    setValue(kopecksToInput(price.lesson_price_kopecks));
                    setExpected(price.lesson_price_kopecks);
                    setNeedsRead(false);
                    setConflict(false);
                    setMessage('');
                    setFieldError('');
                    setEditing(true);
                  }}
                >
                  Изменить цену занятия
                </Button>
              </>
            ) : (
              <>
                <DirtyFormGuard dirty={dirty || pending} />
                <FormField
                  ref={priceInput}
                  label="Цена занятия, ₽"
                  error={fieldError}
                  value={value}
                  inputMode="decimal"
                  placeholder="Например, 800 или 800,50"
                  disabled={pending}
                  onChange={(e) => {
                    setValue(e.currentTarget.value);
                    setFieldError('');
                  }}
                />
                <p className={styles.muted}>
                  Пустое поле означает, что цена неизвестна. Новая цена
                  применяется только к занятиям, созданным после сохранения.
                </p>
                {message && <p role="status">{message}</p>}
                {needsRead && (
                  <Button
                    variant="default"
                    loading={pending}
                    onClick={() =>
                      void query.refetch().then((r) => {
                        if (r.error || !r.data) {
                          setMessage(
                            'Не удалось загрузить актуальную цену. Повтор сохранения пока недоступен.',
                          );
                          return;
                        }
                        setNeedsRead(false);
                        setConflict(true);
                        setMessage(
                          'Проверьте актуальную цену и выберите, какую версию сохранить.',
                        );
                      })
                    }
                  >
                    Загрузить актуальную цену
                  </Button>
                )}
                {conflict && !needsRead && price && (
                  <>
                    <p>
                      Сейчас:{' '}
                      {price.lesson_price_kopecks === null
                        ? 'не указана'
                        : formatKopecks(price.lesson_price_kopecks)}
                      {' · '}Ваш выбор: {value.trim() || 'не указана'}
                    </p>
                    <Button
                      variant="default"
                      onClick={() => {
                        setExpected(price.lesson_price_kopecks);
                        setConflict(false);
                        setMessage('Сохраните выбранную цену ещё раз.');
                      }}
                    >
                      Оставить мой выбор
                    </Button>
                    <Button
                      variant="default"
                      onClick={() => {
                        setValue(kopecksToInput(price.lesson_price_kopecks));
                        setExpected(price.lesson_price_kopecks);
                        setConflict(false);
                        setMessage('Актуальная цена выбрана.');
                      }}
                    >
                      Использовать актуальную цену
                    </Button>
                  </>
                )}
                <Button
                  loading={pending}
                  disabled={needsRead || conflict}
                  onClick={() => void save()}
                >
                  Сохранить цену
                </Button>
                <Button
                  variant="default"
                  disabled={pending}
                  onClick={() => {
                    setEditing(false);
                    setValue(kopecksToInput(price.lesson_price_kopecks));
                    setNeedsRead(false);
                    setConflict(false);
                    setMessage('');
                    setFieldError('');
                  }}
                >
                  Отменить изменение цены
                </Button>
              </>
            )}
          </div>
        )}
      </ReadState>
      {!editing && message && <p role="status">{message}</p>}
    </section>
  );
}

export function StudentWorkspace({
  heading,
  student,
  onStudentRefresh,
  children,
}: {
  heading?: ReactNode;
  student: Student;
  onStudentRefresh: () => Promise<unknown>;
  children?: ReactNode;
}) {
  const path = `/courses/personal/${student.user_id}`;
  const workspace = useRead<Course | null>(path);
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [needsRead, setNeedsRead] = useState(false);
  const settings = useRef<HTMLDetailsElement>(null);
  async function refresh() {
    const result = await workspace.refetch();
    if (result.error) throw result.error;
    return result.data;
  }
  return (
    <>
      <div className={styles.workspaceToolbar}>
        {heading}
        <Button
          variant="light"
          leftSection={<Settings size={18} aria-hidden="true" />}
          onClick={() => {
            if (settings.current) {
              settings.current.open = true;
              settings.current.scrollIntoView({ block: 'start' });
              settings.current.querySelector('summary')?.focus();
            }
          }}
        >
          Настройки ученика
        </Button>
      </div>
      <ReadState query={workspace}>
        {(course) =>
          course ? (
            <>
              <ReadOnly
                mode={course.access_mode}
                reason={course.read_only_reason}
              />
              <StudentHistory
                key={course.id}
                courseId={course.id}
                studentId={String(student.user_id)}
              />
            </>
          ) : (
            <section className={styles.row}>
              <h2>Занятия с учеником</h2>
              <p>
                <Link to="/teacher/schedule">Открыть расписание</Link>
              </p>
              <p>
                Начните обучение — личное пространство появится автоматически.
                Здесь будут занятия, материалы и задания.
              </p>
              <Button
                loading={pending}
                disabled={needsRead}
                onClick={() => {
                  if (pending || needsRead) return;
                  busy(true);
                  setError('');
                  void request<Course>(path, { method: 'POST' })
                    .then(refresh)
                    .catch(async () => {
                      setNeedsRead(true);
                      setError(
                        'Результат пока неизвестен. Проверьте пространство перед повтором.',
                      );
                      try {
                        await refresh();
                        setNeedsRead(false);
                      } catch {
                        /* Keep writes blocked until a successful read. */
                      }
                    })
                    .finally(() => busy(false));
                }}
              >
                Начать занятия
              </Button>
              {needsRead && (
                <Button
                  variant="default"
                  onClick={() => {
                    void refresh()
                      .then(() => setNeedsRead(false))
                      .catch(() =>
                        setError(
                          'Проверка не удалась. Восстановите связь и повторите.',
                        ),
                      );
                  }}
                >
                  Проверить пространство
                </Button>
              )}
              <p role="alert">{error}</p>
            </section>
          )
        }
      </ReadState>
      <TeacherReminders studentId={student.user_id} />
      <details
        ref={settings}
        className={`${styles.panel} ${styles.studentSettings} ${styles.secondaryDisclosure}`}
      >
        <summary>Настройки ученика и обучения</summary>
        <PriceEditor key={student.user_id} studentId={student.user_id} />
        <NormEditor studentId={student.user_id} embedded />
        <section className={styles.studentSetting}>
          <h3>Школьный класс</h3>
          <p>
            {student.school_grade
              ? `${student.school_grade} класс`
              : 'Класс не указан'}
          </p>
          <GradeEditor student={student} refresh={onStudentRefresh} />
        </section>
        {workspace.data && (
          <CourseDetail
            key={workspace.data.id}
            studentId={String(student.user_id)}
            course={workspace.data}
            refresh={refresh}
            showHistory={false}
          />
        )}
        <details className={`${styles.row} ${styles.secondaryDisclosure}`}>
          <summary>Архив и прежние курсы</summary>
          <TeacherCoursesPage
            studentId={String(student.user_id)}
            excludeId={workspace.data?.id}
          />
        </details>
        {children}
      </details>
    </>
  );
}
