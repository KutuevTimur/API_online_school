import { useRef, useState } from 'react';
import { Button, Stack } from '@mantine/core';
import { ConfirmDialog } from './ConfirmDialog';
import { FormField } from './FormField';
import { invitationURL, type Invitation } from '../../features/students/api';
export function InvitationDialog({
  invitation,
  onClose,
  purpose = 'invite',
  audience = 'student',
}: {
  invitation: Invitation | null;
  purpose?: 'invite' | 'reset';
  audience?: 'student' | 'user';
  onClose: () => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [message, setMessage] = useState('');
  const url = invitationURL(
    invitation?.activation_link,
    import.meta.env.VITE_PUBLIC_ORIGIN || window.location.origin,
    purpose,
  );
  return (
    <ConfirmDialog
      opened={invitation !== null}
      title={
        purpose === 'reset'
          ? 'Сброс пароля'
          : audience === 'user'
            ? 'Приглашение пользователя'
            : 'Приглашение ученика'
      }
      confirmLabel="Готово"
      onConfirm={onClose}
      onCancel={onClose}
    >
      <Stack>
        {url ? (
          <>
            <p>
              Передайте ссылку лично пользователю. Любой получивший её сможет
              {purpose === 'reset'
                ? ' задать новый пароль.'
                : ' активировать аккаунт.'}{' '}
              Новая ссылка отменяет предыдущую.
            </p>
            <FormField
              ref={input}
              label={
                purpose === 'reset'
                  ? 'Ссылка сброса пароля'
                  : 'Ссылка приглашения'
              }
              value={url}
              readOnly
              onFocus={(e) => e.currentTarget.select()}
            />
            <p>
              Действует до{' '}
              {invitation?.expires_at
                ? new Date(invitation.expires_at).toLocaleString('ru-RU', {
                    timeZone: 'Europe/Moscow',
                  }) + ' МСК'
                : 'срока, указанного при выдаче'}
              . Ссылка одноразовая.
            </p>
            <Button
              onClick={() => {
                void navigator.clipboard
                  ?.writeText(url)
                  .then(() => setMessage('Ссылка скопирована'))
                  .catch(() => {
                    input.current?.focus();
                    input.current?.select();
                    setMessage(
                      'Не удалось скопировать. Ссылка выделена — скопируйте её вручную.',
                    );
                  });
                if (!navigator.clipboard) {
                  input.current?.focus();
                  input.current?.select();
                  setMessage('Выделите ссылку и скопируйте вручную.');
                }
              }}
            >
              Скопировать ссылку
            </Button>
            <p role="status">{message}</p>
          </>
        ) : (
          <p role="status">
            Приглашение недоступно: аккаунт уже активирован или доступ
            ограничен. Для восстановления доступа обратитесь к администратору.
          </p>
        )}
      </Stack>
    </ConfirmDialog>
  );
}
