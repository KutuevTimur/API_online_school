import { Link, useParams } from 'react-router';
import { usePageTitle } from '../../app/router';
import type { Answer } from '../../shared/api/files';
import { deadlineLabel } from '../../shared/lib/datetime';
import {
  type Homework,
  type Lecture,
  type Page,
  useRead,
} from '../courses/queries';
import { useSession } from '../auth/session';
import { ReadFiles, ReadOnly, ReadState } from '../courses/ReadUI';
import { PlainTextLinks } from '../../shared/ui/PlainTextLinks';
import layout from './homework.module.css';
import { AnswerForm } from './AnswerForm';
import {
  StudentHistoryReturn,
  useStudentHistoryOrigin,
} from '../courses/studentHistoryOrigin';
import { SubmissionHistory, DeadlineHistory } from './SubmissionHistory';
import styles from '../courses/read.module.css';
const emptyAnswer = (id: number): Answer => ({
  id: 0,
  homework_id: id,
  attempt_number: 1,
  version: 1,
  is_working: true,
  status: 'draft',
  text_content: null,
  files: [],
  review_files: [],
  grade: null,
  teacher_comment: null,
  submitted_at: null,
  checked_at: null,
  checked_by: null,
  created_at: '',
  updated_at: '',
});
function LessonMaterials({ lessonId }: { lessonId: number }) {
  const auth = useSession();
  const query = useRead<Page<Lecture>>(
    '/lectures',
    {
      lesson_id: lessonId,
      student_user_id: auth.user?.id,
      limit: 20,
      offset: 0,
    },
    !!auth.user,
  );
  return (
    <section className={styles.panel}>
      <h2>Конспект занятия</h2>
      <ReadState query={query}>
        {(data) => (
          <>
            {!data.items.length && <p>Материалы пока не добавлены.</p>}
            <ReadFiles
              material
              studyLabel="конспект"
              initiallyCollapsed
              files={data.items.flatMap((item) =>
                item.file ? [item.file] : [],
              )}
            />
          </>
        )}
      </ReadState>
    </section>
  );
}
function WorkingAnswer({ homework }: { homework: Homework }) {
  const working = useRead<Answer>(
    `/submissions/${homework.working_submission_id}`,
    { homework_id: homework.id },
    !!homework.working_submission_id,
  );
  const render = (answer: Answer) => (
    <AnswerForm
      key={homework.id}
      homeworkId={homework.id}
      initial={answer}
      readOnly={homework.access_mode === 'read_only'}
      loadError={!!homework.working_submission_id && working.isError}
    />
  );
  // Keep the form at one React position when the first saved answer gains an ID.
  // Changing its wrapper after the refetch would reset an already-blocked navigation.
  return (
    <>
      {homework.working_submission_id && (
        <ReadState query={working}>{() => null}</ReadState>
      )}
      {(!homework.working_submission_id || working.data) &&
        render(working.data || emptyAnswer(homework.id))}
    </>
  );
}
export function HomeworkPage() {
  const origin = useStudentHistoryOrigin();
  const { homeworkId = '' } = useParams();
  const query = useRead<Homework>(
    `/homeworks/${encodeURIComponent(homeworkId)}`,
  );
  usePageTitle(query.data?.title || 'Домашнее задание');
  return (
    <ReadState query={query}>
      {(data) => (
        <div className={`${styles.pageSections} ${layout.page}`}>
          {origin.returnTo ? (
            <StudentHistoryReturn />
          ) : (
            <Link to="/student/homeworks">Все домашние задания</Link>
          )}
          <header className={styles.heading}>
            <p>
              {data.course_name} · {data.lesson_title}
            </p>
            <h1>{data.title}</h1>
            <p>{deadlineLabel(data.deadline)}</p>
          </header>
          <ReadOnly mode={data.access_mode} reason={data.read_only_reason} />
          <div className={layout.workspace}>
            <div className={layout.documents}>
              {data.lesson_id && (
                <LessonMaterials key={data.id} lessonId={data.lesson_id} />
              )}
              <section className={styles.panel}>
                <h2>Условие</h2>
                <p className={`${styles.copy} ${layout.conditionCopy}`}>
                  <PlainTextLinks
                    text={data.description || 'Условие в приложенном файле.'}
                  />
                </p>
                <ReadFiles
                  condition
                  studyLabel="файл задания"
                  files={data.file ? [data.file] : []}
                />
              </section>
            </div>
            <div className={layout.answer}>
              <WorkingAnswer homework={data} />
            </div>
          </div>
          <section className={styles.panel}>
            <SubmissionHistory homeworkId={data.id} />
            <DeadlineHistory homeworkId={data.id} />
          </section>
        </div>
      )}
    </ReadState>
  );
}
