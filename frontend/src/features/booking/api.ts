import type { components } from '../../shared/api/schema';
import { request } from '../../shared/api/client';
export type Booking = components['schemas']['BookingView'];
export type Window = components['schemas']['WindowView'];
export type Capabilities = components['schemas']['PlanningCapabilities'];
export type Operation = components['schemas']['OperationResult'];
export type Resolve = components['schemas']['ResolveResponse'];
export type Grant = components['schemas']['ParentGrantView'];
export type Command = {
  path: string;
  action: string;
  body: Record<string, unknown>;
  method?: string;
  password?: string;
  params?: Record<string, string>;
};
export function receipt(id: string, action: string) {
  return request<Operation>(`/users/me/integrations/vk/operations/${id}`, {
    params: { action },
  });
}
export function execute(command: Command, id: string) {
  return request<
    Operation | Resolve | components['schemas']['ChallengeResponse']
  >(command.path, {
    method: command.method || 'POST',
    params: command.params,
    body: { ...command.body, operation_id: id },
    headers: {
      'X-LGG-Request': 'browser',
      ...(command.password ? { 'X-LGG-Reauth': command.password } : {}),
    },
  });
}
export const accessLabel = (value: string) =>
  ({
    unresolved: 'Кабинет не подключён',
    inactive: 'Ожидает активации',
    active: 'Кабинет подключён',
    blocked: 'Доступ закрыт или курс в архиве',
    awaiting_admin_link: 'Нужно подключение администратора',
    review_required: 'Прошедшая бронь · нужна проверка',
  })[value] || 'Проверьте доступ в кабинет';
export function provisional(bookings: Booking[], lessonIds: number[]) {
  // A materialized booking stays provisional until the Lesson read has caught up.
  return bookings.filter(
    (b) =>
      b.status === 'confirmed' &&
      (!b.lesson_id || !lessonIds.includes(b.lesson_id)),
  );
}
