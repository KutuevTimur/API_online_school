import { useState } from 'react';
import { Button, Stack } from '@mantine/core';
import { useRead, type Page } from '../../courses/queries';
import { Pages, ReadState, useListState } from '../../courses/ReadUI';
import { SelectField } from '../../../shared/ui/SelectField';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { request } from '../../../shared/api/client';
import { useFeedback } from '../../../shared/ui/FeedbackProvider';
import { ApiError } from '../../../shared/api/error';
import { type AdminUser, type AdminLink, userLabel } from './api';
import { PrivateSearch, usePrivateSearch } from './Search';
function UserSelector({
  role,
  selected,
  onSelect,
}: {
  role: 'teacher' | 'student';
  selected: AdminUser | null;
  onSelect: (user: AdminUser | null) => void;
}) {
  const search = usePrivateSearch();
  const query = useRead<Page<AdminUser>>('/admin/users', {
    role,
    is_active: 'true',
    q: search.q || undefined,
    limit: 20,
    offset: 0,
  });
  const label = role === 'teacher' ? 'Преподаватель' : 'Ученик';
  return (
    <Stack>
      <PrivateSearch label={`Поиск: ${label.toLowerCase()}`} search={search} />
      <ReadState query={query}>
        {(data) => (
          <>
            <SelectField
              label={label}
              value={selected ? String(selected.user_id) : null}
              clearable
              data={[
                ...(selected &&
                !data.items.some((u) => u.user_id === selected.user_id)
                  ? [selected]
                  : []),
                ...data.items,
              ].map((u) => ({ value: String(u.user_id), label: userLabel(u) }))}
              onChange={(v) =>
                onSelect(
                  data.items.find((u) => String(u.user_id) === v) ||
                    (v === String(selected?.user_id) ? selected : null),
                )
              }
            />
            <p>
              Найдено: {data.total}.{' '}
              {data.total > 20
                ? 'Уточните поиск для остальных пользователей.'
                : ''}
            </p>
          </>
        )}
      </ReadState>
    </Stack>
  );
}
export function Links({ user }: { user: AdminUser }) {
  const state = useListState('links_');
  const query = useRead<Page<AdminLink>>('/teacher_students', {
    ...(user.role === 'teacher'
      ? { teacher_user_id: user.user_id }
      : { student_user_id: user.user_id }),
    limit: state.limit,
    offset: state.offset,
  });
  const [teacher, setTeacher] = useState<AdminUser | null>(
    user.role === 'teacher' ? user : null,
  );
  const [student, setStudent] = useState<AdminUser | null>(
    user.role === 'student' ? user : null,
  );
  const [confirm, setConfirm] = useState<'link' | AdminLink | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const feedback = useFeedback();
  return (
    <section>
      <h2>
        {user.role === 'teacher'
          ? 'Связи с учениками'
          : 'Связи с преподавателями'}
      </h2>
      <ReadState query={query}>
        {(data) => (
          <>
            {!data.items.length && <p>Связей пока нет.</p>}
            {data.items.map((link) => (
              <div key={`${link.teacher_user_id}:${link.student_user_id}`}>
                <p>
                  {userLabel(link.teacher)} → {userLabel(link.student)} ·{' '}
                  {link.active ? 'Обучение активно' : 'Связь завершена'}
                </p>
                {link.active && (
                  <Button
                    variant="default"
                    onClick={() => {
                      setError('');
                      setConfirm(link);
                    }}
                  >
                    Завершить связь с {link.teacher.username}
                  </Button>
                )}
              </div>
            ))}
            <Pages total={data.total} state={state} label="Страницы связей" />
          </>
        )}
      </ReadState>
      <details>
        <summary>Подключить существующего ученика</summary>
        <Stack>
          <UserSelector
            role="teacher"
            selected={teacher}
            onSelect={setTeacher}
          />
          <UserSelector
            role="student"
            selected={student}
            onSelect={setStudent}
          />
          {teacher && student && (
            <p>
              Пара: {userLabel(teacher)} → {userLabel(student)}
            </p>
          )}
          <Button
            disabled={!teacher || !student}
            onClick={() => {
              setError('');
              setConfirm('link');
            }}
          >
            Проверить и подключить
          </Button>
        </Stack>
      </details>
      <ConfirmDialog
        opened={confirm !== null}
        title={
          confirm === 'link'
            ? 'Подключить ученика?'
            : 'Завершить только эту связь?'
        }
        confirmLabel={
          confirm === 'link' ? 'Подключить ученика' : 'Завершить связь'
        }
        destructive={confirm !== 'link'}
        pending={pending}
        error={error}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          if (pending || !confirm) return;
          const pair =
            confirm === 'link'
              ? teacher && student
                ? {
                    teacher_user_id: teacher.user_id,
                    student_user_id: student.user_id,
                  }
                : null
              : confirm;
          if (!pair) return;
          setPending(true);
          setError('');
          void request(
            confirm === 'link'
              ? '/teacher_students'
              : `/teacher_students/${pair.teacher_user_id}/${pair.student_user_id}`,
            {
              method: confirm === 'link' ? 'POST' : 'DELETE',
              ...(confirm === 'link'
                ? {
                    body: {
                      teacher_user_id: pair.teacher_user_id,
                      student_user_id: pair.student_user_id,
                    },
                  }
                : {}),
            },
          )
            .then(() => {
              feedback(
                confirm === 'link' ? 'Ученик подключён' : 'Связь завершена',
              );
              setConfirm(null);
              void query.refetch();
            })
            .catch((e) => {
              setError(
                e instanceof ApiError
                  ? `${e.message} Перечитайте список связей перед повтором.`
                  : 'Не удалось подтвердить действие. Перечитайте связи.',
              );
              void query.refetch();
            })
            .finally(() => setPending(false));
        }}
      >
        {confirm === 'link' ? (
          <>
            <p>
              {teacher && userLabel(teacher)} → {student && userLabel(student)}
            </p>
            <p>
              Существующая активная связь сохранится без дублирования.
              Завершённая связь возобновится; период перерыва останется закрыт.
            </p>
          </>
        ) : (
          confirm && (
            <>
              <p>
                {userLabel(confirm.teacher)} → {userLabel(confirm.student)}
              </p>
              <p>
                История и материалы сохранятся для чтения. Новые записи и
                отправка работ в этой связи будут недоступны. Аккаунт ученика и
                обучение у другого преподавателя продолжат работать.
              </p>
            </>
          )
        )}
      </ConfirmDialog>
    </section>
  );
}
