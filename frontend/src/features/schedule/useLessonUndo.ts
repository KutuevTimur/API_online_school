import { useQueryClient } from '@tanstack/react-query';
import type { Lesson } from '../courses/queries';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { ApiError } from '../../shared/api/error';
import { changeLesson } from './lessonChanges';
import { planningRefresh } from './planning';

export function useLessonUndo() {
  const show = useFeedback();
  const client = useQueryClient();
  return (before: Lesson, after: Lesson) => {
    const cancelled = after.status === 'cancelled';
    const deadline = Date.now() + 15000;
    const inverse = cancelled
      ? { status: before.status }
      : { scheduled_at: before.scheduled_at };
    show(
      cancelled
        ? 'Занятие отменено. История и материалы сохранены.'
        : 'Занятие перенесено.',
      {
        durationMs: 15000,
        expiresAt: deadline,
        action: {
          label: 'Вернуть',
          run: async () => {
            if (Date.now() > deadline)
              throw new Error(
                'Время быстрого возврата истекло. Откройте занятие для дальнейших изменений.',
              );
            try {
              await changeLesson(after, inverse);
            } catch (e) {
              throw new Error(
                e instanceof ApiError && e.status === 409
                  ? 'Занятие уже изменилось. Возврат не выполнен; обновите расписание.'
                  : 'Результат возврата не подтверждён. Обновите расписание перед следующим действием.',
              );
            } finally {
              void client.invalidateQueries(planningRefresh);
            }
          },
        },
      },
    );
  };
}
