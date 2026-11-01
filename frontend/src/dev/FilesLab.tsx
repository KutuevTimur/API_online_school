import { useSearchParams } from 'react-router';
import { usePageTitle } from '../app/router';
import {
  useCallback,
  useEffect,
  useState,
  useSyncExternalStore,
  useContext,
} from 'react';
import { Button, Group } from '@mantine/core';
import { session, useSession } from '../features/auth/session';
import { ReauthOverlay } from '../features/auth/ReauthOverlay';
import { AppShell } from '../shared/ui/AppShell';
import { UploadQueue } from '../shared/ui/UploadQueue';
import { FilePreview } from '../shared/ui/FilePreview';
import { DirtyFormGuard } from '../shared/ui/DirtyFormGuard';
import { FileRecoveryExamples } from './FileRecoveryExamples';
import { DraftContext } from '../app/DraftProvider';
import { UploadQueueModel } from '../shared/lib/uploadQueue';
import { LinkButton } from '../shared/ui/LinkButton';
import { request } from '../shared/api/client';
import {
  answerAdapter,
  type Answer,
  type FileDescriptor,
} from '../shared/api/files';
import type { components } from '../shared/api/schema';
import styles from '../shared/ui/ui.module.css';
type Homework = components['schemas']['HomeworkResponseDTO'];
export function FilesLab() {
  usePageTitle('Файлы · техническая галерея');
  const auth = useSession();
  const [params, setParams] = useSearchParams();
  const [answer, setAnswer] = useState<Answer>();
  const [readOnly, setReadOnly] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<{
    files: FileDescriptor[];
    index: number;
  }>();
  const close = useCallback(() => {
    setPreview(undefined);
    setParams(
      (value) => {
        const next = new URLSearchParams(value);
        next.delete('file');
        return next;
      },
      { replace: true },
    );
  }, [setParams]);
  useEffect(() => {
    if (auth.status === 'boot') void session.refresh().catch(() => {});
    return session.cleanup(() => {
      setAnswer(undefined);
      setPreview(undefined);
    });
  }, [auth.status]);
  async function load() {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      const page = await request<{ items: Homework[] }>('/homeworks/my/page');
      const homework = page.items.find(
        (item) => item.title === 'Synthetic файлы T14f',
      );
      if (!homework?.working_submission_id)
        throw new Error(
          'Войдите synthetic учеником из локального файла доступа.',
        );
      setReadOnly(!homework.can_submit);
      setAnswer(
        await request<Answer>(
          `/submissions/${homework.working_submission_id}`,
          { params: { homework_id: homework.id } },
        ),
      );
    } catch {
      setError(
        'Не удалось открыть synthetic ответ. Войдите synthetic учеником и повторите.',
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <AppShell role={auth.user?.role} preview>
      <section className={styles.panel}>
        <h1>Файлы · техническая галерея</h1>
        <p>
          Только искусственные материалы. Загрузка ниже обращается к настоящему
          защищённому API тестового окружения. Учебный кабинет ещё не подключён.
        </p>
        <Group>
          <LinkButton to="/__ui" variant="default">
            К примеру кабинета
          </LinkButton>
          <LinkButton to="/login" variant="default">
            Войти
          </LinkButton>
          <Button
            onClick={() => void load()}
            loading={busy}
            disabled={!auth.user || busy}
          >
            Открыть тестовые файлы
          </Button>
        </Group>
        {error && <p role="alert">{error}</p>}
        {answer && (
          <LiveFiles
            key={`${auth.user?.id}:${answer.id}`}
            answer={answer}
            readOnly={readOnly}
            onPreview={(files, index) => {
              setPreview({ files, index });
              setParams({ file: String(files[index].id) });
            }}
          />
        )}
        <FileRecoveryExamples />
      </section>
      <FilePreview
        files={params.has('file') ? preview?.files || [] : []}
        index={preview?.index || 0}
        onIndexChange={(index) =>
          setPreview((value) => (value ? { ...value, index } : undefined))
        }
        onClose={close}
      />
      <ReauthOverlay />
    </AppShell>
  );
}
function LiveFiles({
  answer,
  readOnly,
  onPreview,
}: {
  answer: Answer;
  readOnly: boolean;
  onPreview: (files: FileDescriptor[], index: number) => void;
}) {
  const drafts = useContext(DraftContext);
  const key = `files:${answer.id}`;
  const [adapter] = useState(() =>
    answerAdapter(answer.homework_id, answer.id),
  );
  const [model] = useState(() => {
    const existing = drafts.get(key);
    if (existing instanceof UploadQueueModel) return existing;
    const model = new UploadQueueModel(answer, adapter);
    drafts.set(key, model);
    return model;
  });
  const state = useSyncExternalStore(model.subscribe, model.snapshot);
  return (
    <>
      <DirtyFormGuard
        allowPreviewQuery
        dirty={state.items.some((item) => !!item.file)}
        onDiscard={() => {
          model.dispose();
          drafts.delete(key);
        }}
      />
      <UploadQueue
        draftKey={key}
        initial={answer}
        adapter={adapter}
        readOnly={readOnly}
        onPreview={onPreview}
      />
    </>
  );
}
