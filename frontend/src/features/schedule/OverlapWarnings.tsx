import { Link } from 'react-router';
import { useRead, type Lesson } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { dateLabel } from '../../shared/lib/datetime';
function Overlap({ id }: { id: number }) {
  const query = useRead<Lesson>(`/lessons/${id}`);
  return (
    <ReadState query={query}>
      {(lesson) => (
        <p>
          <Link to={`/teacher/lessons/${lesson.id}`}>
            {lesson.title} · {dateLabel(lesson.scheduled_at)}
          </Link>{' '}
          · {lesson.duration_minutes} мин
        </p>
      )}
    </ReadState>
  );
}
export function OverlapWarnings({
  warnings,
}: {
  warnings: { lesson_ids: number[] }[];
}) {
  const ids = [...new Set(warnings.flatMap((w) => w.lesson_ids))];
  return (
    <section role="status">
      <h2>Сохранено, есть пересечение</h2>
      {ids.map((id) => (
        <Overlap key={id} id={id} />
      ))}
    </section>
  );
}
