import { useState } from 'react';
import { Button } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { request } from '../../shared/api/client';
import { dateLabel } from '../../shared/lib/datetime';
import type { Lesson } from '../courses/queries';
import { planningRefresh } from './planning';
import { changeLesson } from './lessonChanges';

export function LessonStatusDialog({
  lesson,
  status,
  onClose,
  onSaved,
}: {
  lesson: Lesson;
  status: 'cancelled' | 'completed' | 'scheduled';
  onClose: () => void;
  onSaved?: (before: Lesson, after: Lesson) => void;
}) {
  const client = useQueryClient();
  const [pending, busy] = useState(false);
  const [unknown, setUnknown] = useState(false);
  const [error, setError] = useState('');
  const cancel = status === 'cancelled';
  const restore = status === 'scheduled';
  return (
    <ConfirmDialog
      opened
      title={
        cancel
          ? 'Отменить занятие?'
          : restore
            ? 'Восстановить занятие?'
            : 'Завершить занятие?'
      }
      confirmLabel={
        cancel
          ? 'Отменить занятие'
          : restore
            ? 'Восстановить занятие'
            : 'Завершить'
      }
      destructive={cancel}
      pending={pending}
      confirmDisabled={unknown}
      error={error}
      onCancel={onClose}
      onConfirm={() => {
        if (pending || unknown) return;
        busy(true);
        void changeLesson(lesson, { status })
          .then((after) => {
            onSaved?.(lesson, after);
            onClose();
            void client.invalidateQueries(planningRefresh);
          })
          .catch(() => {
            setUnknown(true);
            setError(
              'Результат не подтверждён. Сначала загрузите актуальное занятие; повтор автоматически не отправляется.',
            );
          })
          .finally(() => busy(false));
      }}
    >
      <p>
        {lesson.student_labels?.map((s) => s.display_name).join(', ') ||
          lesson.title}{' '}
        · {dateLabel(lesson.scheduled_at)}.
      </p>
      <p>
        {cancel
          ? 'Меняется только эта встреча. Она исчезнет из обычной сетки. История и материалы сохранятся; сроки ДЗ будут пересчитаны до следующего активного занятия.'
          : restore
            ? 'Встреча вернётся в расписание с прежним временем и материалами. Сроки ДЗ будут пересчитаны; ученик получит уведомление о восстановлении.'
            : 'Занятие будет отмечено проведённым. Материалы сохранятся.'}
      </p>
      {unknown && (
        <Button
          variant="default"
          disabled={pending}
          onClick={() => {
            busy(true);
            void request<Lesson>(`/lessons/${lesson.id}`)
              .then((after) => {
                void client.invalidateQueries(planningRefresh);
                if (after.status === status) {
                  onClose();
                  return;
                }
                setError(
                  'Актуальное состояние загружено. Закройте окно и проверьте занятие перед новой попыткой.',
                );
              })
              .catch(() =>
                setError(
                  'Не удалось прочитать состояние. Повтор остаётся заблокирован.',
                ),
              )
              .finally(() => busy(false));
          }}
        >
          Загрузить актуальное занятие
        </Button>
      )}
    </ConfirmDialog>
  );
}
