import { useState } from 'react';
import { Button, Stack } from '@mantine/core';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { FormField } from '../../../shared/ui/FormField';
import { request } from '../../../shared/api/client';
import { ApiError } from '../../../shared/api/error';
import { useFeedback } from '../../../shared/ui/FeedbackProvider';
import type { components } from '../../../shared/api/schema';
export type Cleanup = components['schemas']['CleanupResponse'];
export type Action = {
  title: string;
  description: string;
  label: string;
  path: string;
  method?: string;
  body?: unknown;
  purge?: { id: number; name: string };
};
// Keep uncertain outcomes above the dialog so cancel/reopen cannot bypass recovery.
export function useActionRecovery(action: Action | null) {
  const [paths, setPaths] = useState<Record<string, boolean>>({});
  const path = action?.path || '';
  return {
    unknown: !!paths[path],
    setUnknown: (value: boolean) =>
      setPaths((previous) => ({ ...previous, [path]: value })),
  };
}
export function CleanupPanel({ initial }: { initial?: Cleanup }) {
  const [result, setResult] = useState(initial);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  return (
    <section>
      <h2>Очистка удалённых файлов</h2>
      <p>
        Повторная очистка обрабатывает только оставшиеся задания. Удалять курс
        повторно не нужно.
      </p>
      {result && (
        <p role="status">
          Очищено файлов: {result.completed}. Ожидают очистки: {result.failed}.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      <Button
        variant="default"
        loading={pending}
        disabled={pending}
        onClick={async () => {
          setPending(true);
          setError('');
          try {
            setResult(
              await request<Cleanup>('/admin/file-deletions/retry', {
                method: 'POST',
              }),
            );
          } catch (e) {
            setError(
              e instanceof ApiError
                ? e.message
                : 'Не удалось подтвердить очистку. Можно повторить её позже.',
            );
          } finally {
            setPending(false);
          }
        }}
      >
        Повторить очистку файлов
      </Button>
    </section>
  );
}
export function ActionDialog({
  action: selectedAction,
  opened,
  onClose,
  refresh,
  onDeleted,
  recovery,
}: {
  action: Action | null;
  opened: boolean;
  recovery: ReturnType<typeof useActionRecovery>;
  onClose: () => void;
  refresh: () => Promise<void>;
  onDeleted?: (cleanup?: Cleanup) => void;
}) {
  const action = selectedAction || {
    title: 'Подтверждение',
    description: '',
    label: 'Подтвердить',
    path: '',
  };
  const [name, setName] = useState('');
  const [id, setId] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const { unknown, setUnknown } = recovery;
  const feedback = useFeedback();
  async function reconcile() {
    setPending(true);
    try {
      if (action.purge) {
        try {
          await request(`/courses/${action.purge.id}`);
        } catch (e) {
          if (e instanceof ApiError && e.status === 404) {
            onDeleted?.();
            onClose();
            return;
          }
          throw e;
        }
      }
      await refresh();
      setUnknown(false);
      setError('Данные обновлены. Проверьте состояние перед новым действием.');
      if (!action.purge) {
        onClose();
        feedback('Состояние обновлено. Проверьте результат действия.');
      }
    } catch {
      setError(
        'Не удалось проверить состояние. Повтор действия пока недоступен.',
      );
    } finally {
      setPending(false);
    }
  }
  return (
    <ConfirmDialog
      opened={opened}
      title={action.title}
      onCancel={onClose}
      pending={pending}
      error={error}
      destructive={!!action.purge}
      confirmLabel={action.label}
      confirmDisabled={
        unknown ||
        (!!action.purge &&
          (name !== action.purge.name || id !== String(action.purge.id)))
      }
      onConfirm={async () => {
        if (pending || unknown) return;
        setPending(true);
        setError('');
        try {
          const result = await request<components['schemas']['PurgeResponse']>(
            action.path,
            {
              method: action.method || 'POST',
              body: action.purge
                ? { confirm_course_id: Number(id), confirm_name: name }
                : action.body,
            },
          );
          if (action.purge) {
            onDeleted?.(result.cleanup);
            onClose();
          } else {
            onClose();
            feedback('Изменения сохранены');
            await refresh().catch(() =>
              feedback(
                'Сохранено. Обновите страницу, чтобы увидеть новое состояние.',
              ),
            );
          }
        } catch (e) {
          const uncertain =
            !(e instanceof ApiError) || e.kind !== 'http' || e.status >= 500;
          setUnknown(uncertain);
          setError(
            uncertain
              ? 'Не удалось подтвердить результат. Сначала проверьте состояние.'
              : e instanceof ApiError
                ? e.message
                : 'Не удалось выполнить действие',
          );
          if (e instanceof ApiError && e.status === 403) setUnknown(true);
        } finally {
          setPending(false);
        }
      }}
    >
      <Stack>
        <p>{action.description}</p>
        {action.purge && (
          <>
            <p>
              Курс № {action.purge.id}: {action.purge.name}. Все занятия,
              задания, решения и файлы будут удалены без возможности
              восстановления.
            </p>
            <FormField
              label="Точное название курса"
              value={name}
              onChange={(e) => setName(e.currentTarget.value)}
            />
            <FormField
              label="Номер курса"
              inputMode="numeric"
              value={id}
              onChange={(e) => setId(e.currentTarget.value)}
            />
          </>
        )}
        {unknown && (
          <Button
            variant="default"
            disabled={pending}
            onClick={() => void reconcile()}
          >
            Проверить состояние
          </Button>
        )}
      </Stack>
    </ConfirmDialog>
  );
}
