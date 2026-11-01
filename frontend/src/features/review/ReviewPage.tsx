import { Link, useParams, useSearchParams } from 'react-router';
import { PlainTextLinks } from '../../shared/ui/PlainTextLinks';
import { usePageTitle } from '../../app/router';
import type { Answer } from '../../shared/api/files';
import { type Homework, type Lesson, useRead } from '../courses/queries';
import { dateLabel } from '../../shared/lib/datetime';
import { ReadFiles, ReadOnly, ReadState } from '../courses/ReadUI';
import { type Student, studentLabel } from '../students/api';
import { ReviewForm } from './ReviewForm';
import styles from '../courses/read.module.css';
import layout from './review.module.css';
export function ReviewPage() {
  const { submissionId = '' } = useParams();
  const [params] = useSearchParams();
  const homeworkId = Number(params.get('homework_id'));
  const valid =
    Number.isSafeInteger(homeworkId) &&
    homeworkId > 0 &&
    /^\d+$/.test(submissionId);
  const homework = useRead<Homework>(
    `/homeworks/${homeworkId}`,
    {},
    valid,
    60000,
  );
  const answer = useRead<Answer>(
    `/submissions/${encodeURIComponent(submissionId)}`,
    { homework_id: homeworkId },
    valid,
    60000,
  );
  const student = useRead<Student>(
    `/users/${homework.data?.student_user_id || 0}`,
    {},
    !!homework.data?.student_user_id,
  );
  const lesson = useRead<Lesson>(
    `/lessons/${homework.data?.lesson_id || 0}`,
    {},
    !!homework.data?.lesson_id,
  );
  usePageTitle(
    homework.data?.title
      ? `Проверка · ${homework.data.title}`
      : 'Проверка решения',
  );
  const back = new URLSearchParams(params);
  back.delete('homework_id');
  back.delete('file');
  back.delete('condition-file');
  back.delete('review-file');
  return (
    <>
      <Link to={`/teacher/review${back.size ? '?' + back : ''}`}>
        К очереди
      </Link>
      {!valid ? (
        <p role="alert">Неполный адрес работы. Откройте ответ из очереди.</p>
      ) : (
        <ReadState query={homework}>
          {(hw) => (
            <>
              <ReadOnly mode={hw.access_mode} reason={hw.read_only_reason} />
              <ReadState query={student}>
                {(s) => (
                  <>
                    <header className={layout.heading}>
                      <div>
                        <h1>
                          <Link to={`/teacher/students/${s.user_id}`}>
                            {s.first_name} {s.last_name}
                            {s.school_grade ? ` · ${s.school_grade} класс` : ''}
                          </Link>
                        </h1>
                        <p>{hw.title}</p>
                        {hw.lesson_id && (
                          <p className={styles.muted}>
                            {hw.lesson_title}
                            {lesson.data &&
                              ` · ${dateLabel(lesson.data.scheduled_at)}`}
                            {lesson.isPending && ' · Загружаем дату занятия…'}
                            {lesson.isError && (
                              <>
                                {' '}
                                · Дата занятия недоступна.{' '}
                                <button
                                  className={layout.retryDate}
                                  onClick={() => void lesson.refetch()}
                                >
                                  Повторить
                                </button>
                              </>
                            )}
                          </p>
                        )}
                      </div>
                      {hw.lesson_id && (
                        <Link
                          to={`/teacher/lessons/${hw.lesson_id}?student=${s.user_id}`}
                        >
                          К занятию
                        </Link>
                      )}
                    </header>
                    <details
                      key={hw.id}
                      className={`${styles.panel} ${layout.condition}`}
                      open
                    >
                      <summary>
                        Условие задания
                        <span className={layout.collapse}>Свернуть</span>
                        <span className={layout.expand}>Развернуть</span>
                      </summary>
                      <p className={`${styles.copy} ${layout.conditionCopy}`}>
                        <PlainTextLinks
                          text={
                            hw.description || 'Условие в приложенном файле.'
                          }
                        />
                      </p>
                      <ReadFiles condition files={hw.file ? [hw.file] : []} />
                    </details>
                    <ReadState query={answer}>
                      {(a) => (
                        <ReviewForm
                          key={`${hw.id}:${a.id}`}
                          initial={a}
                          student={studentLabel(s)}
                          title={hw.title}
                          canReview={
                            hw.can_review &&
                            !homework.isError &&
                            !answer.isError
                          }
                        />
                      )}
                    </ReadState>
                  </>
                )}
              </ReadState>
            </>
          )}
        </ReadState>
      )}
    </>
  );
}
