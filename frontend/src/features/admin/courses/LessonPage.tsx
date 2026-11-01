import { useState } from 'react';
import { Link, useParams } from 'react-router';
import { Button } from '@mantine/core';
import { usePageTitle } from '../../../app/router';
import {
  type Lesson,
  type Recipient,
  type Page,
  type Homework,
  type Lecture,
  useRead,
} from '../../courses/queries';
import {
  Pages,
  ReadFiles,
  ReadState,
  useListState,
} from '../../courses/ReadUI';
import { SelectField } from '../../../shared/ui/SelectField';
import { answerFiles, type Answer } from '../../../shared/api/files';
import { dateLabel, deadlineLabel } from '../../../shared/lib/datetime';
import { ReviewResult } from '../../homeworks/ReviewResult';
import { StatusBadge } from '../../../shared/ui/StatusBadge';
import { ActionDialog, useActionRecovery, type Action } from './Actions';
import styles from '../../courses/read.module.css';
import admin from '../users/users.module.css';
function HomeworkHistory({ homework }: { homework: Homework }) {
  const state = useListState(`hw${homework.id}_`);
  const answers = useRead<Page<Answer>>(
    `/homeworks/${homework.id}/submissions`,
    { limit: state.limit, offset: state.offset },
  );
  return (
    <article className={styles.panel}>
      <h3>{homework.title}</h3>
      <p className={styles.copy}>{homework.description}</p>
      <p>{deadlineLabel(homework.deadline)}</p>
      <ReadFiles condition files={homework.file ? [homework.file] : []} />
      <ReadState query={answers}>
        {(data) => (
          <>
            {!data.items.length && <p>Ответов пока нет.</p>}
            {data.items.map((a) => (
              <section key={a.id} className={styles.panel}>
                <h4>Ответ ученика</h4>
                <StatusBadge status={a.status} />
                <p className={styles.copy}>{a.text_content}</p>
                <ReadFiles files={answerFiles(a)} />
                {a.status === 'checked' && (
                  <ReviewResult answer={a} headingAs="h4" />
                )}
              </section>
            ))}
            <Pages state={state} total={data.total} />
          </>
        )}
      </ReadState>
    </article>
  );
}
function Materials({
  lesson,
  recipient,
}: {
  lesson: number;
  recipient: Recipient;
}) {
  const state = useListState('materials_');
  const params = {
    lesson_id: lesson,
    student_user_id: recipient.student_user_id,
  };
  const lectures = useRead<Page<Lecture>>('/lectures', {
    ...params,
    limit: state.limit,
    offset: state.offset,
  });
  const homeworks = useRead<Homework[]>('/homeworks', params);
  return (
    <>
      <h2>
        Материалы для {recipient.display_name} · {recipient.username}
      </h2>
      <ReadState query={lectures}>
        {(data) => (
          <>
            {!data.items.length && <p>Материалов пока нет.</p>}
            <ReadFiles
              material
              files={data.items.flatMap((l) => (l.file ? [l.file] : []))}
            />
            <Pages state={state} total={data.total} />
          </>
        )}
      </ReadState>
      <h2>Домашние задания и ответы</h2>
      <ReadState query={homeworks}>
        {(data) => (
          <>
            {!data.length && <p>Заданий пока нет.</p>}
            {data.map((h) => (
              <HomeworkHistory key={h.placement_id || h.id} homework={h} />
            ))}
          </>
        )}
      </ReadState>
    </>
  );
}
export function AdminLessonPage() {
  const { lessonId = '' } = useParams();
  const state = useListState('recipients_');
  const lesson = useRead<Lesson>(`/lessons/${encodeURIComponent(lessonId)}`);
  const recipients = useRead<Page<Recipient>>(
    `/lessons/${encodeURIComponent(lessonId)}/students`,
    { limit: state.limit, offset: state.offset },
    !!lesson.data,
  );
  const chosen = state.params.get('recipients_student') || '';
  const recipient = recipients.data?.items.find(
    (r) => String(r.student_user_id) === chosen,
  );
  const [action, setAction] = useState<Action | null>(null);
  const recovery = useActionRecovery(action);
  const [actionOpen, setActionOpen] = useState(false);
  const openAction = (next: Action) => {
    setAction(next);
    setActionOpen(true);
  };
  usePageTitle(lesson.data?.title || 'Просмотр занятия');
  return (
    <div className={admin.page}>
      <ReadState query={lesson}>
        {(l) => (
          <>
            <Link to={`/admin/courses/${l.course_id}`}>К курсу</Link>
            <h1>{l.title}</h1>
            <p>
              {dateLabel(l.scheduled_at)} ·{' '}
              {l.is_deleted ? 'Занятие в архиве' : 'Занятие не архивировано'}
            </p>
            <p className={styles.readonly}>
              Только просмотр и скачивание. Выберите получателя, чтобы открыть
              его материалы и ответы.
            </p>
            <h2>{l.topic || 'О занятии'}</h2>
            <p className={styles.copy}>{l.description}</p>
            {l.is_deleted && (
              <Button
                variant="default"
                onClick={() =>
                  openAction({
                    title: 'Восстановить занятие?',
                    label: 'Восстановить занятие',
                    description: `Занятие «${l.title}» будет снято с архива. Архив курса и границы доступа учеников не изменятся.`,
                    path: `/lessons/${l.id}/restore`,
                  })
                }
              >
                Восстановить занятие
              </Button>
            )}
            <ReadState query={recipients}>
              {(data) => (
                <>
                  {!data.items.length ? (
                    <p>Получателей на этой странице нет.</p>
                  ) : (
                    <SelectField
                      label="Получатель материалов"
                      placeholder="Выберите ученика"
                      value={recipient ? chosen : null}
                      clearable
                      data={data.items.map((r) => ({
                        value: String(r.student_user_id),
                        label: `${r.display_name} · ${r.username}`,
                      }))}
                      onChange={(student) =>
                        state.update({ student: student || '' })
                      }
                    />
                  )}
                  <Pages state={state} total={data.total} />
                  {recipient && (
                    <Materials
                      key={recipient.student_user_id}
                      lesson={l.id}
                      recipient={recipient}
                    />
                  )}
                </>
              )}
            </ReadState>
            {
              <ActionDialog
                action={action}
                opened={actionOpen}
                recovery={recovery}
                onClose={() => setActionOpen(false)}
                refresh={async () => {
                  const result = await lesson.refetch();
                  if (result.isError) throw result.error;
                }}
              />
            }
          </>
        )}
      </ReadState>
    </div>
  );
}
