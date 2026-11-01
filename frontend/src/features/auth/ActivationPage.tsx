import { PasswordField } from './PasswordField';
import { useState, useRef, useEffect, type FormEvent } from 'react';
import { Alert, Button } from '@mantine/core';
import { Link } from 'react-router';
import { AppShell } from '../../shared/ui/AppShell';
import styles from '../../shared/ui/ui.module.css';
// Capture and scrub before React effects / subsequent requests. Memory only.
let fragment =
  new URLSearchParams(window.location.hash.slice(1)).get('token') || '';
if (window.location.hash)
  window.history.replaceState(
    window.history.state,
    '',
    window.location.pathname + window.location.search,
  );
export function ActivationPage({ reset = false }: { reset?: boolean }) {
  const [token] = useState(fragment);
  useEffect(() => {
    fragment = '';
    document.title = (reset ? 'Новый пароль' : 'Активация доступа') + ' — LGG';
  }, [reset]);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const pending = useRef(false);
  const first = useRef<HTMLInputElement>(null);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending.current) return;
    const bytes = new TextEncoder().encode(password).length;
    if (
      [...password].length < 8 ||
      bytes < 8 ||
      bytes > 72 ||
      password !== confirm
    ) {
      setError(
        [...password].length < 8 || bytes < 8 || bytes > 72
          ? 'Не менее 8 символов и не более 72 байт UTF-8'
          : 'Пароли не совпадают',
      );
      first.current?.focus();
      return;
    }
    pending.current = true;
    setBusy(true);
    setError('');
    try {
      const response = await fetch('/api/account_invitations/consume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          purpose: reset ? 'reset' : 'invite',
          new_password: password,
        }),
        signal: AbortSignal.timeout(30000),
      });
      if (!response.ok)
        throw new Error(
          response.status >= 500
            ? 'Сервис недоступен. Повторите позже'
            : 'Ссылка недействительна или уже использована. Получите новую ссылку у преподавателя или администратора',
        );
      setPassword('');
      setConfirm('');
      setDone(true);
    } catch (err) {
      setError(
        err instanceof TypeError || err instanceof DOMException
          ? 'Нет связи. Не удалось подтвердить сохранение. Попробуйте войти с новым паролем перед повтором'
          : err instanceof Error
            ? err.message
            : 'Не удалось подтвердить сохранение',
      );
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  return (
    <AppShell>
      <section className={styles.panel}>
        <h1>{reset ? 'Новый пароль' : 'Активация доступа'}</h1>
        {done ? (
          <>
            <p role="status">Пароль сохранён. Теперь войдите в кабинет.</p>
            <Link to="/login">Перейти ко входу</Link>
          </>
        ) : !token ? (
          <p role="alert">
            Нужна действующая ссылка от преподавателя или администратора.
            Получите новую ссылку.
          </p>
        ) : (
          <form noValidate onSubmit={submit} aria-busy={busy}>
            <p>
              Не менее 8 символов и не более 72 байт UTF-8. Кириллица занимает
              больше одного байта на символ.
            </p>
            <PasswordField
              ref={first}
              label="Новый пароль"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              error={error || undefined}
            />
            <PasswordField
              label="Повторите пароль"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.currentTarget.value)}
              mt="md"
            />
            {error && (
              <Alert role="alert" color="red" mt="md">
                {error}
              </Alert>
            )}
            <Button type="submit" loading={busy} mt="md">
              Сохранить пароль
            </Button>
          </form>
        )}
      </section>
    </AppShell>
  );
}
