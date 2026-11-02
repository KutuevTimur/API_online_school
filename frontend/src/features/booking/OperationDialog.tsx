import { session, useSession } from '../auth/session';
import { useEffect, useRef, useState } from 'react';
import { Button } from '@mantine/core';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { ApiError } from '../../shared/api/error';
import {
  execute,
  receipt,
  type Command,
  type Operation,
  type Resolve,
} from './api';
import type { ReactNode } from 'react';
import type { components } from '../../shared/api/schema';
type Result = Operation | Resolve | components['schemas']['ChallengeResponse'];
const unknown = new Map<string, string>();
session.cleanup(() => unknown.clear());
export function OperationDialog({
  title,
  label,
  command,
  children,
  disabled,
  onClose,
  onSuccess,
  onReload,
}: {
  title: string;
  label: string;
  command: Command;
  children: ReactNode;
  disabled?: boolean;
  onReload?: () => Promise<void>;
  onClose: () => void;
  onSuccess: (result: Result) => void;
}) {
  const opener = useRef(
    document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null,
  );
  useEffect(
    () => () => {
      // Mantine reactivates the parent focus trap on its own next timer turn.
      // Restore afterward, unless a replacement invitation/reauth dialog owns focus.
      requestAnimationFrame(() => {
        window.setTimeout(() => {
          if (
            !Array.from(document.querySelectorAll('[role="dialog"]')).some(
              (dialog) => !dialog.contains(opener.current),
            ) &&
            opener.current?.isConnected
          )
            opener.current.focus();
        }, 0);
      });
    },
    [],
  );
  const auth = useSession();
  const key = `${auth.user?.id}:${command.path}:${command.action}`;
  const id = useRef<string | null>(unknown.get(key) || null);
  const locked = useRef(false);
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [uncertain, setUncertain] = useState(unknown.has(key));
  const [rejected, setRejected] = useState(false);
  async function check() {
    if (!id.current || locked.current) return;
    locked.current = true;
    busy(true);
    try {
      const result = await receipt(id.current, command.action);
      if (result.state === 'committed') {
        unknown.delete(key);
        onSuccess(result);
      } else {
        unknown.delete(key);
        setUncertain(false);
        setRejected(true);
        setError(
          'Изменение не сохранено. Обновите данные, затем проверьте форму.',
        );
      }
    } catch {
      setError(
        'Результат пока неизвестен. Проверьте снова. Повторная отправка заблокирована.',
      );
    } finally {
      locked.current = false;
      busy(false);
    }
  }
  async function send() {
    if (locked.current || id.current || uncertain || rejected) return;
    if (!navigator.onLine) {
      setError('Нет связи. Подключитесь и обновите данные перед сохранением.');
      return;
    }
    locked.current = true;
    busy(true);
    setError('');
    id.current = crypto.randomUUID();
    try {
      unknown.set(key, id.current);
      const result = await execute(command, id.current);
      unknown.delete(key);
      onSuccess(result);
    } catch (e) {
      if (
        e instanceof ApiError &&
        e.status !== 0 &&
        e.status < 500 &&
        e.status !== 401
      ) {
        unknown.delete(key);
        setRejected(true);
        setError(
          e.status === 409
            ? 'Данные изменились. Введённое сохранено. Закройте подтверждение и обновите данные.'
            : e.status === 410
              ? 'Срок ссылки истёк. Запросите новую.'
              : e.message,
        );
      } else {
        setUncertain(true);
        setError(
          'Не удалось подтвердить сохранение. Проверьте результат перед дальнейшими действиями.',
        );
      }
    } finally {
      locked.current = false;
      busy(false);
    }
  }
  return (
    <>
      <DirtyFormGuard dirty={pending || uncertain} />
      <ConfirmDialog
        opened
        title={title}
        confirmLabel={label}
        pending={pending}
        error={error}
        confirmDisabled={disabled || uncertain || rejected}
        onConfirm={() => void send()}
        onCancel={onClose}
      >
        {children}
        {rejected && onReload && (
          <Button
            variant="default"
            disabled={pending}
            onClick={() => {
              busy(true);
              void onReload()
                .then(() => {
                  id.current = null;
                  setRejected(false);
                  setError(
                    'Данные обновлены. Проверьте введённое перед подтверждением.',
                  );
                })
                .catch(() =>
                  setError('Не удалось обновить данные. Повторите проверку.'),
                )
                .finally(() => busy(false));
            }}
          >
            Обновить данные, сохранив введённое
          </Button>
        )}
        {uncertain && (
          <Button
            variant="default"
            onClick={() => void check()}
            disabled={pending}
          >
            Проверить результат
          </Button>
        )}
      </ConfirmDialog>
    </>
  );
}
