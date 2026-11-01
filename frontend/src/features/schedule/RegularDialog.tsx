import { useState } from 'react';
import { Checkbox, Stack, Button } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import { dateLabel } from '../../shared/lib/datetime';
import { type RegularOperation, planningRefresh } from './planning';
export function RegularDialog({
  operation,
  onClose,
  onSaved,
}: {
  operation: RegularOperation;
  onClose: () => void;
  onSaved: (op: RegularOperation) => void;
}) {
  const [op, setOp] = useState(operation);
  const [ack, setAck] = useState(false);
  const [pending, busy] = useState(false);
  const [unknown, setUnknown] = useState(false);
  const [error, setError] = useState('');
  const client = useQueryClient();
  const conflicts = op.preview.occurrences.some(
    (o) =>
      o.conflict_lesson_ids?.length ||
      0 ||
      o.conflict_occurrence_dates?.length ||
      0,
  );
  async function recover() {
    busy(true);
    try {
      const result = await request<RegularOperation>(
        `/lessons/regular/operations/${op.operation_id}`,
      );
      setOp(result);
      setUnknown(false);
      setAck(false);
      if (result.state === 'committed') {
        await client.invalidateQueries(planningRefresh);
        onSaved(result);
      } else
        setError('Результат прочитан. Проверьте даты и подтвердите ещё раз.');
    } catch {
      setError(
        'Не удалось прочитать результат. Сохранение заблокировано до проверки.',
      );
    } finally {
      busy(false);
    }
  }
  return (
    <ConfirmDialog
      opened
      title="Регулярное расписание · МСК"
      confirmLabel={
        op.action === 'stop'
          ? 'Остановить серию'
          : op.action === 'cancel_future'
            ? 'Отменить перечисленные встречи'
            : 'Подтвердить запись'
      }
      pending={pending}
      confirmDisabled={unknown || (conflicts && !ack)}
      error={error}
      onCancel={onClose}
      onConfirm={() => {
        if (pending || unknown) return;
        busy(true);
        setError('');
        void request<RegularOperation>(
          `/lessons/regular/operations/${op.operation_id}/confirm`,
          {
            method: 'POST',
            body: {
              preview_revision: op.preview_revision,
              acknowledge_conflicts: ack,
            },
          },
        )
          .then(async (result) => {
            await client.invalidateQueries(planningRefresh);
            onSaved(result);
          })
          .catch((e) => {
            setUnknown(true);
            setAck(false);
            setError(
              e instanceof ApiError && e.status === 409
                ? 'Расписание изменилось. Загрузите новый предпросмотр и подтвердите его.'
                : 'Не удалось подтвердить результат. Сначала проверьте состояние операции.',
            );
          })
          .finally(() => busy(false));
      }}
    >
      <Stack>
        <p>
          {op.preview.title} · {op.preview.count} встреч. Продление только
          вручную.
        </p>
        {op.action === 'stop' && (
          <p>Назначенные встречи сохранятся. Продление станет недоступно.</p>
        )}
        <ul>
          {op.preview.occurrences.map((o) => (
            <li key={o.scheduled_at}>
              {dateLabel(o.scheduled_at)} · {o.duration_minutes} мин
              {((o.conflict_lesson_ids?.length || 0) > 0 ||
                (o.conflict_occurrence_dates?.length || 0) > 0) && (
                <strong> · Есть пересечение</strong>
              )}
            </li>
          ))}
        </ul>
        {op.preview.last_date && (
          <p>Последняя дата: {dateLabel(op.preview.last_date)}</p>
        )}
        {conflicts && (
          <Checkbox
            label="Вижу пересечения и подтверждаю сохранение"
            checked={ack}
            onChange={(e) => setAck(e.currentTarget.checked)}
          />
        )}
        {unknown && (
          <Button
            variant="default"
            disabled={pending}
            onClick={() => void recover()}
          >
            Проверить результат операции
          </Button>
        )}
      </Stack>
    </ConfirmDialog>
  );
}
