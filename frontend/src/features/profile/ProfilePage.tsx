import { AccountLink } from '../booking/AccountLink';
import { useState, useEffect, useRef, useContext } from 'react';
import { Stack, Button } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { usePageTitle } from '../../app/router';
import { DraftContext } from '../../app/DraftProvider';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import { FormField } from '../../shared/ui/FormField';
import { ErrorSummary, focusFirstError } from '../../shared/ui/ErrorSummary';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { PasswordField } from '../auth/PasswordField';
import { session, useSession } from '../auth/session';
import { useRead } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import {
  type Account,
  type PublicProfile,
  type MinimalProfile,
  type Profile,
  normalizeProfile,
  validateProfile,
} from './api';
import styles from '../courses/read.module.css';
import { AvatarEditor } from '../../shared/ui/AvatarEditor';
import profileStyles from './profile.module.css';
function ProfileForm({
  profile,
  onRefresh,
  onDirty,
}: {
  profile: Profile;
  onRefresh: () => Promise<unknown>;
  onDirty: (dirty: boolean) => void;
}) {
  const client = useQueryClient();
  const feedback = useFeedback();
  const drafts = useContext(DraftContext);
  const [values, setValues] = useState({
    username: profile.username,
    email: profile.email || '',
    first_name: profile.first_name,
    last_name: profile.last_name,
    middle_name: profile.middle_name,
  });
  const [baseline, setBaseline] = useState(JSON.stringify(values));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const dirty = JSON.stringify(values) !== baseline;
  useEffect(() => onDirty(dirty), [dirty, onDirty]);
  useEffect(() => {
    const key = `profile:${profile.id}`;
    drafts.set(key, { dirty });
    return () => {
      drafts.delete(key);
    };
  }, [drafts, profile.id, dirty]);
  const operation = useRef<AbortController | undefined>(undefined);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      operation.current?.abort();
    };
  }, []);
  async function save() {
    if (pending || uncertain) return;
    const invalid = validateProfile(values);
    setErrors(invalid);
    focusFirstError(invalid);
    if (Object.keys(invalid).length) return;
    setPending(true);
    setMessage('');
    operation.current = new AbortController();
    try {
      await request(`/users/${profile.id}`, {
        method: 'PATCH',
        body: { ...values, email: values.email || null },
        signal: operation.current.signal,
      });
      if (!alive.current) return;
      setBaseline(JSON.stringify(values));
      setMessage('Профиль сохранён');
      feedback('Профиль сохранён');
      await onRefresh();
      await client.invalidateQueries({
        queryKey: ['student-read', '/users/me'],
      });
    } catch (error) {
      if (!alive.current) return;
      if (error instanceof ApiError) {
        if (error.status === 409) {
          const fields = {
            username: 'Логин или почта уже используются. Укажите другие.',
          };
          setErrors(fields);
          focusFirstError(fields);
        } else if (error.status === 422) {
          setErrors(error.fields);
          focusFirstError(error.fields);
        }
        setUncertain(
          error.status === 0 || error.status >= 500 || error.status === 401,
        );
        setMessage(
          error.status === 409
            ? 'Изменения не сохранены. Введённые данные оставлены в форме.'
            : error.message,
        );
      } else setMessage('Не удалось подтвердить сохранение');
    } finally {
      if (alive.current) setPending(false);
    }
  }
  return (
    <section className={styles.panel}>
      <h2>Личные данные</h2>
      <form
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <Stack>
          <ErrorSummary errors={errors} />
          {(
            [
              'first_name',
              'last_name',
              'middle_name',
              'username',
              'email',
            ] as const
          ).map((key) => (
            <FormField
              key={key}
              id={key}
              label={
                {
                  first_name: 'Имя',
                  last_name: 'Фамилия',
                  middle_name: 'Отчество',
                  username: 'Логин',
                  email: 'Почта (необязательно)',
                }[key]
              }
              value={values[key]}
              type={key === 'email' ? 'email' : 'text'}
              autoComplete={
                {
                  first_name: 'given-name',
                  last_name: 'family-name',
                  middle_name: 'additional-name',
                  username: 'username',
                  email: 'email',
                }[key]
              }
              error={errors[key]}
              disabled={pending}
              onChange={(e) => {
                setValues({ ...values, [key]: e.currentTarget.value });
                setErrors((previous) => {
                  const next = { ...previous };
                  delete next[key];
                  return next;
                });
                setMessage('');
              }}
            />
          ))}
          {message && <p role="status">{message}</p>}
          {uncertain && (
            <>
              <p>
                Результат сохранения неизвестен. Сначала проверьте серверную
                версию. Введённые данные останутся в форме.
              </p>
              <Button
                variant="default"
                loading={pending}
                onClick={() => {
                  setPending(true);
                  void onRefresh()
                    .then(() => {
                      setUncertain(false);
                      setMessage(
                        'Серверная версия обновлена. Сравните данные перед повторным сохранением.',
                      );
                    })
                    .catch(() =>
                      setMessage(
                        'Не удалось обновить профиль. Повторите проверку.',
                      ),
                    )
                    .finally(() => setPending(false));
                }}
              >
                Проверить сохранение
              </Button>
              <p>
                Сейчас на сервере: {profile.first_name} {profile.last_name};{' '}
                {profile.username}; {profile.email || 'без почты'}
              </p>
            </>
          )}
          <Button
            type="submit"
            loading={pending}
            disabled={!dirty || uncertain}
          >
            Сохранить профиль
          </Button>
        </Stack>
      </form>
    </section>
  );
}
function PasswordForm({
  id,
  onDirty,
}: {
  id: number;
  onDirty: (dirty: boolean) => void;
}) {
  const drafts = useContext(DraftContext);
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [repeat, setRepeat] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(false);
  const dirty = !!(current || password || repeat);
  useEffect(() => onDirty(dirty), [dirty, onDirty]);
  useEffect(() => {
    const key = `password:${id}`;
    drafts.set(key, { dirty });
    return () => {
      drafts.delete(key);
    };
  }, [drafts, id, dirty]);
  const feedback = useFeedback();
  const operation = useRef<AbortController | undefined>(undefined);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      operation.current?.abort();
    };
  }, []);
  async function save() {
    if (pending) return;
    const invalid: Record<string, string> = {};
    if (!current) invalid.current_password = 'Введите текущий пароль';
    if (password.length < 8 || new TextEncoder().encode(password).length > 72)
      invalid.new_password = 'От 8 символов до 72 байт';
    if (password !== repeat) invalid.repeat_password = 'Пароли не совпадают';
    setErrors(invalid);
    focusFirstError(invalid);
    if (Object.keys(invalid).length) return;
    setPending(true);
    setMessage('');
    operation.current = new AbortController();
    try {
      await request(`/auth/change_password/${id}`, {
        method: 'POST',
        body: { current_password: current, new_password: password },
        signal: operation.current.signal,
      });
      if (!alive.current) return;
      setCurrent('');
      setPassword('');
      setRepeat('');
      feedback('Пароль изменён. Войдите снова с новым паролем.');
      setMessage('Пароль изменён. Войдите снова с новым паролем.');
      session.expire();
    } catch (error) {
      if (!alive.current) return;
      if (error instanceof ApiError && error.status === 401) {
        try {
          await request<Account>('/users/me');
          const invalid = {
            current_password: 'Текущий пароль неверен. Проверьте его.',
          };
          setErrors(invalid);
          focusFirstError(invalid);
          setMessage('Пароль не изменён');
          return;
        } catch {
          /* The auth layer owns expired-session recovery. */
        }
      }
      if (
        error instanceof ApiError &&
        (error.status === 0 || error.status >= 500 || error.status === 401)
      ) {
        setCurrent('');
        setPassword('');
        setRepeat('');
        setMessage(
          'Результат смены пароля неизвестен. Войдите снова; если новый пароль не подходит, используйте прежний.',
        );
        session.expire();
      } else {
        const fields =
          error instanceof ApiError && error.status === 422
            ? error.fields
            : { current_password: 'Проверьте текущий пароль' };
        setErrors(fields);
        focusFirstError(fields);
        setMessage('Пароль не изменён. Проверьте отмеченные поля.');
      }
    } finally {
      if (alive.current) setPending(false);
    }
  }
  return (
    <details className={`${styles.panel} ${styles.secondaryDisclosure}`}>
      <summary>Изменить пароль</summary>
      <p>После смены пароля нужно войти снова. Другие сессии завершатся.</p>
      <form
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <Stack>
          <ErrorSummary errors={errors} />
          <PasswordField
            id="current_password"
            label="Текущий пароль"
            autoComplete="current-password"
            value={current}
            error={errors.current_password}
            disabled={pending}
            onChange={(e) => setCurrent(e.currentTarget.value)}
          />
          <PasswordField
            id="new_password"
            label="Новый пароль"
            description="От 8 символов до 72 байт"
            autoComplete="new-password"
            value={password}
            error={errors.new_password}
            disabled={pending}
            onChange={(e) => setPassword(e.currentTarget.value)}
          />
          <PasswordField
            id="repeat_password"
            label="Повторите новый пароль"
            autoComplete="new-password"
            value={repeat}
            error={errors.repeat_password}
            disabled={pending}
            onChange={(e) => setRepeat(e.currentTarget.value)}
          />
          {message && <p role="status">{message}</p>}
          <Button type="submit" loading={pending} disabled={!dirty}>
            Изменить пароль
          </Button>
        </Stack>
      </form>
    </details>
  );
}
export function ProfilePage() {
  usePageTitle('Профиль');
  const [profileDirty, setProfileDirty] = useState(false);
  const [passwordDirty, setPasswordDirty] = useState(false);
  const auth = useSession();
  const me = useRead<Account>('/users/me');
  const profile = useRead<PublicProfile | MinimalProfile>(
    `/users/${auth.user!.id}`,
    {},
    !!me.data && me.data.role !== 'admin',
  );
  const refresh = async () => {
    const result = await profile.refetch();
    if (result.error) throw result.error;
    const account = await me.refetch();
    if (account.error) throw account.error;
  };
  return (
    <>
      <DirtyFormGuard dirty={profileDirty || passwordDirty} />
      <header className={styles.heading}>
        <h1>Профиль</h1>
        <p>Ваши данные и доступ к кабинету.</p>
      </header>
      <ReadState query={me}>
        {(account) => (
          <>
            {account.role === 'admin' ? (
              <section className={styles.panel}>
                <h2>Учётная запись</h2>
                <p>{account.username}</p>
                <p>{account.email || 'Почта не указана'}</p>
              </section>
            ) : (
              <ReadState query={profile}>
                {(data) => {
                  const normalized = normalizeProfile(data);
                  return normalized.editable ? (
                    <div className={profileStyles.profileLayout}>
                      <ProfileForm
                        profile={normalized}
                        onRefresh={refresh}
                        onDirty={setProfileDirty}
                      />
                      <details
                        className={`${profileStyles.avatarSettings} ${styles.secondaryDisclosure}`}
                      >
                        <summary>Аватар профиля</summary>
                        <AvatarEditor
                          profile={normalized}
                          path={`/users/${normalized.id}/avatar`}
                          onRefresh={refresh}
                        />
                      </details>
                    </div>
                  ) : (
                    <section className={styles.panel}>
                      <p>
                        {normalized.first_name} {normalized.last_name}
                      </p>
                      <p>{normalized.username}</p>
                    </section>
                  );
                }}
              </ReadState>
            )}
            <div className={styles.lessonIntro} />
            <PasswordForm id={account.id} onDirty={setPasswordDirty} />
            <AccountLink />
          </>
        )}
      </ReadState>
    </>
  );
}
