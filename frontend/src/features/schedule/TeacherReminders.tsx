import { useState } from 'react';
import { Button } from '@mantine/core';
import { FileText, NotebookPen, ArrowRight } from 'lucide-react';
import { LinkButton } from '../../shared/ui/LinkButton';
import { Link, useLocation } from 'react-router';
import { useRead, type Page } from '../courses/queries';
import { ReadState, Pages, useListState } from '../courses/ReadUI';
import { dateLabel } from '../../shared/lib/datetime';
import type { Reminder } from './planning';
import styles from '../courses/read.module.css';
export function TeacherReminders({
  studentId,
  overview = false,
}: {
  studentId?: number;
  overview?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const state = useListState('reminder-');
  const location = useLocation();
  const query = useRead<Page<Reminder>>(
    '/teacher-planning/reminders',
    {
      student_user_id: studentId,
      limit: state.limit,
      offset: state.offset,
    },
    true,
    60000,
  );
  return (
    <section
      className={`${styles.panel} ${overview ? `${styles.dayPanel} ${styles.materialsPanel}` : ''}`}
    >
      <h2 className={overview ? styles.daySectionTitle : undefined}>
        {overview && <FileText size={20} aria-hidden="true" />}Нужно выдать
        материалы
        {overview && query.data && (
          <span className={styles.dayCount}>{query.data.total}</span>
        )}
      </h2>
      {!overview && (
        <p className={styles.muted}>Только закончившиеся занятия</p>
      )}
      <ReadState query={query}>
        {(data) => (
          <>
            {!data.total && (
              <p>У закончившихся занятий нет невыданных материалов.</p>
            )}
            {data.items
              .slice(
                0,
                overview && !expanded && state.offset === 0 ? 3 : undefined,
              )
              .map((r) => (
                <article
                  className={overview ? styles.dayMaterialRow : styles.row}
                  key={`${r.lesson_id}-${r.student_user_id}`}
                >
                  <div className={overview ? styles.dayTaskBody : undefined}>
                    <h3>
                      {overview ? (
                        <>
                          {r.first_name} {r.last_name}
                        </>
                      ) : (
                        <Link
                          to={`/teacher/lessons/${r.lesson_id}?student=${r.student_user_id}`}
                          state={{
                            returnTo: location.pathname + location.search,
                            studentListSearch:
                              location.state?.studentListSearch,
                          }}
                        >
                          {r.first_name} {r.last_name}
                        </Link>
                      )}
                    </h3>
                    <p>
                      {overview
                        ? dateLabel(r.scheduled_at)
                        : `${r.title} · ${r.course_name} · ${dateLabel(r.scheduled_at)}`}
                    </p>
                    <p
                      className={
                        overview ? styles.dayMaterialNeeds : styles.attention
                      }
                    >
                      {overview ? (
                        <>
                          {r.needs_homework && (
                            <span>
                              <NotebookPen size={15} aria-hidden="true" />
                              ДЗ не выдано
                            </span>
                          )}
                          {r.needs_lecture && (
                            <span>
                              <FileText size={15} aria-hidden="true" />
                              Нет конспекта
                            </span>
                          )}
                        </>
                      ) : (
                        [
                          r.needs_homework ? 'ДЗ не выдано' : '',
                          r.needs_lecture ? 'Конспект не загружен' : '',
                        ]
                          .filter(Boolean)
                          .join(' · ')
                      )}
                    </p>
                  </div>
                  {overview && (
                    <LinkButton
                      to={`/teacher/lessons/${r.lesson_id}?student=${r.student_user_id}`}
                      state={{
                        returnTo: location.pathname + location.search,
                        studentListSearch: location.state?.studentListSearch,
                      }}
                      variant="default"
                      rightSection={<ArrowRight size={16} aria-hidden="true" />}
                      aria-label={`К занятию: ${r.first_name} ${r.last_name}, ${dateLabel(r.scheduled_at)}`}
                    >
                      К занятию
                    </LinkButton>
                  )}
                </article>
              ))}
            {overview && expanded && (
              <Button
                variant="default"
                onClick={() => {
                  setExpanded(false);
                  state.update({ offset: 0 });
                }}
              >
                Свернуть
              </Button>
            )}
            {overview && !expanded && state.offset === 0 && data.total > 3 ? (
              <Button variant="default" onClick={() => setExpanded(true)}>
                {overview
                  ? `Показать все · ${data.total}`
                  : `Все занятия без материалов · ${data.total}`}
              </Button>
            ) : (
              <Pages
                label="Страницы напоминаний преподавателя"
                total={data.total}
                state={state}
              />
            )}
          </>
        )}
      </ReadState>
    </section>
  );
}
