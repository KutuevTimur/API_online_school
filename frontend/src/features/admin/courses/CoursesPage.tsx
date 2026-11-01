import { useState } from 'react';
import { Link, useLocation, useParams } from 'react-router';
import { Button, Stack } from '@mantine/core';
import { usePageTitle } from '../../../app/router';
import {
  type Course,
  type Lesson,
  type Page,
  useRead,
} from '../../courses/queries';
import { Pages, ReadState, useListState, Views } from '../../courses/ReadUI';
import { DataList } from '../../../shared/ui/DataList';
import { SelectField } from '../../../shared/ui/SelectField';
import type { components } from '../../../shared/api/schema';
import {
  ActionDialog,
  useActionRecovery,
  CleanupPanel,
  type Action,
  type Cleanup,
} from './Actions';
import { PrivateSearch, usePrivateSearch } from '../users/Search';
import { type AdminUser, userLabel } from '../users/api';
import { dateLabel } from '../../../shared/lib/datetime';
import styles from '../../courses/read.module.css';
import admin from '../users/users.module.css';
type Enrollment = components['schemas']['StudentCourseResponseDTO'];
export function UserFilter({
  role,
  value,
  onChange,
}: {
  role?: 'teacher' | 'student';
  value: string;
  onChange: (id: string) => void;
}) {
  const search = usePrivateSearch();
  const label =
    role === 'teacher'
      ? 'Преподаватель'
      : role === 'student'
        ? 'Ученик'
        : 'Кто выполнил';
  const users = useRead<Page<AdminUser>>('/admin/users', {
    role,
    q: search.q || undefined,
    limit: 20,
    offset: 0,
  });
  const selected = useRead<AdminUser>(
    `/admin/users/${encodeURIComponent(value || '0')}`,
    {},
    !!value,
  );
  return (
    <Stack gap="xs">
      <PrivateSearch label={`Поиск: ${label.toLowerCase()}`} search={search} />
      <ReadState query={users}>
        {(data) => (
          <>
            <SelectField
              label={label}
              placeholder="Все"
              clearable
              value={value || null}
              data={[
                ...(selected.data &&
                !data.items.some((u) => u.user_id === selected.data.user_id)
                  ? [selected.data]
                  : []),
                ...data.items,
              ].map((u) => ({ value: String(u.user_id), label: userLabel(u) }))}
              onChange={(v) => onChange(v || '')}
            />
            <p>
              Найдено: {data.total}
              {data.total > 20
                ? '. Уточните поиск, чтобы найти остальных.'
                : ''}
            </p>
          </>
        )}
      </ReadState>
      {selected.isError && (
        <p role="alert">
          Не удалось прочитать выбранного пользователя.{' '}
          <Button variant="subtle" onClick={() => void selected.refetch()}>
            Повторить
          </Button>
          <Button variant="subtle" onClick={() => onChange('')}>
            Сбросить выбор
          </Button>
        </p>
      )}
    </Stack>
  );
}
export function AdminCoursesPage() {
  usePageTitle('Все курсы');
  const state = useListState();
  const view = state.params.has('view') ? state.view : 'all';
  const query = useRead<Page<Course>>('/courses', {
    view,
    teacher_user_id: state.params.get('teacher') || undefined,
    student_user_id: state.params.get('student') || undefined,
    limit: state.limit,
    offset: state.offset,
  });
  return (
    <div className={admin.page}>
      <h1>Все курсы</h1>
      <Views
        value={view}
        onChange={(view) => state.update({ view, offset: 0 })}
      />
      <details>
        <summary>
          Поиск по преподавателю и ученику
          {state.params.get('teacher') || state.params.get('student')
            ? ' · применены фильтры'
            : ''}
        </summary>
        <div className={admin.filters}>
          <UserFilter
            role="teacher"
            value={state.params.get('teacher') || ''}
            onChange={(teacher) => state.update({ teacher, offset: 0 })}
          />
          <UserFilter
            role="student"
            value={state.params.get('student') || ''}
            onChange={(student) => state.update({ student, offset: 0 })}
          />
        </div>
        <Button
          variant="default"
          onClick={() =>
            state.update({ teacher: '', student: '', view: 'all', offset: 0 })
          }
        >
          Сбросить фильтры
        </Button>
      </details>
      <ReadState query={query}>
        {(data) => (
          <>
            <p>Всего курсов: {data.total}</p>
            {!data.items.length && <p>Курсы не найдены. Измените фильтры.</p>}
            <DataList
              label="Все курсы"
              rows={data.items}
              rowKey={(c) => String(c.id)}
              rowLink={(c) => `/admin/courses/${c.id}`}
              rowState={{ coursesSearch: state.params.toString() }}
              renderRow={(c) => (
                <>
                  <span>{c.name}</span>
                  <span>
                    {c.teacher_name || `Преподаватель № ${c.teacher_user_id}`} ·{' '}
                    {c.is_deleted ? 'В архиве' : 'Активен'}
                  </span>
                </>
              )}
            />
            <Pages state={state} total={data.total} />
            {state.offset >= data.total && state.offset > 0 && (
              <Button onClick={() => state.update({ offset: 0 })}>
                На первую страницу
              </Button>
            )}
          </>
        )}
      </ReadState>
    </div>
  );
}
export function AdminCoursePage() {
  const { courseId = '' } = useParams();
  const location = useLocation();
  const state = useListState('lessons_');
  const people = useListState('students_');
  const course = useRead<Course>(`/courses/${encodeURIComponent(courseId)}`);
  const lessons = useRead<Page<Lesson>>(
    '/lessons',
    {
      course_id: courseId,
      view: 'all',
      limit: state.limit,
      offset: state.offset,
    },
    !!course.data,
  );
  const students = useRead<Page<Enrollment>>(
    `/courses/${encodeURIComponent(courseId)}/students`,
    { limit: people.limit, offset: people.offset },
    !!course.data,
  );
  const [action, setAction] = useState<Action | null>(null);
  const recovery = useActionRecovery(action);
  const [actionOpen, setActionOpen] = useState(false);
  const openAction = (next: Action) => {
    setAction(next);
    setActionOpen(true);
  };
  const [deleted, setDeleted] = useState<{ cleanup?: Cleanup } | null>(null);
  usePageTitle(deleted ? 'Курс удалён' : course.data?.name || 'Курс');
  const back =
    typeof location.state?.coursesSearch === 'string'
      ? '?' + location.state.coursesSearch
      : '';
  async function refresh() {
    const results = await Promise.all([
      course.refetch(),
      lessons.refetch(),
      students.refetch(),
    ]);
    if (results.some((r) => r.isError)) throw new Error('read failed');
  }
  return (
    <div className={admin.page}>
      <Link to={'/admin/courses' + back}>К списку курсов</Link>
      {deleted ? (
        <>
          <h1>Курс удалён безвозвратно</h1>
          <p>
            Учебные данные удалены.{' '}
            {deleted.cleanup
              ? deleted.cleanup.failed
                ? 'Остались файлы, ожидающие очистки.'
                : 'Очистка файлов завершена.'
              : 'Состояние очистки файлов не подтверждено. Проверьте оставшиеся задания.'}
          </p>
          <CleanupPanel initial={deleted.cleanup} />
          <Link to="/admin/audit?action=purge">Открыть журнал удаления</Link>
        </>
      ) : (
        <ReadState query={course}>
          {(c) => (
            <>
              <h1>{c.name}</h1>
              <p>
                Преподаватель: {c.teacher_name || `№ ${c.teacher_user_id}`} ·
                Курс № {c.id} · {c.is_deleted ? 'В архиве' : 'Активен'}
              </p>
              <p className={styles.readonly}>
                Учебные данные доступны администратору только для просмотра и
                скачивания.
              </p>
              <p className={styles.copy}>{c.description}</p>
              {c.is_deleted && (
                <>
                  <p>
                    Восстановление курса сохранит отдельно архивированные
                    занятия и прежние границы доступа учеников.
                  </p>
                  <Button
                    onClick={() =>
                      openAction({
                        title: 'Восстановить курс?',
                        label: 'Восстановить курс',
                        description: `Курс «${c.name}» вернётся в активные. Отдельно архивированные занятия и участие учеников не восстановятся.`,
                        path: `/courses/${c.id}/restore`,
                      })
                    }
                  >
                    Восстановить курс
                  </Button>
                </>
              )}
              <h2>Занятия</h2>
              <ReadState query={lessons}>
                {(data) => (
                  <>
                    {!data.items.length && <p>Занятий пока нет.</p>}
                    <ul className={styles.list}>
                      {data.items.map((l) => (
                        <li key={l.id} className={styles.row}>
                          <Link to={`/admin/lessons/${l.id}`}>{l.title}</Link>
                          <p>
                            {dateLabel(l.scheduled_at)} ·{' '}
                            {l.is_deleted ? 'В архиве' : 'Не архивировано'}
                          </p>
                        </li>
                      ))}
                    </ul>
                    <Pages state={state} total={data.total} />
                  </>
                )}
              </ReadState>
              <details>
                <summary>Ученики и доступ к истории</summary>
                <ReadState query={students}>
                  {(data) => (
                    <>
                      {!data.items.length && <p>У курса нет учеников.</p>}
                      <ul className={styles.list}>
                        {data.items.map((s) => {
                          const name = s.student
                            ? `${s.student.first_name} ${s.student.last_name}`
                            : `Ученик № ${s.student_user_id}`;
                          return (
                            <li key={s.id} className={styles.row}>
                              <p>
                                {name} · № {s.student_user_id}
                              </p>
                              <p>
                                {s.history_revoked
                                  ? 'Доступ к истории отозван'
                                  : 'Доступ к истории разрешён'}
                              </p>
                              <p>
                                {s.is_deleted || s.access_ended_at
                                  ? 'Участие завершено'
                                  : 'Участие не завершено'}
                              </p>
                              <Button
                                variant="default"
                                onClick={() =>
                                  openAction({
                                    title: s.history_revoked
                                      ? 'Вернуть доступ к истории?'
                                      : 'Отозвать доступ к истории?',
                                    label: s.history_revoked
                                      ? 'Вернуть доступ'
                                      : 'Отозвать доступ',
                                    description: `${name} (№ ${s.student_user_id}), курс «${c.name}». ${s.history_revoked ? 'Вернётся чтение и скачивание истории в прежних границах. Участие и доступ к новым занятиям не изменятся.' : 'Ученик потеряет чтение и скачивание истории этого курса. Данные сохранятся, другие курсы не изменятся.'}`,
                                    path: `/courses/${c.id}/students/${s.student_user_id}/history-access`,
                                    method: 'PATCH',
                                    body: { revoked: !s.history_revoked },
                                  })
                                }
                              >
                                {s.history_revoked
                                  ? 'Вернуть доступ к истории'
                                  : 'Отозвать доступ к истории'}
                              </Button>
                            </li>
                          );
                        })}
                      </ul>
                      <Pages state={people} total={data.total} />
                    </>
                  )}
                </ReadState>
              </details>
              <section className={styles.panel}>
                <h2>Безвозвратное удаление</h2>
                <p>
                  Это отдельное опасное действие. Восстановить удалённый курс
                  будет невозможно.
                </p>
                <Button
                  variant="outline"
                  color="var(--lgg-danger)"
                  onClick={() =>
                    openAction({
                      title: 'Удалить курс безвозвратно?',
                      label: 'Удалить безвозвратно',
                      description:
                        'Перед удалением проверьте название и номер курса.',
                      path: `/courses/${c.id}/purge`,
                      purge: { id: c.id, name: c.name },
                    })
                  }
                >
                  Удалить курс безвозвратно
                </Button>
              </section>
            </>
          )}
        </ReadState>
      )}
      {
        <ActionDialog
          action={action}
          opened={actionOpen}
          recovery={recovery}
          onClose={() => setActionOpen(false)}
          refresh={refresh}
          onDeleted={(cleanup) => setDeleted({ cleanup })}
        />
      }
    </div>
  );
}
