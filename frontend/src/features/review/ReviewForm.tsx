import { ConflictCompare } from '../../shared/ui/ConflictCompare';
import {
  useContext,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from 'react';
import { Button, Group, Radio } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { DraftContext } from '../../app/DraftProvider';
import type { Answer } from '../../shared/api/files';
import { answerFiles } from '../../shared/api/files';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { TextAreaField } from '../../shared/ui/FormField';
import { ReadFiles } from '../courses/ReadUI';
import { reviewAPI } from './api';
import { ReviewResult } from '../homeworks/ReviewResult';
import { acceptedFiles } from '../../shared/api/files';
import fileStyles from '../../shared/ui/files.module.css';
import { ReviewDraft } from './reviewDraft';
import styles from '../courses/read.module.css';
import layout from './review.module.css';
export function ReviewForm({
  initial,
  student,
  title,
  canReview,
}: {
  initial: Answer;
  student: string;
  title: string;
  canReview: boolean;
}) {
  const drafts = useContext(DraftContext);
  const key = `teacher-review:${initial.homework_id}:${initial.id}`;
  const [model] = useState(() => {
    const old = drafts.get(key);
    if (old instanceof ReviewDraft) return old;
    const next = new ReviewDraft(
      initial,
      reviewAPI(initial.homework_id, initial.id),
    );
    drafts.set(key, next);
    return next;
  });
  const state = useSyncExternalStore(model.subscribe, model.snapshot);
  const client = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  const [missingGrade, setMissingGrade] = useState(false);
  const firstRadio = useRef<HTMLInputElement>(null);
  useEffect(() => model.reconcile(initial), [initial, model]);
  useEffect(() => {
    if (state.answer.status === 'checked') void client.invalidateQueries();
  }, [client, state.answer]);
  const checked = state.answer.status === 'checked';
  const disabled =
    !canReview ||
    checked ||
    state.busy ||
    state.unknown ||
    !!state.latest ||
    state.blocked;
  async function save() {
    await model.check();
    setConfirm(false);
    await client.invalidateQueries();
  }
  return (
    <>
      <DirtyFormGuard
        dirty={model.dirty}
        allowPreviewQuery
        onDiscard={() => drafts.delete(key)}
      />
      <div className={layout.review}>
        <section className={styles.panel}>
          <h2>Решение ученика</h2>
          {state.latest && (
            <p role="alert">
              Ученик изменил ответ. Ниже открыта прежняя версия. Ваша оценка и
              комментарий сохранены отдельно.
            </p>
          )}
          <p className={styles.copy}>
            {state.answer.text_content || 'Ответ в приложенных файлах.'}
          </p>
          <ReadFiles embedded files={answerFiles(state.answer)} />
        </section>
        <section
          className={`${checked ? styles.result : styles.panel} ${layout.grading}`}
        >
          {checked ? (
            <ReviewResult teacher answer={state.answer} />
          ) : (
            <>
              <h2>Проверка</h2>
              <form
                noValidate
                onSubmit={(e) => {
                  e.preventDefault();
                  if (disabled) return;
                  if (state.grade === '') {
                    setMissingGrade(true);
                    firstRadio.current?.focus();
                    return;
                  }
                  setConfirm(true);
                }}
              >
                <Radio.Group
                  name="grade"
                  label="Оценка"
                  value={state.grade}
                  error={missingGrade ? 'Выберите оценку от 0 до 5' : undefined}
                  onChange={(grade) => {
                    model.edit(grade, state.comment);
                    setMissingGrade(false);
                  }}
                >
                  <div className={layout.grades}>
                    {[0, 1, 2, 3, 4, 5].map((grade) => (
                      <Radio
                        key={grade}
                        ref={grade === 0 ? firstRadio : undefined}
                        value={String(grade)}
                        label={String(grade)}
                        disabled={disabled}
                        classNames={{
                          root: layout.grade,
                          body: layout.gradeBody,
                          label: layout.gradeLabel,
                          labelWrapper: layout.gradeLabelWrapper,
                        }}
                      />
                    ))}
                  </div>
                </Radio.Group>
                <TextAreaField
                  mt="md"
                  minRows={3}
                  label="Комментарий ученику"
                  description="Необязательно"
                  value={state.comment}
                  disabled={state.busy || checked}
                  onChange={(e) =>
                    model.edit(state.grade, e.currentTarget.value)
                  }
                />
                <div className={fileStyles.queue}>
                  <p className={layout.fileHint}>
                    Файлы — необязательно. Фото или PDF · до 10 файлов по 20
                    МиБ.
                  </p>
                  <label className={fileStyles.picker}>
                    Добавить файлы к проверке
                    <input
                      type="file"
                      multiple
                      accept={acceptedFiles}
                      aria-label="Добавить файлы к проверке"
                      disabled={disabled}
                      onChange={(e) => {
                        model.attach(Array.from(e.currentTarget.files || []));
                        e.currentTarget.value = '';
                      }}
                    />
                  </label>
                  {state.files.map((file, i) => (
                    <article
                      key={`${i}:${file.name}`}
                      className={fileStyles.row}
                    >
                      <div className={fileStyles.details}>
                        <strong>{file.name}</strong>
                        <p>Отправится вместе с проверкой</p>
                        <Group>
                          <label className={fileStyles.picker}>
                            Заменить файл
                            <input
                              type="file"
                              accept={acceptedFiles}
                              aria-label={`Заменить файл проверки ${file.name}`}
                              disabled={disabled}
                              onChange={(e) => {
                                if (e.currentTarget.files?.[0])
                                  model.attach([e.currentTarget.files[0]], i);
                                e.currentTarget.value = '';
                              }}
                            />
                          </label>
                          <Button
                            variant="subtle"
                            color="var(--lgg-danger)"
                            disabled={disabled}
                            onClick={() => model.removeFile(i)}
                          >
                            Удалить файл
                          </Button>
                        </Group>
                      </div>
                    </article>
                  ))}
                </div>
                <p>
                  Оценку, комментарий и файлы после завершения изменить нельзя.
                </p>
                <Button type="submit" disabled={disabled} loading={state.busy}>
                  Завершить проверку
                </Button>
              </form>
              {!canReview && (
                <p role="status">
                  Сейчас доступен только просмотр. Проверить можно отправленный
                  ответ в активном обучении.
                </p>
              )}
              {state.latest && (
                <ConflictCompare
                  local={
                    <>
                      <p>Оценка: {state.grade || 'не выбрана'}</p>
                      <p className={styles.copy}>
                        {state.comment || 'Без комментария'}
                      </p>
                    </>
                  }
                  server={
                    <>
                      <p className={styles.copy}>
                        {state.latest.text_content || 'Ответ в файлах'}
                      </p>
                      <p>
                        Файлов: {state.latest.files.length}. После открытия
                        перечитайте решение и подтвердите оценку.
                      </p>
                    </>
                  }
                  onReload={() => model.openLatest()}
                />
              )}
              {(state.unknown || state.blocked) && (
                <Button
                  mt="md"
                  variant="default"
                  loading={state.busy}
                  onClick={async () => {
                    await model.refresh();
                    await client.invalidateQueries();
                  }}
                >
                  Проверить результат на сервере
                </Button>
              )}
              {state.error && <p role="alert">{state.error}</p>}
            </>
          )}
        </section>
      </div>
      <ConfirmDialog
        opened={confirm}
        title="Завершить проверку?"
        confirmLabel="Завершить проверку"
        pending={state.busy}
        confirmDisabled={disabled}
        onCancel={() => setConfirm(false)}
        onConfirm={() => void save()}
      >
        <p>
          {student} · {title}
        </p>
        <p>Оценка: {state.grade} из 5.</p>
        <p>Оценку и комментарий изменить нельзя. Ученик увидит результат.</p>
        {!!state.files.length && (
          <p>
            Файлов к проверке: {state.files.length}. Их тоже нельзя будет
            изменить.
          </p>
        )}
      </ConfirmDialog>
    </>
  );
}
