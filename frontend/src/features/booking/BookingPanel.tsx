import { request } from '../../shared/api/client';
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { Button, Checkbox, Stack } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { useRead, type Page } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { SelectField } from '../../shared/ui/SelectField';
import { DateTimeField } from '../../shared/ui/DateTimeField';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { InvitationDialog } from '../../shared/ui/InvitationDialog';
import { dateLabel, moscow } from '../../shared/lib/datetime';
import { moscowToUtc } from '../../shared/lib/time';
import { OperationDialog } from './OperationDialog';
import {
  accessLabel,
  type Booking,
  type Capabilities,
  type Command,
  type Grant,
  type Resolve,
  type Window,
} from './api';
import type { Invitation, Student } from '../students/api';
import styles from './booking.module.css';
export function BookingPanel({
  week,
  studentId,
}: {
  week: string;
  studentId?: number;
}) {
  const caps = useRead<Capabilities>('/teacher-planning/booking-capabilities');
  const [sourceParams, sourceSet] = useSearchParams();
  const selected = sourceParams.get('booking_source');
  const select = (value: string | null) => {
    const next = new URLSearchParams(sourceParams);
    if (value) next.set('booking_source', value);
    else next.delete('booking_source');
    next.delete('booking_cursor');
    next.delete('window_cursor');
    sourceSet(next);
  };
  const connection =
    caps.data?.items.find((c) => c.connection_id === selected) ||
    caps.data?.items[0];
  return (
    <ReadState query={caps}>
      {(data) =>
        data.items.length ? (
          <section className={styles.panel} aria-label="Запись и брони">
            <h2>{studentId ? 'Связь с записью' : 'Запись и брони'}</h2>
            {data.items.length > 1 && (
              <SelectField
                label="Источник записи"
                value={connection?.connection_id || null}
                data={data.items.map((c) => ({
                  value: c.connection_id,
                  label: c.label,
                }))}
                onChange={select}
              />
            )}
            {!data.enabled && (
              <p role="status">
                Управление записью отключено. Сохранённые брони доступны для
                чтения.
              </p>
            )}
            {connection && (
              <ConnectionBookings
                key={connection.connection_id + week}
                week={week}
                connection={connection.connection_id}
                writable={data.enabled && connection.enabled}
                studentId={studentId}
              />
            )}
          </section>
        ) : null
      }
    </ReadState>
  );
}
function ConnectionBookings({
  week,
  connection,
  writable,
  studentId,
}: {
  week: string;
  connection: string;
  writable: boolean;
  studentId?: number;
}) {
  const client = useQueryClient();
  const [paging, setPaging] = useSearchParams();
  const cursor = paging.get('booking_cursor') || undefined;
  const windowCursor = paging.get('window_cursor') || undefined;
  const page = (key: string, value?: string) => {
    const next = new URLSearchParams(paging);
    if (value) next.set(key, value);
    else next.delete(key);
    setPaging(next);
  };
  const setCursor = (v?: string) => page('booking_cursor', v);
  const setWindowCursor = (v?: string) => page('window_cursor', v);
  const params = {
    connection_id: connection,
    week_start: week,
    cursor,
    limit: 25,
  };
  const bookings = useRead<{ items: Booking[]; next_cursor?: string | null }>(
    studentId
      ? '/teacher-planning/linked-bookings'
      : '/teacher-planning/bookings',
    studentId
      ? {
          connection_id: connection,
          student_user_id: studentId,
          cursor,
          limit: 25,
        }
      : params,
    true,
    60000,
  );
  const windows = useRead<{ items: Window[]; next_cursor?: string | null }>(
    '/teacher-planning/booking-windows',
    { ...params, cursor: windowCursor },
    !studentId,
    60000,
  );
  const [publish, setPublish] = useState(false);
  const [date, setDate] = useState<string | null>(week);
  const [time, setTime] = useState('15:00');
  const [error, setError] = useState('');
  const [command, setCommand] = useState<{
    title: string;
    label: string;
    command: Command;
    text: string;
  } | null>(null);
  const [target, setTarget] = useState<Booking | null>(null);
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [invitationUsername, setInvitationUsername] = useState<string | null>(
    null,
  );
  const [message, setMessage] = useState('');
  async function refresh() {
    await client.invalidateQueries({ queryKey: ['student-read'] });
  }
  const publishWindow = () => {
    const start = date && moscowToUtc(date, time);
    if (
      !start ||
      !date ||
      date < week ||
      date > moscow(week).add(6, 'day').format('YYYY-MM-DD') ||
      Date.parse(start) <= Date.now()
    ) {
      setError('Выберите будущее время в указанной неделе.');
      document.getElementById('window-time')?.focus();
      return;
    }
    setError('');
    setCommand({
      title: 'Открыть окно записи',
      label: 'Открыть окно',
      text: `${dateLabel(start)} · 55 минут. Это окно только выбранной недели.`,
      command: {
        path: '/teacher-planning/booking-windows',
        action: 'windows_publish',
        body: {
          connection_id: connection,
          week_start: week,
          items: [
            {
              start_at: start,
              end_at: new Date(Date.parse(start) + 55 * 60000).toISOString(),
            },
          ],
        },
      },
    });
  };
  function grant(
    booking: Booking,
    item: Grant,
    decision: 'confirm' | 'revoke' | 'reject',
  ) {
    const label =
      decision === 'confirm'
        ? 'Подтвердить связь'
        : decision === 'reject'
          ? 'Отклонить связь'
          : 'Отозвать связь';
    setCommand({
      title: label,
      label,
      text: `${item.parent_label} → ${booking.recipient.first_name} ${booking.recipient.last_name}. Только запись и разрешённое расписание у вас. Доступ к кабинету, решениям и оценкам не предоставляется.`,
      command: {
        path: `/teacher-planning/parent-grants/${item.grant_id}/${decision}`,
        action: 'grant_' + decision,
        body: { expected_revision: item.revision },
      },
    });
  }
  return (
    <Stack>
      {studentId ? (
        <p>История записи · все даты · МСК</p>
      ) : (
        <p>
          Неделя {moscow(week).format('D MMMM')} —{' '}
          {moscow(week).add(6, 'day').format('D MMMM YYYY')} · МСК
        </p>
      )}
      {!writable && (
        <p>Источник закрыт для изменений. Подтверждённые брони сохраняются.</p>
      )}
      {!studentId && (
        <>
          <Button
            variant="default"
            disabled={!writable}
            onClick={() => setPublish(!publish)}
            aria-expanded={publish}
          >
            Открыть время для записи
          </Button>
          {publish && (
            <form
              noValidate
              onSubmit={(e) => {
                e.preventDefault();
                publishWindow();
              }}
            >
              <DirtyFormGuard dirty={publish} />
              <Stack>
                <DateTimeField
                  date={date}
                  time={time}
                  timeId="window-time"
                  onDateChange={setDate}
                  onTimeChange={setTime}
                  error={error}
                />
                <p>
                  Продолжительность окна — 55 минут. На следующую неделю окно не
                  переносится.
                </p>
                <Button type="submit" disabled={!writable}>
                  Открыть окно
                </Button>
              </Stack>
            </form>
          )}
          <details>
            <summary>Окна выбранной недели</summary>
            <ReadState query={windows}>
              {(data) => (
                <>
                  {!data.items.length && (
                    <p>
                      Открытых окон пока нет. Пустой календарь не разрешает
                      запись.
                    </p>
                  )}
                  <ul className={styles.list}>
                    {data.items.map((w) => (
                      <li key={w.window_id}>
                        <span>
                          {dateLabel(w.start_at)} ·{' '}
                          {w.status === 'published'
                            ? 'Открыто'
                            : w.status === 'consumed'
                              ? 'Занято бронью'
                              : 'Закрыто'}
                        </span>
                        {w.status === 'published' && (
                          <Button
                            variant="default"
                            disabled={!writable}
                            onClick={() =>
                              setCommand({
                                title: 'Закрыть окно',
                                label: 'Закрыть окно',
                                text: `${dateLabel(w.start_at)}. Новая запись на это время станет недоступна.`,
                                command: {
                                  path: `/teacher-planning/booking-windows/${w.window_id}/close`,
                                  action: 'window_close',
                                  body: { expected_revision: w.revision },
                                },
                              })
                            }
                          >
                            Закрыть окно
                          </Button>
                        )}
                      </li>
                    ))}
                  </ul>
                  <Button
                    variant="default"
                    disabled={!windowCursor}
                    onClick={() => setWindowCursor(undefined)}
                  >
                    К первым окнам
                  </Button>
                  {data.next_cursor && (
                    <Button
                      variant="default"
                      onClick={() => setWindowCursor(data.next_cursor!)}
                    >
                      Следующие окна
                    </Button>
                  )}
                </>
              )}
            </ReadState>
          </details>
        </>
      )}
      <ReadState query={bookings}>
        {(data) => (
          <>
            {!data.items.length && <p>Броней на эту неделю пока нет.</p>}
            <ul className={styles.list}>
              {data.items
                .filter(
                  (b) =>
                    !studentId ||
                    b.recipient.linked_student_user_id === studentId,
                )
                .map((b) => (
                  <li key={b.booking_id} data-booking-id={b.booking_id}>
                    <div>
                      <strong>
                        {b.recipient.first_name} {b.recipient.last_name}
                        {b.recipient.grade
                          ? ` · ${b.recipient.grade} класс`
                          : ''}
                      </strong>
                      <p>
                        {dateLabel(b.start_at)} ·{' '}
                        {b.status === 'confirmed'
                          ? 'Бронь подтверждена'
                          : 'Бронь отменена'}
                      </p>
                      <p>{accessLabel(b.access_state)}</p>
                      {b.lesson_id ? (
                        <Link to={`/teacher/lessons/${b.lesson_id}`}>
                          Открыть занятие
                        </Link>
                      ) : (
                        <p>Время занято. Повторная запись не нужна.</p>
                      )}
                      {b.recipient.linked_student_user_id && (
                        <Link
                          to={`/teacher/students/${b.recipient.linked_student_user_id}`}
                        >
                          К ученику
                        </Link>
                      )}
                      {b.status === 'confirmed' &&
                        writable &&
                        !['blocked', 'awaiting_admin_link'].includes(
                          b.access_state,
                        ) && (
                          <Button
                            variant="default"
                            onClick={() => setTarget(b)}
                          >
                            {b.lesson_id
                              ? 'Доступ в кабинет'
                              : 'Подключить кабинет'}
                          </Button>
                        )}
                      {b.recipient.parent_grants.map((g) => (
                        <div key={g.grant_id} className={styles.relation}>
                          <p>
                            {g.parent_label} ·{' '}
                            {g.state === 'pending'
                              ? 'Связь ожидает подтверждения'
                              : g.state === 'confirmed'
                                ? 'Связь подтверждена'
                                : g.state === 'revoked'
                                  ? 'Связь отозвана'
                                  : 'Связь отклонена'}
                          </p>
                          {writable && g.state === 'pending' && (
                            <>
                              <Button
                                variant="default"
                                onClick={() => grant(b, g, 'confirm')}
                              >
                                Подтвердить связь
                              </Button>
                              <Button
                                variant="subtle"
                                onClick={() => grant(b, g, 'reject')}
                              >
                                Отклонить связь
                              </Button>
                            </>
                          )}
                          {writable && g.state === 'confirmed' && (
                            <Button
                              variant="default"
                              onClick={() => grant(b, g, 'revoke')}
                            >
                              Отозвать связь
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  </li>
                ))}
            </ul>
            <Button
              variant="default"
              disabled={!cursor}
              onClick={() => setCursor(undefined)}
            >
              К первым броням
            </Button>
            {data.next_cursor && (
              <Button
                variant="default"
                onClick={() => setCursor(data.next_cursor!)}
              >
                Следующие брони
              </Button>
            )}
          </>
        )}
      </ReadState>
      <Button variant="subtle" onClick={() => void refresh()}>
        Обновить запись и брони
      </Button>
      {message && <p role="status">{message}</p>}
      {command && (
        <OperationDialog
          {...command}
          onClose={() => setCommand(null)}
          onSuccess={() => {
            setCommand(null);
            setPublish(false);
            setMessage('Изменение сохранено.');
            void refresh();
          }}
        >
          {command.text}
        </OperationDialog>
      )}
      {target && (
        <ResolveBooking
          booking={target}
          onClose={() => setTarget(null)}
          onReload={async () => {
            const row = await request<Booking>(
              `/teacher-planning/bookings/${target.booking_id}`,
            );
            setTarget(row);
          }}
          onSuccess={(r) => {
            setTarget(null);
            setInvitation(r.invitation || null);
            setInvitationUsername(r.student_username || null);
            setMessage(
              r.invitation
                ? 'Приглашение готово.'
                : r.operation.result?.invitation_issued
                  ? 'Доступ выдан. Одноразовая ссылка не повторяется при проверке результата. Обновите бронь и выдайте новое приглашение, если ссылка не была получена.'
                  : 'Кабинет подключён. Для активированного аккаунта новая ссылка не нужна.',
            );
            void refresh();
          }}
        />
      )}
      <InvitationDialog
        invitation={invitation}
        username={invitationUsername}
        onClose={() => setInvitation(null)}
      />
    </Stack>
  );
}
function ResolveBooking({
  booking: b,
  onClose,
  onSuccess,
  onReload,
}: {
  booking: Booking;
  onReload: () => Promise<void>;
  onClose: () => void;
  onSuccess: (r: Resolve) => void;
}) {
  const [mode, setMode] = useState<string | null>(
    b.recipient.linked_student_user_id ? 'own_student' : 'new_student',
  );
  const [student, setStudent] = useState<string | null>(
    b.recipient.linked_student_user_id
      ? String(b.recipient.linked_student_user_id)
      : null,
  );
  const [past, setPast] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [offset, setOffset] = useState(0);
  const students = useRead<Page<Student>>(
    '/users/students',
    { limit: 20, offset },
    mode === 'own_student',
  );
  // Activated accounts use self linking; teacher never creates a replacement account.
  const body = {
    expected_revision: b.revision,
    expected_recipient_revision: b.recipient.revision,
    review_past: past,
    mode,
    ...(mode === 'own_student' ? { student_user_id: Number(student) } : {}),
  };
  const command: Command =
    b.access_state === 'active' && !b.lesson_id
      ? {
          path: `/teacher-planning/bookings/${b.booking_id}/materialize`,
          action: 'booking_materialize',
          body: {
            expected_revision: b.revision,
            expected_recipient_revision: b.recipient.revision,
            review_past: past,
          },
        }
      : {
          path: `/teacher-planning/bookings/${b.booking_id}/resolve-invite`,
          action: 'recipient_resolve',
          body,
        };
  return (
    <OperationDialog
      onReload={onReload}
      title="Подключить кабинет"
      label={confirm ? 'Выдать доступ' : 'Продолжить'}
      command={command}
      disabled={
        !confirm ||
        (mode === 'own_student' && !student) ||
        (b.access_state === 'active' && !!b.lesson_id)
      }
      onClose={onClose}
      onSuccess={(r) =>
        onSuccess('operation' in r ? (r as Resolve) : { operation: r })
      }
    >
      <Stack>
        <p>
          {b.recipient.first_name} {b.recipient.last_name} ·{' '}
          {dateLabel(b.start_at)}. Будут подключены все сохранённые брони этого
          ребёнка у вас. Родитель доступа в кабинет не получает.
        </p>
        {b.access_state === 'active' ? (
          <p>
            Аккаунт уже активирован. Используйте обычный вход. Новая ссылка
            активации не выдаётся.
          </p>
        ) : (
          <>
            <SelectField
              label="Учебный аккаунт"
              value={mode}
              onChange={setMode}
              data={[
                { value: 'new_student', label: 'Новый ученик' },
                { value: 'own_student', label: 'Мой существующий ученик' },
              ]}
              disabled={!!b.recipient.linked_student_user_id}
            />
            {mode === 'own_student' && (
              <ReadState query={students}>
                {(data) => (
                  <Stack>
                    <SelectField
                      label="Свой ученик"
                      searchable
                      value={student}
                      onChange={setStudent}
                      data={data.items.map((s) => ({
                        value: String(s.user_id),
                        label: `${s.first_name} ${s.last_name} · ${s.username}`,
                      }))}
                      disabled={!!b.recipient.linked_student_user_id}
                    />
                    {data.total > 20 && (
                      <>
                        <p>
                          Ученики {offset + 1}–
                          {Math.min(offset + 20, data.total)} из {data.total}
                        </p>
                        <Button
                          variant="default"
                          disabled={offset === 0}
                          onClick={() => setOffset(Math.max(0, offset - 20))}
                        >
                          Предыдущие ученики
                        </Button>
                        <Button
                          variant="default"
                          disabled={offset + 20 >= data.total}
                          onClick={() => setOffset(offset + 20)}
                        >
                          Следующие ученики
                        </Button>
                      </>
                    )}
                  </Stack>
                )}
              </ReadState>
            )}
            <p>
              Если существующий аккаунт активирован, ученик сначала подтверждает
              свою связь в профиле. Преподаватель не подменяет это
              подтверждение.
            </p>
          </>
        )}
        <Checkbox
          label="Проверил прошедшие брони этого ребёнка; разрешаю добавить их в историю"
          checked={past}
          onChange={(e) => setPast(e.currentTarget.checked)}
        />
        <Checkbox
          label="Проверил адресата и область доступа"
          checked={confirm}
          onChange={(e) => setConfirm(e.currentTarget.checked)}
        />
      </Stack>
    </OperationDialog>
  );
}
