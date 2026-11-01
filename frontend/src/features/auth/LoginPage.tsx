import { PasswordField } from './PasswordField';
import { useState, useRef, useEffect, type FormEvent } from 'react';
import { Button, TextInput, Alert } from '@mantine/core';
import { useLocation, useNavigate } from 'react-router';
import { session, useSession, safeReturn, currentUser } from './session';
import { AppShell } from '../../shared/ui/AppShell';
import styles from '../../shared/ui/ui.module.css';
export function LoginPage({
  reauth = false,
  embedded = false,
}: {
  reauth?: boolean;
  embedded?: boolean;
}) {
  const current = useSession();
  useEffect(() => {
    const previous = document.title;
    document.title = 'Вход — LGG';
    return () => {
      if (embedded) document.title = previous;
    };
  }, [embedded]);
  const navigate = useNavigate();
  const location = useLocation();
  useEffect(() => {
    if (!reauth && current.status === 'boot')
      void session.refresh().catch(() => {});
    if (!reauth && current.user)
      navigate(
        safeReturn(
          new URLSearchParams(location.search).get('returnTo'),
          current.user,
        ),
        { replace: true },
      );
  }, [current, reauth, navigate, location.search]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (reauth) usernameRef.current?.focus();
  }, [reauth]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending.current) return;
    if (!username || !password) {
      setError('Введите логин и пароль');
      (!username ? usernameRef : passwordRef).current?.focus();
      return;
    }
    pending.current = true;
    setBusy(true);
    setError('');
    try {
      await session.login(username, password);
      setPassword('');
      if (!reauth)
        navigate(
          safeReturn(
            new URLSearchParams(location.search).get('returnTo'),
            currentUser()!,
          ),
          { replace: true },
        );
    } catch (err) {
      setPassword('');
      setError(
        err instanceof TypeError || err instanceof DOMException
          ? 'Нет связи. Попробуйте ещё раз'
          : err instanceof Error
            ? err.message
            : 'Не удалось войти',
      );
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  const content = (
    <div className={styles.login}>
      <section className={`${styles.panel} ${styles.lesson}`}>
        {!embedded && (
          <h1>{reauth ? 'Войдите снова' : 'Учёба в одном месте.'}</h1>
        )}
        <p>
          {reauth
            ? 'Срок сессии истёк. Несохранённая работа остаётся в этой вкладке до входа тем же пользователем.'
            : 'Занятия, материалы и домашние задания — в вашей онлайн-школе.'}
        </p>
      </section>
      <section className={styles.panel}>
        <h2>Вход в кабинет</h2>
        <form noValidate onSubmit={submit} aria-busy={busy}>
          <TextInput
            ref={usernameRef}
            label="Логин"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.currentTarget.value)}
            error={error && !username ? 'Введите логин' : undefined}
          />
          <PasswordField
            ref={passwordRef}
            label="Пароль"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.currentTarget.value)}
            error={error && !password ? 'Введите пароль' : undefined}
            mt="md"
          />
          <div style={{ minHeight: '4rem' }}>
            {(error || current.message) && (
              <Alert role="alert" color="red" mt="md">
                {error || current.message}
              </Alert>
            )}
          </div>
          <Button type="submit" loading={busy} fullWidth>
            Войти
          </Button>
        </form>
        <p className={styles.muted}>
          Нет доступа или забыли пароль? Обратитесь к преподавателю или
          администратору за новой ссылкой.
        </p>
      </section>
    </div>
  );
  return embedded ? content : <AppShell>{content}</AppShell>;
}
