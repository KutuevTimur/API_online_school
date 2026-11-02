import { useEffect, useRef, useState, type PointerEvent } from 'react';
import { Button, Group } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { useRead, type Lesson } from '../courses/queries';
import { SelectField } from '../../shared/ui/SelectField';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { dateLabel } from '../../shared/lib/datetime';
import { OperationDialog } from './OperationDialog';
import type { Booking, Capabilities, Command, Window } from './api';
import styles from './availability.module.css';
export function overlaps(start: string, end: string, from: string, to: string) {
  return (
    Date.parse(start) < Date.parse(to) && Date.parse(end) > Date.parse(from)
  );
}
export function cellBusy(
  start: string,
  lessons: Lesson[],
  bookings: Booking[],
) {
  const end = new Date(Date.parse(start) + 55 * 60000).toISOString();
  return (
    lessons.some(
      (l) =>
        l.status !== 'cancelled' &&
        overlaps(
          start,
          end,
          l.scheduled_at,
          new Date(
            Date.parse(l.scheduled_at) + (l.duration_minutes || 55) * 60000,
          ).toISOString(),
        ),
    ) ||
    bookings.some(
      (b) =>
        b.status === 'confirmed' &&
        !b.lesson_id &&
        overlaps(start, end, b.start_at, b.end_at),
    )
  );
}
export function selectedPublished(windows: Window[], starts: Set<string>) {
  return windows.filter(
    (w) =>
      w.status === 'published' &&
      [...starts].some((start) =>
        overlaps(
          start,
          new Date(Date.parse(start) + 55 * 60000).toISOString(),
          w.start_at,
          w.end_at,
        ),
      ),
  );
}
export function useAvailability(week: string) {
  const client = useQueryClient();
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60000);
    return () => window.clearInterval(timer);
  }, []);
  const capabilities = useRead<Capabilities>(
    '/teacher-planning/booking-capabilities',
  );
  const [source, setSource] = useState<string | null>(null);
  const connection =
    capabilities.data?.items.find((c) => c.connection_id === source) ||
    capabilities.data?.items[0];
  const windows = useRead<{ items: Window[]; next_cursor?: string | null }>(
    '/teacher-planning/booking-windows',
    { connection_id: connection?.connection_id, week_start: week, limit: 100 },
    !!connection,
    60000,
  );
  const [editing, setEditing] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmation, setConfirmation] = useState<{
    title: string;
    label: string;
    command: Command;
    text: string;
    summary?: string[];
  } | null>(null);
  const [message, setMessage] = useState('');
  const stroke = useRef<boolean | null>(null);
  const touch = useRef(false);
  const available =
    !!capabilities.data?.enabled &&
    !!connection?.enabled &&
    !!windows.data &&
    !windows.isError &&
    !windows.data.next_cursor;
  useEffect(() => {
    const stop = () => {
      stroke.current = null;
    };
    window.addEventListener('pointerup', stop);
    window.addEventListener('blur', stop);
    return () => {
      window.removeEventListener('pointerup', stop);
      window.removeEventListener('blur', stop);
    };
  }, []);
  function change(start: string, value: boolean) {
    setSelected((previous) => {
      const next = new Set(previous);
      if (value) next.add(start);
      else next.delete(start);
      return next;
    });
  }
  function published(start: string) {
    const end = new Date(Date.parse(start) + 55 * 60000).toISOString();
    return windows.data?.items.find(
      (w) =>
        w.status === 'published' && overlaps(start, end, w.start_at, w.end_at),
    );
  }
  function selectable(start: string, busy: boolean) {
    return (
      editing &&
      available &&
      !busy &&
      (removing
        ? !!published(start)
        : Date.parse(start) > Date.now() && !published(start))
    );
  }
  function point(
    event: PointerEvent<HTMLButtonElement>,
    start: string,
    busy: boolean,
  ) {
    touch.current = event.pointerType !== 'mouse';
    if (touch.current || event.button !== 0 || !selectable(start, busy)) return;
    event.preventDefault();
    event.currentTarget.focus({ preventScroll: true });
    stroke.current = !selected.has(start);
    change(start, stroke.current);
  }
  function enter(
    event: PointerEvent<HTMLButtonElement>,
    start: string,
    busy: boolean,
  ) {
    if (
      event.buttons === 1 &&
      stroke.current !== null &&
      selectable(start, busy)
    )
      change(start, stroke.current);
  }
  function click(start: string, busy: boolean, detail: number) {
    if ((detail === 0 || touch.current) && selectable(start, busy))
      change(start, !selected.has(start));
  }
  const selectedWindows = selectedPublished(
    windows.data?.items || [],
    selected,
  );
  const count = removing ? selectedWindows.length : selected.size;
  function publish() {
    if (!count || !connection || !available) return;
    const starts = [...selected].sort();
    setConfirmation(
      removing
        ? {
            title: 'Убрать выбранное время',
            summary: selectedWindows.map(
              (w) =>
                `${dateLabel(w.start_at)} — ${new Date(w.end_at).toLocaleTimeString('ru-RU', { timeZone: 'Europe/Moscow', hour: '2-digit', minute: '2-digit' })}`,
            ),
            label: `Закрыть окна (${count})`,
            text: `Будет закрыто ${count} свободных окон. Занятия и подтверждённые брони сохраняются.`,
            command: {
              path: '/teacher-planning/booking-windows/close',
              action: 'windows_close',
              body: {
                connection_id: connection.connection_id,
                items: selectedWindows.map((w) => ({
                  window_id: w.window_id,
                  expected_revision: w.revision,
                })),
              },
            },
          }
        : {
            title: 'Открыть выбранное время',
            label: `Открыть окна (${count})`,
            text: `Будет открыто ${count} окон по 55 минут только на выбранной неделе.`,
            command: {
              path: '/teacher-planning/booking-windows',
              action: 'windows_publish',
              body: {
                connection_id: connection.connection_id,
                week_start: week,
                items: starts.map((start_at) => ({
                  start_at,
                  end_at: new Date(
                    Date.parse(start_at) + 55 * 60000,
                  ).toISOString(),
                })),
              },
            },
          },
    );
  }
  function clear() {
    setSelected(new Set());
    setMessage('');
    stroke.current = null;
  }
  function cancel() {
    setEditing(false);
    setSelected(new Set());
    setMessage('');
    stroke.current = null;
  }
  return {
    now,
    reload: async () => {
      await client.invalidateQueries({ queryKey: ['student-read'] });
    },
    capabilities,
    windows,
    connection,
    source,
    setSource,
    editing,
    setEditing,
    removing,
    setRemoving,
    selectedWindows,
    count,
    selected,
    published,
    available,
    selectable,
    point,
    enter,
    click,
    publish,
    cancel,
    clear,
    message,
    confirmation,
    setConfirmation,
    saved: () => {
      setConfirmation(null);
      setSelected(new Set());
      setMessage('Время обновлено. Открытые окна отмечены в календаре.');
      void client.invalidateQueries({ queryKey: ['student-read'] });
    },
  };
}
export type Availability = ReturnType<typeof useAvailability>;
export function AvailabilityToolbar({
  state,
  onStart,
}: {
  state: Availability;
  onStart: (removing: boolean) => void;
}) {
  if (!state.capabilities.data?.items.length) return null;
  return (
    <section className={styles.toolbar} aria-label="Время для записи">
      {(!state.capabilities.data.enabled || !state.connection?.enabled) && (
        <p>
          Запись через VK отключена. Сохранённые окна и брони доступны для
          просмотра.
        </p>
      )}
      {!state.editing ? (
        <div className={styles.controls}>
          <span className={styles.controlsLabel}>Время для записи</span>
          <Group gap={6} wrap="nowrap">
            <Button
              variant="default"
              className={styles.compactButton}
              aria-label="Открыть время для записи"
              disabled={!state.available}
              onClick={() => {
                state.setRemoving(false);
                onStart(false);
              }}
            >
              Открыть
            </Button>
            <Button
              variant="default"
              className={styles.compactButton}
              aria-label="Убрать время для записи"
              disabled={
                !state.available ||
                !state.windows.data?.items.some((w) => w.status === 'published')
              }
              onClick={() => {
                state.setRemoving(true);
                onStart(true);
              }}
            >
              Убрать
            </Button>
          </Group>
          <span className={styles.legend}>Открыто для записи</span>
        </div>
      ) : (
        <>
          <p>
            {state.removing
              ? 'Выберите открытые ячейки, которые хотите убрать: нажимайте или ведите мышью с зажатой кнопкой. Занятия и брони сохраняются.'
              : 'Выберите свободные часы: нажимайте или ведите мышью с зажатой кнопкой. На телефоне — нажимайте по одному. Занятия остаются на месте.'}
          </p>
          {state.capabilities.data.items.length > 1 && (
            <SelectField
              label="Источник записи"
              disabled={state.selected.size > 0}
              value={state.connection?.connection_id || null}
              data={state.capabilities.data.items.map((c) => ({
                value: c.connection_id,
                label: c.label,
              }))}
              onChange={(v) => {
                state.setSource(v);
                state.clear();
              }}
            />
          )}
          <Group>
            <Button
              disabled={!state.count || !state.available}
              onClick={state.publish}
            >
              {state.removing ? 'Убрать выбранные' : 'Открыть выбранные'} (
              {state.count})
            </Button>
            <Button
              variant="default"
              onClick={state.clear}
              disabled={!state.selected.size}
            >
              Снять выделение
            </Button>
            <Button variant="subtle" onClick={state.cancel}>
              Отмена
            </Button>
          </Group>
        </>
      )}
      {state.windows.isFetching && (
        <p role="status">Обновляем открытое время…</p>
      )}
      {state.windows.isError && (
        <p role="alert">
          Не удалось загрузить окна.{' '}
          <Button
            variant="default"
            onClick={() => void state.windows.refetch()}
          >
            Повторить
          </Button>
        </p>
      )}
      {state.windows.data?.next_cursor && (
        <p role="alert">
          Слишком много окон для отображения недели. Управление временно
          недоступно.
        </p>
      )}
      {state.message && <p role="status">{state.message}</p>}
      {state.selected.size > 0 && !state.confirmation && (
        <DirtyFormGuard
          dirty
          allowQueryKeys={['day']}
          description="Выбранные часы ещё не открыты для записи. При уходе выделение потеряется. «Отмена» вернёт к работе."
        />
      )}
      {state.confirmation && (
        <OperationDialog
          {...state.confirmation}
          onReload={state.reload}
          onClose={() => state.setConfirmation(null)}
          onSuccess={state.saved}
        >
          <p>{state.confirmation.text}</p>
          {state.confirmation.summary && (
            <ul>
              {state.confirmation.summary.map((text) => (
                <li key={text}>{text}</li>
              ))}
            </ul>
          )}
          {state.confirmation.command.action === 'windows_publish' && (
            <ul>
              {[...state.selected].sort().map((s) => (
                <li key={s}>{dateLabel(s)}</li>
              ))}
            </ul>
          )}
        </OperationDialog>
      )}
    </section>
  );
}
export function AvailabilityCell({
  state,
  start,
  busy,
}: {
  state: Availability;
  start: string;
  busy: boolean;
}) {
  const open = state.published(start);
  const chosen = state.selected.has(start);
  if (
    busy ||
    (!state.editing && !open) ||
    (state.editing && state.removing && !open)
  )
    return null;
  if (!state.editing || (!state.removing && !!open))
    return (
      <span
        className={styles.openRead}
        aria-label={`${dateLabel(start)} · открыто для записи`}
      >
        Открыто для записи
      </span>
    );
  const time = new Date(start).toLocaleTimeString('ru-RU', {
    timeZone: 'Europe/Moscow',
    hour: '2-digit',
    minute: '2-digit',
  });
  const stateText = state.removing
    ? chosen
      ? 'Будет закрыто'
      : 'Убрать время'
    : chosen
      ? 'Выбрано'
      : 'Выбрать';
  const disabled =
    !state.available || (!state.removing && Date.parse(start) <= state.now);
  return (
    <button
      type="button"
      className={styles.cell}
      data-open={!!open}
      data-selected={chosen}
      disabled={disabled}
      data-start={start}
      aria-pressed={chosen}
      aria-label={`${time} ${stateText} · ${dateLabel(start)}${open ? ' · закрыть окно' : ''}`}
      onPointerDown={(e) => state.point(e, start, busy)}
      onPointerEnter={(e) => state.enter(e, start, busy)}
      onClick={(e) => state.click(start, busy, e.detail)}
    >
      <span>
        {new Date(start).toLocaleTimeString('ru-RU', {
          timeZone: 'Europe/Moscow',
          hour: '2-digit',
          minute: '2-digit',
        })}
      </span>{' '}
      <span>{stateText}</span>
    </button>
  );
}
