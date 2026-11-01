import { Button } from '@mantine/core';
import { Link } from 'react-router';
import { type Course, type Lesson, useRead } from './queries';
import styles from './read.module.css';

// Scoped detail uses the canonical readKey/cache, never a paginated catalog lookup.
export function CourseContext({
  lesson,
  variant = 'full',
}: {
  lesson: Lesson;
  variant?: 'full' | 'teacher-inline';
}) {
  const course = useRead<Course>(`/courses/${lesson.course_id}`);
  return (
    <div className={styles.courseContext}>
      {variant === 'full' && (
        <Link to={`/student/courses/${lesson.course_id}`}>
          Курс:{' '}
          {course.data?.name || lesson.course_name || 'Название недоступно'}
        </Link>
      )}
      {course.data?.teacher_name && (
        <span>Преподаватель: {course.data.teacher_name}</span>
      )}
      {course.isPending && (
        <span role="status">Загружаем данные преподавателя…</span>
      )}
      {course.isError && (
        <div role="alert">
          Не удалось {course.data ? 'обновить' : 'загрузить'} данные{' '}
          {variant === 'full' ? 'курса и преподавателя' : 'преподавателя'}.
          <Button variant="default" onClick={() => void course.refetch()}>
            Повторить
          </Button>
        </div>
      )}
      {!course.isPending && !course.isError && !course.data?.teacher_name && (
        <span>Имя преподавателя недоступно</span>
      )}
    </div>
  );
}
