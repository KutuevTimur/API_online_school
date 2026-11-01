import type { Answer } from '../../shared/api/files';
import { ReadFiles } from '../courses/ReadUI';
import styles from '../courses/read.module.css';
export function ReviewResult({
  answer,
  teacher = false,
  headingAs = 'h2',
}: {
  answer: Answer;
  teacher?: boolean;
  headingAs?: 'h2' | 'h4';
}) {
  const Heading = headingAs;
  const FilesHeading = headingAs === 'h4' ? 'h5' : 'h3';
  return (
    <>
      <Heading>Проверка учителя</Heading>
      <p role="status" className={styles.resultGrade}>
        {teacher ? 'Проверено · ' : ''}Оценка: {answer.grade} из 5
      </p>
      <p className={styles.copy}>
        {answer.teacher_comment ||
          (teacher ? 'Без комментария' : 'Учитель не добавил комментарий')}
      </p>
      {!!answer.review_files?.length && (
        <>
          <FilesHeading className={styles.resultFilesHeading}>
            Файлы от учителя
          </FilesHeading>
          <ReadFiles
            review
            files={answer.review_files.flatMap((f) => (f.file ? [f.file] : []))}
          />
        </>
      )}
      {teacher && (
        <p className={styles.muted}>
          Проверка завершена. Изменить результат нельзя.
        </p>
      )}
    </>
  );
}
