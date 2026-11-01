import { Link, useParams } from 'react-router';
import dayjs from 'dayjs';
import { usePageTitle } from '../../app/router';
import { dateLabel } from '../../shared/lib/datetime';
import { type Lecture, useRead } from '../courses/queries';
import { ReadFiles, ReadOnly, ReadState } from '../courses/ReadUI';
import styles from '../courses/read.module.css';
export function dateBoundary(value: string | null, end = false) {
  if (
    !value ||
    !/^\d{4}-\d{2}-\d{2}$/.test(value) ||
    !dayjs(value).isValid() ||
    dayjs(value).format('YYYY-MM-DD') !== value
  )
    return undefined;
  const start = dayjs.tz(value, 'Europe/Moscow');
  return end
    ? start
        .add(1, 'day')
        .subtract(1, 'millisecond')
        .toISOString()
        .replace('.999Z', '.999999Z')
    : start.toISOString();
}
export function Material({ item }: { item: Lecture }) {
  return (
    <article className={styles.panel}>
      <p>
        {item.course_name || 'Учебный материал'} · {dateLabel(item.created_at)}
      </p>
      <h2>{item.original_file_name}</h2>
      <p>{item.lesson_title}</p>
      <ReadOnly mode={item.access_mode} reason={item.read_only_reason} />
      <ReadFiles files={item.file ? [item.file] : []} />
      {!item.file && <p>Файл пока недоступен. Попробуйте обновить страницу.</p>}
      {item.lesson_id && (
        <Link to={`/student/lessons/${item.lesson_id}`}>К занятию</Link>
      )}
    </article>
  );
}
export function MaterialPage() {
  const { lectureId = '' } = useParams();
  const query = useRead<Lecture>(`/lectures/${encodeURIComponent(lectureId)}`);
  usePageTitle('Конспект');
  return (
    <>
      <header className={styles.heading}>
        <Link to="/student/materials">К моим занятиям</Link>
        <h1>Конспект</h1>
      </header>
      <ReadState query={query}>{(item) => <Material item={item} />}</ReadState>
    </>
  );
}
