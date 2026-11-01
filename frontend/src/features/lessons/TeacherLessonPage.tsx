import { OverlapWarnings } from '../schedule/OverlapWarnings';
import { useState } from 'react';
import { Link, useLocation, useParams, useSearchParams } from 'react-router';
import { Button, Group } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { usePageTitle } from '../../app/router';
import {
  useRead,
  type Lesson,
  type Page,
  type Recipient,
} from '../courses/queries';
import { ReadState, ReadOnly, Pages, useListState } from '../courses/ReadUI';
import {
  dateLabel,
  lessonStatus,
  safeCallUrl,
} from '../../shared/lib/datetime';
import { request } from '../../shared/api/client';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { SelectField } from '../../shared/ui/SelectField';
import { FormField } from '../../shared/ui/FormField';
import { LessonEditor } from '../schedule/LessonEditor';
import { LessonStatusDialog } from '../schedule/LessonStatusDialog';
import { useLessonUndo } from '../schedule/useLessonUndo';
import { RegularDialog } from '../schedule/RegularDialog';
import {
  planningRefresh,
  previewRegularChange,
  type RegularOperation,
} from '../schedule/planning';
import { TeacherMaterials } from './TeacherMaterials';
import { CallLink } from './LessonPage';
import styles from '../courses/read.module.css';
export function TeacherLessonPage() {
  const { lessonId = '' } = useParams();
  const [params, setParams] = useSearchParams();
  const location = useLocation();
  const client = useQueryClient();
  const saved = useLessonUndo();
  const lesson = useRead<Lesson>(
    `/lessons/${encodeURIComponent(lessonId)}`,
    {},
    true,
    60000,
  );
  const state = useListState('recipients-');
  const recipients = useRead<Page<Recipient>>(
    `/lessons/${encodeURIComponent(lessonId)}/students`,
    { limit: state.limit, offset: state.offset },
    !!lesson.data,
  );
  const chosen =
    params.get('student') ||
    (recipients.data?.total === 1
      ? String(recipients.data.items[0]?.student_user_id)
      : '');
  const recipient = recipients.data?.items.find(
    (r) => String(r.student_user_id) === chosen,
  );
  const [materialsDirty, setMaterialsDirty] = useState(false);
  const [editing, setEditing] = useState(false);
  const [action, setAction] = useState('');
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [unknown, setUnknown] = useState(false);
  const [op, setOp] = useState<RegularOperation | null>(null);
  const [weeks, setWeeks] = useState('4');
  usePageTitle(lesson.data?.title || 'Занятие преподавателя');
  const returnTo =
    typeof location.state?.returnTo === 'string' &&
    /^\/teacher(?:\/|$)/.test(location.state.returnTo)
      ? location.state.returnTo
      : '/teacher/schedule';
  async function act(data: Lesson) {
    if (pending || unknown) return;
    busy(true);
    setError('');
    try {
      await request(`/lessons/${data.id}`, {
        method: 'DELETE',
      });
      await client.invalidateQueries(planningRefresh);
      setAction('');
    } catch {
      setUnknown(true);
      setError(
        'Не удалось подтвердить изменение. Загрузите актуальное занятие перед повтором.',
      );
    } finally {
      busy(false);
    }
  }
  async function series(
    action: 'extend' | 'stop' | 'cancel_future',
    data: Lesson,
  ) {
    if (pending) return;
    if (
      action === 'extend' &&
      (!Number.isInteger(Number(weeks)) ||
        Number(weeks) < 1 ||
        Number(weeks) > 12)
    ) {
      setError('Укажите 1–12 недель');
      return;
    }
    busy(true);
    setError('');
    try {
      setOp(await previewRegularChange(data, action, Number(weeks)));
    } catch {
      setError(
        'Предпросмотр недоступен. Обновите занятие; остановленную серию продлевать нельзя.',
      );
    } finally {
      busy(false);
    }
  }
  return (
    <ReadState query={lesson}>
      {(data) => (
        <div className={styles.pageSections}>
          <Link
            to={returnTo}
            state={{ studentListSearch: location.state?.studentListSearch }}
          >
            {returnTo.startsWith('/teacher/students/')
              ? 'К ученику'
              : returnTo.startsWith('/teacher/courses/')
                ? 'К занятиям курса'
                : returnTo.startsWith('/teacher/schedule')
                  ? 'К расписанию'
                  : 'В мой день'}
          </Link>
          <header className={styles.heading}>
            <div className={styles.lessonIdentity}>
              <h1>
                {recipient
                  ? `${recipient.display_name}${recipient.school_grade ? ` · ${recipient.school_grade} класс` : ''}`
                  : 'Занятие'}
              </h1>
              {recipient && (
                <Button
                  component={Link}
                  to={`/teacher/students/${recipient.student_user_id}`}
                  state={{
                    studentListSearch: location.state?.studentListSearch,
                  }}
                  variant="default"
                  className={styles.action}
                >
                  Перейти к ученику
                </Button>
              )}
            </div>
            <p>
              {dateLabel(data.scheduled_at)} ·{' '}
              {data.is_deleted
                ? `В архиве · ${lessonStatus(data.status)}`
                : lessonStatus(data.status)}
            </p>
          </header>
          <ReadOnly mode={data.access_mode} reason={data.read_only_reason} />
          <p className={styles.lessonTopic}>
            {[
              data.title !== 'Занятие' ? data.title : '',
              data.topic !== data.title ? data.topic : '',
            ]
              .filter(Boolean)
              .join(' · ')}
          </p>
          {safeCallUrl(data.effective_call_url) && (
            <CallLink url={data.effective_call_url} />
          )}
          {location.state?.savedWarnings?.length > 0 && (
            <OverlapWarnings warnings={location.state.savedWarnings} />
          )}
          <ReadState query={recipients}>
            {(page) => (
              <>
                {page.total !== 1 && (
                  <SelectField
                    disabled={materialsDirty}
                    label="Ученик — получатель материалов"
                    value={chosen || null}
                    data={page.items.map((r) => ({
                      value: String(r.student_user_id),
                      label: r.display_name,
                    }))}
                    onChange={(v) => {
                      const p = new URLSearchParams(params);
                      p.set('student', v || '');
                      setParams(p, { state: location.state });
                    }}
                  />
                )}
                {page.total > state.limit && (
                  <Pages
                    label="Страницы получателей занятия"
                    total={page.total}
                    state={state}
                  />
                )}
                {recipient ? (
                  <TeacherMaterials
                    key={recipient.student_user_id}
                    lessonId={data.id}
                    studentId={recipient.student_user_id}
                    readOnly={!data.can_manage}
                    onDirtyChange={setMaterialsDirty}
                  />
                ) : (
                  <p>
                    Выберите получателя. Если участник недоступен, откройте курс
                    и проверьте обучение.
                  </p>
                )}
              </>
            )}
          </ReadState>
          {data.can_manage && (
            <section className={styles.panel} aria-label="Управление занятием">
              <h2>Управление занятием</h2>
              <Group>
                {data.status === 'cancelled' && (
                  <Button
                    disabled={materialsDirty}
                    onClick={() => setAction('scheduled')}
                  >
                    Восстановить занятие
                  </Button>
                )}
                <Button
                  className={styles.action}
                  disabled={materialsDirty}
                  onClick={() => setEditing(true)}
                >
                  Перенести
                </Button>
                <Button
                  className={`${styles.action} ${styles.lessonComplete}`}
                  variant="default"
                  disabled={materialsDirty}
                  onClick={() => setAction('completed')}
                >
                  Отметить завершённым
                </Button>
                <Button
                  className={`${styles.action} ${styles.materialRemove}`}
                  variant="default"
                  disabled={materialsDirty}
                  onClick={() => setAction('cancelled')}
                >
                  Отменить занятие
                </Button>
              </Group>
            </section>
          )}
          <details className={`${styles.panel} ${styles.secondaryDisclosure}`}>
            <summary>Управление встречей и обучением</summary>
            <Group>
              <Link to={`/teacher/courses/${data.course_id}`}>
                К занятиям курса
              </Link>
            </Group>
            {!safeCallUrl(data.effective_call_url) && (
              <p>Ссылка на встречу ещё не добавлена</p>
            )}
            {data.can_manage && (
              <Group mt="md">
                <Button
                  variant="default"
                  disabled={materialsDirty}
                  onClick={() => setAction('archive')}
                >
                  В архив
                </Button>
              </Group>
            )}
            {data.regular_series_id && data.can_manage && (
              <details
                className={`${styles.row} ${styles.secondaryDisclosure}`}
              >
                <summary>Регулярное время</summary>
                <p>
                  Перенос и отмена меняют только эту встречу. Продление идёт от
                  прежней границы серии.
                </p>
                <FormField
                  label="Добавить недель, 1–12"
                  value={weeks}
                  onChange={(e) => setWeeks(e.currentTarget.value)}
                />
                <Group mt="md">
                  <Button
                    disabled={pending || materialsDirty}
                    onClick={() => void series('extend', data)}
                  >
                    Предпросмотр продления
                  </Button>
                  <Button
                    variant="default"
                    disabled={pending || materialsDirty}
                    onClick={() => void series('stop', data)}
                  >
                    Остановить серию
                  </Button>
                  <Button
                    variant="default"
                    disabled={pending || materialsDirty}
                    onClick={() => void series('cancel_future', data)}
                  >
                    Отменить будущие встречи серии
                  </Button>
                </Group>
              </details>
            )}
            {error && <p role="alert">{error}</p>}
            {unknown && (
              <Button
                variant="default"
                onClick={() =>
                  void lesson.refetch().then((r) => {
                    if (!r.isError) {
                      setUnknown(false);
                      setAction('');
                      setError(
                        'Актуальное занятие загружено. Проверьте результат.',
                      );
                    }
                  })
                }
              >
                Загрузить актуальное занятие
              </Button>
            )}
          </details>
          {editing && (
            <LessonEditor
              lesson={data}
              initial={data.scheduled_at}
              onClose={() => setEditing(false)}
            />
          )}
          {(action === 'cancelled' ||
            action === 'completed' ||
            action === 'scheduled') && (
            <LessonStatusDialog
              lesson={data}
              status={action}
              onClose={() => setAction('')}
              onSaved={action === 'cancelled' ? saved : undefined}
            />
          )}
          <ConfirmDialog
            opened={action === 'archive'}
            title={
              action === 'archive'
                ? 'В архив занятие?'
                : action === 'cancelled'
                  ? 'Отменить занятие?'
                  : 'Завершить занятие?'
            }
            confirmLabel={
              action === 'archive'
                ? 'Архивировать'
                : action === 'cancelled'
                  ? 'Отменить занятие'
                  : 'Завершить'
            }
            pending={pending}
            error={error}
            confirmDisabled={unknown}
            onCancel={() => setAction('')}
            onConfirm={() => void act(data)}
          >
            <p>
              {data.title} · {dateLabel(data.scheduled_at)}. Материалы
              сохранятся. Сроки ДЗ будут пересчитаны до следующего активного
              занятия. Архив доступен только для чтения.
            </p>
          </ConfirmDialog>
          {op && (
            <RegularDialog
              operation={op}
              onClose={() => setOp(null)}
              onSaved={() => {
                setOp(null);
                void client.invalidateQueries(planningRefresh);
              }}
            />
          )}
        </div>
      )}
    </ReadState>
  );
}
