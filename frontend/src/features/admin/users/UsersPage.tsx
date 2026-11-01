import { useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router';
import { Button, Group, Stack } from '@mantine/core';
import { usePageTitle } from '../../../app/router';
import { useRead, type Page } from '../../courses/queries';
import { Pages, ReadState, useListState } from '../../courses/ReadUI';
import { SelectField } from '../../../shared/ui/SelectField';
import { DataList } from '../../../shared/ui/DataList';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { InvitationDialog } from '../../../shared/ui/InvitationDialog';
import { DirtyFormGuard } from '../../../shared/ui/DirtyFormGuard';
import { request } from '../../../shared/api/client';
import { ApiError } from '../../../shared/api/error';
import { useFeedback } from '../../../shared/ui/FeedbackProvider';
import type { Invitation } from '../../students/api';
import { type AdminUser, roles, userLabel } from './api';
import { PrivateSearch, usePrivateSearch } from './Search';
import { UserForm } from './UserForm';
import { Links } from './Links';
import { Storage, TeacherStorage } from './Storage';
import styles from '../../courses/read.module.css';
import adminStyles from './users.module.css';
export function UsersPage() {
  usePageTitle('Пользователи');
  const state = useListState();
  const search = usePrivateSearch();
  const navigate = useNavigate();
  const role = roles.some((r) => r.value === state.params.get('role'))
    ? state.params.get('role')!
    : '';
  const booleanFilter = (key: string) =>
    ['true', 'false'].includes(state.params.get(key) || '')
      ? state.params.get(key)!
      : undefined;
  const query = useRead<Page<AdminUser>>('/admin/users', {
    role: role || undefined,
    is_active: booleanFilter('is_active'),
    is_activated: booleanFilter('is_activated'),
    q: search.q || undefined,
    limit: state.limit,
    offset: state.offset,
  });
  return (
    <div className={adminStyles.page}>
      <Group justify="space-between">
        <h1>Пользователи</h1>
        <Button onClick={() => navigate('/admin/users/new')}>
          Создать пользователя
        </Button>
      </Group>
      <Stack>
        <PrivateSearch
          label="Поиск по имени или логину"
          search={search}
          onChange={() => state.update({ offset: 0 })}
        />
        <div className={adminStyles.filters}>
          <SelectField
            label="Роль"
            clearable
            placeholder="Все роли"
            value={role || null}
            data={roles}
            onChange={(v) => state.update({ role: v || '', offset: 0 })}
          />
          <SelectField
            label="Аккаунт"
            clearable
            placeholder="Все аккаунты"
            value={booleanFilter('is_active') || null}
            data={[
              { value: 'true', label: 'Активен' },
              { value: 'false', label: 'Заблокирован' },
            ]}
            onChange={(v) => state.update({ is_active: v || '', offset: 0 })}
          />
          <SelectField
            label="Активация"
            clearable
            placeholder="Все состояния"
            value={booleanFilter('is_activated') || null}
            data={[
              { value: 'true', label: 'Активирован' },
              { value: 'false', label: 'Ожидает активации' },
            ]}
            onChange={(v) => state.update({ is_activated: v || '', offset: 0 })}
          />
        </div>
      </Stack>
      <ReadState query={query}>
        {(data) => (
          <>
            <p>Всего: {data.total}</p>
            {!data.items.length && (
              <p>Ничего не найдено. Очистите поиск или измените фильтры.</p>
            )}
            <DataList
              label="Пользователи"
              rows={data.items}
              rowKey={(u) => String(u.user_id)}
              rowLink={(u) => `/admin/users/${u.user_id}`}
              rowState={{ usersSearch: state.params.toString() }}
              renderRow={(u) => (
                <>
                  <span>{userLabel(u)}</span>
                  <span>
                    {roles.find((r) => r.value === u.role)?.label} ·{' '}
                    {u.is_active ? 'Активен' : 'Заблокирован'} ·{' '}
                    {u.is_activated ? 'Активирован' : 'Ожидает активации'}
                  </span>
                </>
              )}
            />
            <Pages total={data.total} state={state} />
          </>
        )}
      </ReadState>
    </div>
  );
}
export function CreateUserPage() {
  usePageTitle('Создать пользователя');
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [created, setCreated] = useState(false);
  const [dirty, setDirty] = useState(false);
  return (
    <div className={adminStyles.page}>
      <Link to="/admin/users">Пользователи</Link>
      <DirtyFormGuard dirty={dirty && !created} />
      <h1>Создать пользователя</h1>
      <p>Пароль пользователь задаст сам по одноразовой ссылке приглашения.</p>
      {!created ? (
        <UserForm
          onDirty={setDirty}
          onSaved={(result) => {
            if (result) {
              setCreated(true);
              setInvitation(result);
            }
          }}
        />
      ) : (
        <p role="status">
          Пользователь создан. Откройте его карточку из списка.
        </p>
      )}
      {invitation && (
        <InvitationDialog
          invitation={invitation}
          audience="user"
          onClose={() => setInvitation(null)}
        />
      )}
    </div>
  );
}
export function UserPage() {
  usePageTitle('Карточка пользователя');
  const { userId = '' } = useParams();
  const query = useRead<AdminUser>(
    `/admin/users/${encodeURIComponent(userId)}`,
  );
  const location = useLocation();
  const params = new URLSearchParams(location.state?.usersSearch || '');
  params.delete('q');
  return (
    <>
      <Link to={`/admin/users${params.size ? '?' + params : ''}`}>
        Пользователи
      </Link>
      <ReadState query={query}>
        {(user) => (
          <UserDetail
            user={user}
            refresh={async () => {
              const result = await query.refetch();
              if (result.error) throw result.error;
            }}
          />
        )}
      </ReadState>
    </>
  );
}
function UserDetail({
  user,
  refresh,
}: {
  user: AdminUser;
  refresh: () => Promise<void>;
}) {
  const [confirm, setConfirm] = useState<'status' | 'invite' | 'reset' | null>(
    null,
  );
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [purpose, setPurpose] = useState<'invite' | 'reset'>('invite');
  const [statusTarget, setStatusTarget] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [profileDirty, setProfileDirty] = useState(false);
  const [quotaDirty, setQuotaDirty] = useState(false);
  const feedback = useFeedback();
  const open = (action: 'status' | 'invite' | 'reset') => {
    setStatusTarget(!user.is_active);
    setInvitation(null);
    setError('');
    setConfirm(action);
  };
  return (
    <Stack className={adminStyles.page}>
      <DirtyFormGuard dirty={profileDirty || quotaDirty} />
      <header>
        <h1>
          {[user.first_name, user.last_name].filter(Boolean).join(' ') ||
            user.username}
        </h1>
        <p>Логин: {user.username}</p>
        <p>
          {roles.find((r) => r.value === user.role)?.label} ·{' '}
          {user.is_active ? 'Аккаунт активен' : 'Аккаунт заблокирован'} ·{' '}
          {user.is_activated ? 'Активирован' : 'Ожидает активации'}
        </p>
      </header>
      {user.role !== 'admin' && (
        <details className={styles.row}>
          <summary>Редактировать профиль</summary>
          <UserForm user={user} onDirty={setProfileDirty} onSaved={refresh} />
        </details>
      )}
      <section>
        <h2>Приглашение и доступ</h2>
        <Group>
          {user.role !== 'admin' && (
            <Button
              disabled={!user.is_active}
              onClick={() => open(user.is_activated ? 'reset' : 'invite')}
            >
              {user.is_activated
                ? 'Выдать ссылку сброса пароля'
                : 'Выдать новое приглашение'}
            </Button>
          )}
          <Button variant="default" onClick={() => open('status')}>
            {user.is_active
              ? 'Заблокировать общий аккаунт'
              : 'Включить общий аккаунт'}
          </Button>
        </Group>
        {!user.is_active && (
          <p>
            Сначала включите аккаунт: приглашение и сброс недоступны
            заблокированному пользователю.
          </p>
        )}
        <p>
          Блокировка отключает все сессии этого пользователя и доступ ко всем
          его преподавателям. Для окончания обучения у одного преподавателя
          завершите связь ниже.
        </p>
      </section>
      {user.role !== 'admin' && <Links user={user} />}
      {user.role === 'student' && (
        <Storage userId={user.user_id} onDirty={setQuotaDirty} />
      )}
      {user.role === 'teacher' && <TeacherStorage userId={user.user_id} />}
      {confirm && (
        <ConfirmDialog
          opened={confirm !== null}
          title={
            confirm === 'status'
              ? !statusTarget
                ? 'Заблокировать общий аккаунт?'
                : 'Включить общий аккаунт?'
              : confirm === 'reset'
                ? 'Выдать ссылку сброса пароля?'
                : 'Выдать новое приглашение?'
          }
          confirmLabel={
            confirm === 'status'
              ? !statusTarget
                ? 'Заблокировать аккаунт'
                : 'Включить аккаунт'
              : 'Выдать ссылку'
          }
          destructive={confirm === 'status' && !statusTarget}
          pending={pending}
          error={error}
          onCancel={() => setConfirm(null)}
          onConfirm={() => {
            if (pending || !confirm) return;
            setPending(true);
            setError('');
            setInvitation(null);
            const action = confirm;
            void (async () => {
              try {
                if (action === 'status') {
                  await request(`/users/${user.user_id}/account-status`, {
                    method: 'PATCH',
                    body: { is_active: statusTarget },
                  });
                  feedback(
                    !statusTarget ? 'Аккаунт заблокирован' : 'Аккаунт включён',
                  );
                } else {
                  setPurpose(action);
                  const result = await request<Invitation | null>(
                    '/account_invitations/issue',
                    {
                      method: 'POST',
                      body: { user_id: user.user_id, purpose: action },
                    },
                  );
                  setInvitation(result ?? {});
                }
                setConfirm(null);
                await refresh();
              } catch (e) {
                setError(
                  e instanceof ApiError
                    ? e.message + ' Перечитайте состояние перед повтором.'
                    : 'Не удалось подтвердить действие.',
                );
                await refresh().catch(() => {});
              } finally {
                setPending(false);
              }
            })();
          }}
        >
          <p>{userLabel(user)}</p>
          <p>
            {confirm === 'status'
              ? !statusTarget
                ? 'Все сессии пользователя будут отключены. Доступ ко всем преподавателям прекратится; история и файлы сохранятся.'
                : 'Пользователь снова сможет войти. Завершённые связи не возобновятся автоматически.'
              : 'Ссылка одноразовая. Новая выдача отменяет предыдущую ссылку этого назначения. Передайте её лично пользователю; пароль он задаст сам.'}
          </p>
        </ConfirmDialog>
      )}
      {invitation && (
        <InvitationDialog
          invitation={invitation}
          purpose={purpose}
          audience="user"
          onClose={() => setInvitation(null)}
        />
      )}
    </Stack>
  );
}
