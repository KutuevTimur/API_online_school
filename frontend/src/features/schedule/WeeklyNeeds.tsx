import { Link } from 'react-router';
import { useRead, type Page } from '../courses/queries';
import { ReadState, Pages, useListState } from '../courses/ReadUI';
import { normLabel, type PlanningStudent } from './planning';
import styles from '../courses/read.module.css';
export function WeeklyNeeds({ week }: { week: string }) {
  const state = useListState('needs-');
  const query = useRead<Page<PlanningStudent>>('/teacher-planning/students', {
    week,
    deficit_only: 'true',
    limit: state.limit,
    offset: state.offset,
  });
  return (
    <details className={styles.panel}>
      <summary>
        Не хватает занятий{query.data ? ` · ${query.data.total}` : ''}
      </summary>
      <p>
        Сравниваем занятия за выбранную неделю с нормой ученика. Отменённые и
        архивные занятия не учитываем.
      </p>
      <ReadState query={query}>
        {(data) => (
          <>
            <p>Учеников с недобором: {data.total}</p>
            {!data.total && (
              <p>
                По заданным нормам всем хватает занятий. Ученики без нормы и на
                паузе сюда не попадают.
              </p>
            )}
            {data.items.map((s) => (
              <p key={s.user_id}>
                <Link to={`/teacher/students/${s.user_id}`}>
                  {s.first_name} {s.last_name}
                </Link>{' '}
                · {normLabel(s)}
              </p>
            ))}
            <p>
              <Link to="/teacher/students">Задать норму</Link> — откройте
              ученика → Настройки ученика → Недельная норма.
            </p>
            {data.total > state.limit && (
              <Pages
                label="Страницы недельного недобора"
                state={state}
                total={data.total}
              />
            )}
          </>
        )}
      </ReadState>
    </details>
  );
}
