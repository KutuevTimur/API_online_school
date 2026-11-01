import {
  useContext,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from 'react';
import { useLocation } from 'react-router';
import { Button, Textarea } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { DraftContext } from '../../app/DraftProvider';
import type { Answer, FileDescriptor } from '../../shared/api/files';
import { UploadQueue } from '../../shared/ui/UploadQueue';
import { FilePreview } from '../../shared/ui/FilePreview';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { ConflictCompare } from '../../shared/ui/ConflictCompare';
import { StudentAnswerBadge } from '../../shared/ui/StatusBadge';
import { studentAnswerState } from '../../shared/lib/studentAnswerState';
import { ReviewResult } from './ReviewResult';
import { AnswerDraft } from './answerDraft';
import { adapter } from './api';
import { readKey } from '../courses/queries';
import styles from '../courses/read.module.css';
import answerStyles from './answer.module.css';
export function AnswerForm({
  homeworkId,
  initial,
  readOnly,
  loadError = false,
}: {
  homeworkId: number;
  initial: Answer;
  readOnly: boolean;
  loadError?: boolean;
}) {
  const { hash } = useLocation();
  const resultRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (hash === '#result' && initial.status === 'checked') {
      resultRef.current?.focus();
      resultRef.current?.scrollIntoView({ block: 'start' });
    }
  }, [hash, initial.status]);
  const drafts = useContext(DraftContext);
  const key = `homework-answer:${homeworkId}`;
  const [model] = useState(() => {
    const old = drafts.get(key);
    if (old instanceof AnswerDraft) return old;
    const next = new AnswerDraft(homeworkId, initial);
    drafts.set(key, next);
    return next;
  });
  const textRef = useRef<HTMLTextAreaElement>(null);
  const state = useSyncExternalStore(model.subscribe, model.snapshot);
  const query = useQueryClient();
  useEffect(() => {
    if (model.fieldError) textRef.current?.focus();
  }, [model, state]);
  useEffect(() => {
    model.reconcile(initial);
  }, [model, initial]);
  useEffect(() => {
    if (!state.answer.id) return;
    query.setQueryData(
      readKey(`/submissions/${state.answer.id}`, { homework_id: homeworkId }),
      state.answer,
    );
    void query.invalidateQueries({
      queryKey: readKey(`/homeworks/${homeworkId}`),
    });
    void query.invalidateQueries({
      queryKey: ['student-read', '/homeworks/my/page'],
    });
    void query.invalidateQueries({
      queryKey: ['student-read', `/homeworks/${homeworkId}/submissions`],
    });
  }, [query, state.answer, homeworkId]);
  const [preview, setPreview] = useState<{
    files: FileDescriptor[];
    index: number;
  }>({ files: [], index: -1 });
  const checked =
    state.answer.status === 'checked' || initial.status === 'checked';
  const locked = readOnly || checked || loadError;
  const busy = state.busy || model.saving;
  async function save(send = false) {
    await model.save(send);
    await query.invalidateQueries();
  }
  const visualState = studentAnswerState(
    checked
      ? initial.status === 'checked'
        ? initial
        : state.answer
      : state.answer,
    {
      dirty: model.dirty,
      uncertain:
        loadError || state.needsRead || busy || (state.blocked && !checked),
      readOnly,
    },
  );
  return (
    <>
      <section
        className={`${styles.panel} ${answerStyles.form}`}
        data-state={visualState}
        aria-label="Ваше решение"
      >
        <h2>Ваше решение</h2>
        <p role="status">
          <StudentAnswerBadge state={visualState} />
        </p>
        {!checked && model.dirty && state.answer.id > 0 && (
          <p>
            Есть несохранённые изменения. Сохранённая версия решения остаётся на
            сервере.
          </p>
        )}
        <form
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            void save();
          }}
        >
          <Textarea
            label="Текст решения или вопросы"
            autosize
            minRows={3}
            ref={textRef}
            error={model.fieldError}
            value={
              checked
                ? (state.answer.status === 'checked'
                    ? state.answer.text_content
                    : initial.text_content) || ''
                : model.text
            }
            readOnly={locked}
            disabled={busy}
            className="resize-none"
            onChange={(e) => model.setText(e.currentTarget.value)}
          />
        </form>
        {state.conflict && (
          <ConflictCompare
            local={<p className={styles.copy}>{model.text || 'Без текста'}</p>}
            server={
              <p className={styles.copy}>
                {state.answer.text_content ||
                  'Перечитайте ответ, чтобы увидеть актуальную версию'}
              </p>
            }
            onReload={() => void model.read()}
          />
        )}
        <UploadQueue
          integrated
          draftKey={key}
          model={model}
          initial={initial}
          adapter={adapter(homeworkId, () => model.state.answer)}
          readOnly={locked}
          disabled={model.saving}
          onFilesSelected={() => void save()}
          onPreview={(files, index) => setPreview({ files, index })}
        />
        {!locked && (
          <>
            <p className={styles.muted}>
              {state.answer.status === 'submitted'
                ? 'Решение отправлено. До проверки можно внести изменения. Загруженные файлы сохраняются сразу.'
                : 'Загруженные файлы сохраняются сразу. Учитель получит решение после отправки.'}
            </p>
            <Button
              mt="md"
              type="button"
              onClick={() => void save(state.answer.status !== 'submitted')}
              loading={busy}
              disabled={busy || state.needsRead || state.blocked}
            >
              {state.answer.status === 'submitted'
                ? 'Сохранить изменения'
                : 'Отправить решение'}
            </Button>
          </>
        )}
        <FilePreview
          files={preview.files}
          index={preview.index}
          onIndexChange={(index) => setPreview({ ...preview, index })}
          onClose={() => setPreview({ ...preview, index: -1 })}
        />
        <DirtyFormGuard
          allowPreviewQuery
          dirty={model.dirty || busy}
          onDiscard={() => {
            model.dispose();
            drafts.delete(key);
          }}
        />
      </section>
      {checked && (
        <section
          id="result"
          ref={resultRef}
          tabIndex={-1}
          aria-label="Результат проверки"
          className={`${styles.result} ${styles.studentResult}`}
          data-state={visualState}
        >
          <ReviewResult
            answer={state.answer.status === 'checked' ? state.answer : initial}
          />
        </section>
      )}
    </>
  );
}
