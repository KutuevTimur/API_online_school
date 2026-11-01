import { Link } from 'react-router';
import { Button } from '@mantine/core';
import { usePageTitle } from '../../../app/router';
import { type Page, useRead } from '../../courses/queries';
import { Pages, ReadState, useListState } from '../../courses/ReadUI';
import { SelectField } from '../../../shared/ui/SelectField';
import type { components } from '../../../shared/api/schema';
import { UserFilter } from '../courses/CoursesPage';
import { CleanupPanel } from '../courses/Actions';
const auditTime = new Intl.DateTimeFormat('ru-RU', {
  timeZone: 'Europe/Moscow',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
});
import styles from '../../courses/read.module.css';
import admin from '../users/users.module.css';
const actions: Record<string, string> = {
  restore: 'Восстановление из архива',
  purge: 'Безвозвратное удаление курса',
  revoke_history: 'Отзыв доступа к истории',
  restore_history: 'Возврат доступа к истории',
  account_create: 'Создание пользователя',
  profile_update: 'Изменение профиля',
  account_status: 'Блокировка / разблокировка',
  teacher_student_link: 'Подключение к преподавателю',
  teacher_student_end: 'Завершение связи',
  activation_issued: 'Выдача приглашения',
  activation_consumed: 'Активация аккаунта',
  reset_issued: 'Выдача ссылки восстановления',
  reset_consumed: 'Восстановление пароля',
  file_quota: 'Изменение квоты',
  avatar_update: 'Изменение фото',
  avatar_delete: 'Удаление фото',
  student_grade_update: 'Изменение класса',
};
const objects: Record<string, string> = {
  course: 'Курс',
  lesson: 'Занятие',
  enrollment: 'Участие в курсе',
  user: 'Пользователь',
  teacher_student: 'Связь с преподавателем',
};
export function AuditPage() {
  usePageTitle('Журнал действий');
  const state = useListState();
  const action = state.params.get('action') || '';
  const query = useRead<Page<components['schemas']['AuditEventResponseDTO']>>(
    '/audit-events',
    {
      actor_user_id: state.params.get('actor') || undefined,
      action: action || undefined,
      limit: state.limit,
      offset: state.offset,
    },
  );
  return (
    <div className={admin.page}>
      <h1>Журнал действий</h1>
      <p>Время указано по Москве. Записи доступны только для просмотра.</p>
      <details>
        <summary>
          Фильтры журнала
          {action || state.params.get('actor') ? ' · применены' : ''}
        </summary>
        <div className={admin.filters}>
          <UserFilter
            value={state.params.get('actor') || ''}
            onChange={(actor) => state.update({ actor, offset: 0 })}
          />
          <SelectField
            label="Действие"
            placeholder="Все действия"
            clearable
            value={action || null}
            data={[
              ...Object.entries(actions).map(([value, label]) => ({
                value,
                label,
              })),
              ...(action && !actions[action]
                ? [{ value: action, label: action }]
                : []),
            ]}
            onChange={(v) => state.update({ action: v || '', offset: 0 })}
          />
        </div>
        <Button
          variant="default"
          onClick={() => state.update({ actor: '', action: '', offset: 0 })}
        >
          Сбросить фильтры
        </Button>
      </details>
      <ReadState query={query}>
        {(data) => (
          <>
            <p>Всего записей: {data.total}</p>
            {!data.items.length && <p>Записи не найдены. Измените фильтры.</p>}
            <ul className={styles.list}>
              {data.items.map((e) => (
                <li className={styles.row} key={`${e.source}:${e.id}`}>
                  <p>
                    <strong>{actions[e.action] || e.action}</strong> ·{' '}
                    {e.result === 'success'
                      ? 'Успешно'
                      : e.result === 'denied'
                        ? 'Отказано'
                        : e.result === 'failed'
                          ? 'Ошибка'
                          : e.result}
                  </p>
                  <p>
                    <time dateTime={e.created_at}>
                      {auditTime.format(new Date(e.created_at))}
                    </time>{' '}
                    ·{' '}
                    <Link to={`/admin/users/${e.actor_user_id}`}>
                      Кто выполнил: № {e.actor_user_id}
                    </Link>
                  </p>
                  <p>
                    {objects[e.object_type] || e.object_type} № {e.object_id}
                  </p>
                </li>
              ))}
            </ul>
            <Pages state={state} total={data.total} />
            {state.offset >= data.total && state.offset > 0 && (
              <Button onClick={() => state.update({ offset: 0 })}>
                На первую страницу
              </Button>
            )}
          </>
        )}
      </ReadState>
      <details>
        <summary>Обслуживание удалённых файлов</summary>
        <CleanupPanel />
      </details>
    </div>
  );
}
