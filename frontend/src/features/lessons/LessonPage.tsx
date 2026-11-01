import { useRef } from 'react';
import { PlainTextLinks } from '../../shared/ui/PlainTextLinks';
import { Video } from 'lucide-react';
import { Button } from '@mantine/core';
import { studentAnswerState } from '../../shared/lib/studentAnswerState';
import { Link, useParams } from 'react-router';
import { ReviewResult } from '../homeworks/ReviewResult';
import {
  StudentHistoryReturn,
  useStudentHistoryOrigin,
} from '../courses/studentHistoryOrigin';
import { StudentAnswerBadge } from '../../shared/ui/StatusBadge';
import { answerFiles, type Answer } from '../../shared/api/files';
import { LinkButton } from '../../shared/ui/LinkButton';
import { ExternalLinkButton } from '../../shared/ui/LinkButton';
import { usePageTitle } from '../../app/router';
import { useSession } from '../auth/session';
import {
  dateLabel,
  deadlineLabel,
  lessonStatus,
  safeCallUrl,
} from '../../shared/lib/datetime';
import {
  type Lesson,
  type Homework,
  type Lecture,
  type Page,
  type Recipient,
  useRead,
} from '../courses/queries';
import {
  ReadFiles,
  ReadOnly,
  ReadState,
  Pages,
  useListState,
} from '../courses/ReadUI';
import styles from '../courses/read.module.css';
export function CallLink({
  url,
  variant,
  audience = 'teacher',
}: {
  audience?: 'teacher' | 'student';
  url?: string | null;
  variant?: 'default';
}) {
  const safe = safeCallUrl(url);
  return safe ? (
    <ExternalLinkButton
      href={safe}
      studentAction={audience === 'student'}
      variant={variant}
      leftSection={
        audience === 'student' ? (
          <Video size={18} aria-hidden="true" />
        ) : undefined
      }
    >
      {audience === 'student' ? 'Присоединиться' : 'Открыть встречу'}
    </ExternalLinkButton>
  ) : (
    <p>Ссылка на встречу ещё не добавлена</p>
  );
}
export function HomeworkThread({
  homework: item,
  readOnly = false,
}: {
  homework: Homework;
  readOnly?: boolean;
}) {
  const origin = useStudentHistoryOrigin();
  const resultRef = useRef<HTMLElement>(null);
  const answer = useRead<Answer>(
    `/submissions/${item.working_submission_id}`,
    { homework_id: item.id },
    !!item.working_submission_id,
  );
  const readonly = readOnly || item.access_mode === 'read_only';
  const visualState = studentAnswerState(answer.data, {
    uncertain:
      !!item.working_submission_id &&
      (answer.isPending || answer.isError || answer.isFetching),
    readOnly: readonly,
  });
  const target = `/student/homeworks/${item.id}`;
  const checked = answer.data?.status === 'checked';
  return (
    <article className={styles.lessonWork}>
      <section
        className={`${styles.panel} ${styles.studentHomework}`}
        data-state={visualState}
      >
        <h3>{item.title}</h3>
        <p className={styles.copy}>
          <PlainTextLinks
            text={item.description || 'Условие в приложенном файле.'}
          />
        </p>
        <p>
          {item.placement_kind === 'debt' ? 'Долг · ' : ''}
          {deadlineLabel(item.deadline)}
        </p>
        <ReadFiles condition files={item.file ? [item.file] : []} />
        <p>
          <StudentAnswerBadge state={visualState} />
        </p>
        {answer.data?.status === 'submitted' && (
          <p>Решение отправлено. Учитель ещё не завершил проверку.</p>
        )}
        {checked ? (
          <Button
            variant="default"
            className={styles.studentWorkAction}
            onClick={() => {
              resultRef.current?.focus();
              resultRef.current?.scrollIntoView({ block: 'start' });
            }}
          >
            Посмотреть результат
          </Button>
        ) : (
          <LinkButton
            className={styles.studentWorkAction}
            to={target}
            state={origin.state}
          >
            {readonly
              ? 'Открыть домашнее задание'
              : visualState === 'submitted'
                ? 'Открыть отправленное решение'
                : visualState === 'draft'
                  ? 'Продолжить решение'
                  : visualState === 'unknown'
                    ? 'Открыть домашнее задание'
                    : 'Подготовить решение'}
          </LinkButton>
        )}
      </section>
      {!!item.working_submission_id && (
        <ReadState query={answer}>
          {(data) => (
            <>
              <section
                className={`${styles.panel} ${styles.studentHomework}`}
                data-state={visualState}
              >
                <h4>Ваше решение</h4>
                {data.text_content && (
                  <p className={styles.copy}>{data.text_content}</p>
                )}
                <ReadFiles files={answerFiles(data)} />
              </section>
              {data.status === 'checked' && (
                <section
                  data-state={visualState}
                  ref={resultRef}
                  tabIndex={-1}
                  aria-label={`Результат проверки: ${item.title}`}
                  className={`${styles.result} ${styles.studentResult}`}
                >
                  <ReviewResult answer={data} headingAs="h4" />
                </section>
              )}
            </>
          )}
        </ReadState>
      )}
    </article>
  );
}
function Materials({
  lessonId,
  recipient,
  readOnly,
}: {
  lessonId: number;
  recipient: Recipient;
  readOnly: boolean;
}) {
  const state = useListState();
  const params = {
    lesson_id: lessonId,
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
      <section
        className={`${styles.panel} ${styles.studentMaterial}`}
        data-state={
          readOnly ||
          lectures.isPending ||
          lectures.isError ||
          lectures.isFetching
            ? 'unknown'
            : lectures.data?.items.length
              ? 'available'
              : 'missing'
        }
      >
        <h2>Конспект</h2>
        <ReadState query={lectures}>
          {(data) => (
            <>
              {!data.items.length && <p>Конспект пока не добавлен.</p>}
              <ReadFiles
                material
                files={data.items.flatMap((item) =>
                  item.file ? [item.file] : [],
                )}
              />
              <Pages total={data.total} state={state} />
            </>
          )}
        </ReadState>
      </section>
      <section
        className={`${styles.panel} ${styles.studentHomeworkList}`}
        data-state={
          readOnly ||
          homeworks.isPending ||
          homeworks.isError ||
          homeworks.isFetching
            ? 'unknown'
            : homeworks.data?.length
              ? 'available'
              : 'missing'
        }
        aria-label="Домашние задания"
      >
        <h2>Домашние задания</h2>
        <ReadState query={homeworks}>
          {(data) => (
            <>
              {!data.length && <p>Домашних заданий пока нет.</p>}
              {data.map((item) => (
                <HomeworkThread
                  key={item.placement_id || item.id}
                  homework={item}
                  readOnly={readOnly}
                />
              ))}
            </>
          )}
        </ReadState>
      </section>
    </>
  );
}
export function LessonPage() {
  const origin = useStudentHistoryOrigin();
  const { lessonId = '' } = useParams();
  const auth = useSession();
  const lesson = useRead<Lesson>(
    `/lessons/${encodeURIComponent(lessonId)}`,
    {},
    true,
    60000,
  );
  const recipients = useRead<Page<Recipient>>(
    `/lessons/${encodeURIComponent(lessonId)}/students`,
    { limit: 20, offset: 0 },
    !!lesson.data,
  );
  usePageTitle(lesson.data?.title || 'Занятие');
  return (
    <ReadState query={lesson}>
      {(data) => (
        <>
          {origin.returnTo ? (
            <StudentHistoryReturn />
          ) : (
            <Link to={`/student/courses/${data.course_id}?view=all`}>
              К занятиям курса
            </Link>
          )}
          <header className={styles.heading}>
            <h1>{data.title}</h1>
            <p>
              {dateLabel(data.scheduled_at)} · {data.duration_minutes} мин ·{' '}
              {lessonStatus(data.status)}
            </p>
          </header>
          <ReadOnly mode={data.access_mode} reason={data.read_only_reason} />
          <section className={`${styles.lesson} ${styles.lessonIntro}`}>
            <h2>{data.topic || 'О занятии'}</h2>
            <p className={styles.copy}>{data.description}</p>
            <CallLink url={data.effective_call_url} />
          </section>
          <ReadState query={recipients}>
            {(page) => {
              const recipient = page.items.find(
                (item) => item.student_user_id === auth.user?.id,
              );
              return recipient ? (
                <Materials
                  lessonId={data.id}
                  recipient={recipient}
                  readOnly={data.access_mode === 'read_only' || lesson.isError}
                />
              ) : (
                <p role="alert">
                  Не удалось определить получателя материалов. Вернитесь в свои
                  курсы.
                </p>
              );
            }}
          </ReadState>
        </>
      )}
    </ReadState>
  );
}
