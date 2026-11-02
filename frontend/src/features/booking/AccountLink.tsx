import { useState } from 'react';
import { Button, Stack } from '@mantine/core';
import { useRead } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { useSession } from '../auth/session';
import { PasswordField } from '../auth/PasswordField';
import { SelectField } from '../../shared/ui/SelectField';
import { OperationDialog } from './OperationDialog';
import type { Command } from './api';
import styles from './booking.module.css';
type Status = {
  items: { connection_id: string; purpose: string; revision: number }[];
  challenges: {
    challenge_id: string;
    revision: number;
    claimed_contact: string | null;
    expires_at: string;
  }[];
  connections: { connection_id: string; label: string }[];
};
export function AccountLink() {
  const auth = useSession();
  const status = useRead<Status>(
    '/users/me/integrations/vk',
    {},
    auth.user?.role !== 'admin',
  );
  const [selected, select] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [command, setCommand] = useState<Command | null>(null);
  const [secret, setSecret] = useState('');
  const [message, setMessage] = useState('');
  if (auth.user?.role === 'admin') return null;
  // Feature is optional; an unavailable server capability must leave the profile usable.
  if (status.error && 'status' in status.error && status.error.status === 403)
    return null;
  return (
    <details className={styles.panel}>
      <summary>Связь с записью</summary>
      <ReadState query={status}>
        {(data) => (
          <Stack>
            <p>
              Связь подтверждается вами в текущей сессии. Она не создаёт новый
              учебный аккаунт и не подключает другого преподавателя.
            </p>
            <SelectField
              label="Источник записи"
              value={selected || data.connections[0]?.connection_id || null}
              onChange={select}
              data={data.connections.map((c) => ({
                value: c.connection_id,
                label: c.label,
              }))}
            />
            <PasswordField
              label="Текущий пароль для подтверждения связи"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
            />
            <Button
              disabled={!password || !data.connections.length}
              onClick={() =>
                setCommand({
                  path: '/users/me/integrations/vk',
                  action: 'challenge_issue',
                  password,
                  body: {
                    connection_id:
                      selected || data.connections[0]?.connection_id,
                    purpose: auth.user?.role,
                  },
                })
              }
            >
              Получить код связи
            </Button>
            {secret && (
              <>
                <PasswordField
                  label="Одноразовый код связи"
                  value={secret}
                  readOnly
                />
                <p>
                  Код действует 10 минут. Внешний канал в этой локальной версии
                  отключён. После локального подтверждения обновите состояние.
                </p>
              </>
            )}
            {!data.items.length && <p>Кабинет пока не связан с записью.</p>}
            {data.items.map((link) => (
              <div key={link.connection_id}>
                <p>Связь подтверждена.</p>
                <Button
                  variant="default"
                  disabled={!password}
                  onClick={() =>
                    setCommand({
                      path: '/users/me/integrations/vk',
                      method: 'DELETE',
                      action: 'identity_unlink',
                      password,
                      params: { connection_id: link.connection_id },
                      body: { expected_revision: link.revision },
                    })
                  }
                >
                  Отозвать связь
                </Button>
              </div>
            ))}
            {data.challenges.map((c) => (
              <div key={c.challenge_id}>
                <p>
                  {c.claimed_contact
                    ? `Связь ожидает вашего подтверждения · ${c.claimed_contact}`
                    : 'Ожидается подтверждение одноразового кода'}
                </p>
                {c.claimed_contact && (
                  <Button
                    disabled={!password}
                    onClick={() =>
                      setCommand({
                        path: `/users/me/integrations/vk/challenges/${c.challenge_id}/confirm`,
                        action: 'challenge_confirm',
                        password,
                        body: { expected_revision: c.revision },
                      })
                    }
                  >
                    Подтвердить свою связь
                  </Button>
                )}
              </div>
            ))}
            <Button variant="default" onClick={() => void status.refetch()}>
              Обновить состояние связи
            </Button>
            {message && <p role="status">{message}</p>}
            {command && (
              <OperationDialog
                title={
                  command.action === 'identity_unlink'
                    ? 'Отозвать связь'
                    : 'Подтвердить свою связь'
                }
                label="Подтвердить"
                command={command}
                onClose={() => setCommand(null)}
                onSuccess={(r) => {
                  setCommand(null);
                  setPassword('');
                  if ('secret' in r && r.secret) setSecret(r.secret);
                  else setSecret('');
                  setMessage('Состояние связи сохранено.');
                  void status.refetch();
                }}
              >
                <p>
                  Адресат — ваш текущий аккаунт {auth.user?.username}. Учебные
                  права, бронь и история сохраняются. Код и пароль не передаются
                  другим пользователям.
                </p>
              </OperationDialog>
            )}
          </Stack>
        )}
      </ReadState>
    </details>
  );
}
