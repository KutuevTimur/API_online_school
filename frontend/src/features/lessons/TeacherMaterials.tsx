import { Link } from 'react-router';
import { PlainTextLinks } from '../../shared/ui/PlainTextLinks';
import { reviewPath } from '../review/api';
import fileStyles from '../../shared/ui/files.module.css';
import { useEffect, useState } from 'react';
import { Button, Group, Stack } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import {
  useRead,
  type Page,
  type Lecture,
  type Homework,
} from '../courses/queries';
import { ReadState, ReadFiles, Pages, useListState } from '../courses/ReadUI';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import { acceptedFiles, validateSelection } from '../../shared/api/files';
import { MaterialUploadQueue } from '../../shared/ui/MaterialUploadQueue';
import { FormField, TextAreaField } from '../../shared/ui/FormField';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { deadlineLabel } from '../../shared/lib/datetime';
import { planningRefresh, type Reminder } from '../schedule/planning';
import styles from '../courses/read.module.css';
export function TeacherMaterials({
  lessonId,
  studentId,
  readOnly,
  onDirtyChange,
}: {
  lessonId: number;
  studentId: number;
  readOnly: boolean;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const client = useQueryClient();
  const state = useListState('material-');
  const debtState = useListState('debt-');
  const params = { lesson_id: lessonId, student_user_id: studentId };
  const lectures = useRead<Page<Lecture>>('/lectures', {
    ...params,
    limit: state.limit,
    offset: state.offset,
  });
  const homeworks = useRead<Homework[]>('/homeworks', params);
  const reminder = useRead<Page<Reminder>>('/teacher-planning/reminders', {
    ...params,
    only_missing: 'false',
  });
  const [debt, setDebt] = useState(false);
  const [issuing, setIssuing] = useState(false);
  const [closingIssue, setClosingIssue] = useState(false);
  const candidates = useRead<Page<Homework>>(
    '/homeworks/available-debts',
    { ...params, limit: debtState.limit, offset: debtState.offset },
    debt && !readOnly,
  );
  const [queueDirty, setQueueDirty] = useState(false);
  const [lecturePickerTarget, setLecturePickerTarget] =
    useState<HTMLDivElement | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [unknown, setUnknown] = useState(false);
  const [remove, setRemove] = useState<{ path: string; title: string } | null>(
    null,
  );
  async function refresh() {
    await client.invalidateQueries(planningRefresh);
    const result = await Promise.all([
      lectures.refetch(),
      homeworks.refetch(),
      reminder.refetch(),
    ]);
    if (result.some((r) => r.isError)) throw new Error('read failed');
  }
  async function mutate(path: string, method: string, body?: unknown) {
    if (pending || unknown) return;
    busy(true);
    setError('');
    try {
      await request(path, {
        method,
        body,
        params: method === 'DELETE' ? params : undefined,
      });
      setRemove(null);
      setNotice('Сохранено');
      await refresh().catch(() =>
        setError(
          'Сохранено, но список материалов пока не обновился. Повторите обновление.',
        ),
      );
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 409
          ? 'У задания уже есть ответ. Удалить его нельзя.'
          : e instanceof ApiError
            ? e.message
            : 'Не удалось сохранить',
      );
      setUnknown(true);
    } finally {
      busy(false);
    }
  }
  const toggleNotNeeded = (kind: 'lecture' | 'homework', value: boolean) =>
    void mutate(
      `/teacher-planning/lessons/${lessonId}/students/${studentId}`,
      'PATCH',
      kind === 'lecture'
        ? { lecture_not_needed: value }
        : { homework_not_needed: value },
    );
  const materialTone = (kind: 'lecture' | 'homework') => {
    const content = kind === 'lecture' ? lectures : homeworks;
    if (
      readOnly ||
      pending ||
      unknown ||
      (kind === 'lecture' && queueDirty) ||
      reminder.isPending ||
      reminder.isError ||
      content.isPending ||
      content.isError
    )
      return undefined;
    const current = reminder.data?.items[0];
    if (!current) return undefined;
    const notNeeded =
      kind === 'lecture'
        ? current.lecture_not_needed
        : current.homework_not_needed;
    const has = kind === 'lecture' ? current.has_lecture : current.has_homework;
    return notNeeded ? undefined : has ? 'ready' : 'missing';
  };
  const dirty = !!(title || description || file) || queueDirty;
  useEffect(
    () => onDirtyChange(dirty || pending || unknown),
    [dirty, pending, unknown, onDirtyChange],
  );
  return (
    <>
      {(dirty || pending || unknown) && (
        <DirtyFormGuard dirty allowPreviewQuery />
      )}
      <section
        aria-label="Конспекты"
        className={`${styles.panel} ${styles.materialPanel}`}
        data-material-state={materialTone('lecture')}
      >
        <div className={`${styles.sectionHeading} ${styles.materialHeading}`}>
          <h2>Конспекты</h2>
          {!readOnly && (
            <Group gap="sm" className={styles.materialActions}>
              <div
                ref={setLecturePickerTarget}
                className={styles.materialPicker}
              />
              <MaterialState
                part="action"
                kind="lecture"
                query={reminder}
                readOnly={readOnly}
                disabled={pending || unknown || queueDirty}
                onToggle={(value) => toggleNotNeeded('lecture', value)}
              />
            </Group>
          )}
        </div>
        <MaterialState
          kind="lecture"
          query={reminder}
          readOnly={readOnly}
          disabled={pending || unknown}
          onToggle={(value) => toggleNotNeeded('lecture', value)}
        />
        <ReadState query={lectures}>
          {(data) => (
            <>
              {!data.total && <p>Конспектов пока нет.</p>}
              {data.items.map((l) => (
                <article className={styles.row} key={l.id}>
                  <ReadFiles files={l.file ? [l.file] : []} />
                  <p className={styles.savedMaterial}>
                    Загружен · доступен ученику
                  </p>
                  {!readOnly && (
                    <Button
                      className={`${styles.action} ${styles.materialRemove}`}
                      variant="default"
                      disabled={pending || unknown}
                      onClick={() =>
                        setRemove({
                          path: `/lectures/${l.id}`,
                          title: l.file?.display_name || 'Конспект',
                        })
                      }
                    >
                      Удалить конспект
                    </Button>
                  )}
                </article>
              ))}
              <Pages
                label="Страницы конспектов занятия"
                state={state}
                total={data.total}
              />
            </>
          )}
        </ReadState>
        {!readOnly && (
          <MaterialUploadQueue
            pickerLabel="Добавить конспект"
            pickerTarget={lecturePickerTarget}
            key={studentId}
            existingCount={lectures.data?.total || 0}
            lessonId={lessonId}
            studentId={studentId}
            refresh={refresh}
            onDirtyChange={setQueueDirty}
          />
        )}
      </section>
      <section
        aria-label="Домашние задания"
        className={`${styles.panel} ${styles.materialPanel}`}
        data-material-state={materialTone('homework')}
      >
        <div className={`${styles.sectionHeading} ${styles.materialHeading}`}>
          <h2>Домашние задания</h2>
          {!readOnly && (
            <Group gap="sm" className={styles.materialActions}>
              <Button
                className={styles.action}
                variant={issuing ? 'default' : 'filled'}
                aria-expanded={issuing}
                aria-controls="issue-homework"
                onClick={() => {
                  if (
                    issuing &&
                    (title || description || file || pending || unknown)
                  )
                    setClosingIssue(true);
                  else setIssuing(!issuing);
                }}
              >
                {issuing ? 'Свернуть выдачу задания' : 'Выдать задание'}
              </Button>
              <MaterialState
                part="action"
                kind="homework"
                query={reminder}
                readOnly={readOnly}
                disabled={pending || unknown}
                onToggle={(value) => toggleNotNeeded('homework', value)}
              />
              <Button
                className={styles.action}
                variant="default"
                aria-expanded={debt}
                onClick={() => setDebt(!debt)}
              >
                Добавить долг
              </Button>
            </Group>
          )}
        </div>
        <MaterialState
          kind="homework"
          query={reminder}
          readOnly={readOnly}
          disabled={pending || unknown}
          onToggle={(value) => toggleNotNeeded('homework', value)}
        />
        <ReadState query={homeworks}>
          {(items) => (
            <>
              {!items.length && <p>Заданий пока нет.</p>}
              {items.map((h) => (
                <article className={styles.row} key={h.placement_id || h.id}>
                  <h3>{h.title}</h3>
                  <p className={`${styles.copy} ${styles.lessonCopy}`}>
                    <PlainTextLinks text={h.description} />
                  </p>
                  <ReadFiles files={h.file ? [h.file] : []} />
                  <p className={styles.muted}>
                    {h.placement_kind === 'debt' ? 'Долг · ' : ''}
                    {deadlineLabel(h.deadline)}
                  </p>
                  <div
                    className={styles.homeworkResponse}
                    data-response-state={h.submission_status}
                  >
                    <p>
                      {h.submission_status === 'checked'
                        ? 'Работа проверена'
                        : h.submission_status === 'submitted'
                          ? 'Ответ получен · нужно проверить'
                          : h.submission_status === 'draft'
                            ? 'Ответ ещё не отправлен · у ученика черновик'
                            : 'Ждём ответ ученика'}
                    </p>
                    {h.working_submission_id &&
                      (h.submission_status === 'submitted' ||
                        h.submission_status === 'checked') && (
                        <Button
                          component={Link}
                          className={`${styles.action} ${h.submission_status === 'submitted' ? styles.reviewPendingAction : styles.reviewCheckedAction}`}
                          variant={
                            h.submission_status === 'checked'
                              ? 'default'
                              : 'filled'
                          }
                          to={reviewPath({
                            id: h.working_submission_id,
                            homework_id: h.id,
                          })}
                        >
                          {h.submission_status === 'checked'
                            ? 'Посмотреть проверку'
                            : 'Проверить работу'}
                        </Button>
                      )}
                  </div>
                  {!readOnly && (
                    <Button
                      className={`${styles.action} ${styles.materialRemove}`}
                      variant="default"
                      disabled={pending || unknown}
                      onClick={() =>
                        setRemove({
                          path: `/homeworks/${h.id}`,
                          title: h.title,
                        })
                      }
                    >
                      Удалить задание
                    </Button>
                  )}
                </article>
              ))}
            </>
          )}
        </ReadState>
        {!readOnly && (
          <>
            <form
              id="issue-homework"
              hidden={!issuing}
              noValidate
              onSubmit={(e) => {
                e.preventDefault();
                if (pending || unknown) return;
                if (!title.trim()) {
                  setError('Укажите название задания');
                  return;
                }
                busy(true);
                setError('');
                const body = new FormData();
                body.append('lesson_id', String(lessonId));
                body.append('student_user_id', String(studentId));
                body.append('title', title);
                body.append('description', description);
                if (file) body.append('file', file);
                void request('/homeworks', { method: 'POST', body })
                  .then(async () => {
                    setTitle('');
                    setDescription('');
                    setFile(null);
                    setNotice('Задание выдано');
                    await refresh().catch(() =>
                      setError(
                        'Задание выдано, но список пока не обновился. Повторите обновление.',
                      ),
                    );
                  })
                  .catch(() => {
                    setError(
                      'Не удалось подтвердить выдачу. Текст сохранён. Проверьте задания перед повтором.',
                    );
                    setUnknown(true);
                  })
                  .finally(() => busy(false));
              }}
            >
              <Stack>
                <h3>Выдать задание</h3>
                <FormField
                  label="Название задания"
                  value={title}
                  error={!title.trim() && error ? error : undefined}
                  onChange={(e) => setTitle(e.currentTarget.value)}
                  maxLength={1000}
                />
                <TextAreaField
                  label="Условие"
                  value={description}
                  onChange={(e) => setDescription(e.currentTarget.value)}
                />
                <label className={fileStyles.picker}>
                  Добавить файл
                  <input
                    type="file"
                    accept={acceptedFiles}
                    onChange={(e) => {
                      const selected = e.currentTarget.files?.[0];
                      if (selected) {
                        const invalid = validateSelection(selected, 0, 0);
                        if (invalid) {
                          setError(invalid);
                          e.currentTarget.value = '';
                          return;
                        }
                        setFile(selected);
                        e.currentTarget.value = '';
                      }
                    }}
                  />
                </label>
                {file && (
                  <p>
                    {file.name}{' '}
                    <Button variant="subtle" onClick={() => setFile(null)}>
                      Убрать файл условия
                    </Button>
                  </p>
                )}
                <p>
                  Срок — до следующего занятия. Если его пока нет, срок будет
                  назначен позже.
                </p>
                <Button type="submit" loading={pending} disabled={unknown}>
                  Выдать задание
                </Button>
              </Stack>
            </form>
            {debt && (
              <ReadState query={candidates}>
                {(data) => (
                  <>
                    {!data.total && (
                      <p>Нет доступных работ для переноса долга.</p>
                    )}
                    {data.items.map((h) => (
                      <article key={h.id}>
                        <h3>{h.title}</h3>
                        <p>
                          {h.submission_status === 'submitted'
                            ? 'На проверке'
                            : deadlineLabel(h.deadline)}
                        </p>
                        <Button
                          className={styles.action}
                          disabled={pending || unknown}
                          onClick={() =>
                            void mutate(`/homeworks/${h.id}/debts`, 'POST', {
                              lesson_id: lessonId,
                            })
                          }
                        >
                          Добавить «{h.title}» как долг
                        </Button>
                      </article>
                    ))}
                    <Pages
                      label="Страницы доступных долгов"
                      state={debtState}
                      total={data.total}
                    />
                  </>
                )}
              </ReadState>
            )}
          </>
        )}
      </section>
      {notice && <p role="status">{notice}</p>}
      {error && <p role="alert">{error}</p>}
      {unknown && (
        <Button
          className={styles.action}
          variant="default"
          onClick={() => {
            void refresh()
              .then(() => {
                setUnknown(false);
                setRemove(null);
                setError(
                  'Состояние обновлено. Проверьте материалы перед осознанным повтором.',
                );
              })
              .catch(() =>
                setError(
                  'Не удалось проверить материалы. Повтор заблокирован.',
                ),
              );
          }}
        >
          Проверить состояние материалов
        </Button>
      )}
      <ConfirmDialog
        opened={closingIssue}
        title="Свернуть выдачу задания?"
        confirmLabel="Свернуть, сохранив ввод"
        onCancel={() => setClosingIssue(false)}
        onConfirm={() => {
          setIssuing(false);
          setClosingIssue(false);
        }}
      >
        <p>
          Текст и выбранный файл останутся в форме. Чтобы продолжить, снова
          нажмите «Выдать задание».
        </p>
      </ConfirmDialog>
      <ConfirmDialog
        destructive
        opened={!!remove}
        title="Удалить материал?"
        confirmLabel="Удалить материал"
        pending={pending}
        confirmDisabled={unknown}
        error={error}
        onCancel={() => setRemove(null)}
        onConfirm={() => {
          if (remove) void mutate(remove.path, 'DELETE');
        }}
      >
        <p>
          {remove?.title}. Материал станет недоступен ученику. Напоминание
          появится снова, если не отмечено «не нужно». ДЗ с ответом удалить
          нельзя.
        </p>
      </ConfirmDialog>
    </>
  );
}

function MaterialState({
  part = 'status',
  kind,
  query,
  readOnly,
  disabled,
  onToggle,
}: {
  kind: 'lecture' | 'homework';
  part?: 'status' | 'action';
  query: ReturnType<typeof useRead<Page<Reminder>>>;
  readOnly: boolean;
  disabled: boolean;
  onToggle: (value: boolean) => void;
}) {
  if (part === 'action') {
    const r = query.data?.items[0];
    if (readOnly || !r || query.isError) return null;
    const lecture = kind === 'lecture';
    const notNeeded = lecture ? r.lecture_not_needed : r.homework_not_needed;
    return (
      <Button
        className={styles.action}
        variant="default"
        disabled={disabled}
        onClick={() => onToggle(!notNeeded)}
      >
        {notNeeded
          ? lecture
            ? 'Снова напоминать о конспекте'
            : 'Снова напоминать о ДЗ'
          : lecture
            ? 'Не добавлять конспект'
            : 'Не задавать ДЗ'}
      </Button>
    );
  }
  return (
    <ReadState query={query}>
      {(data) => {
        const r = data.items[0];
        if (!r) return null;
        const lecture = kind === 'lecture';
        const has = lecture ? r.has_lecture : r.has_homework;
        const notNeeded = lecture
          ? r.lecture_not_needed
          : r.homework_not_needed;
        return (
          <p
            className={
              notNeeded
                ? styles.muted
                : !has
                  ? styles.attention
                  : styles.savedMaterial
            }
          >
            {notNeeded
              ? lecture
                ? 'Конспект не требуется'
                : 'ДЗ не требуется'
              : has
                ? lecture
                  ? 'Конспект загружен'
                  : 'ДЗ выдано'
                : lecture
                  ? 'Нужно добавить конспект'
                  : 'Нужно выдать ДЗ'}
          </p>
        );
      }}
    </ReadState>
  );
}
