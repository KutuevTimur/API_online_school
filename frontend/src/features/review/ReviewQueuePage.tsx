import { useEffect } from 'react';
import { Link } from 'react-router';
import { Button } from '@mantine/core';
import { LinkButton } from '../../shared/ui/LinkButton';
import { usePageTitle } from '../../app/router';
import { DataList } from '../../shared/ui/DataList';
import { SelectField } from '../../shared/ui/SelectField';
import { StatusBadge } from '../../shared/ui/StatusBadge';
import { useRead, type Page, type Course } from '../courses/queries';
import { ReadState, Pages, useListState } from '../courses/ReadUI';
import { OwnStudentSelect } from '../students/OwnStudentSelect';
import { dateLabel } from '../../shared/lib/datetime';
import { reviewPath, type ReviewItem } from './api';
import styles from '../courses/read.module.css';
import layout from './review.module.css';
function ReviewInfo({
  item: r,
  compact = false,
}: {
  item: ReviewItem;
  compact?: boolean;
}) {
  return (
    <>
      <strong>
        {r.student_first_name} {r.student_last_name}
      </strong>
      <span>
        {r.homework_title}
        {r.course_name !== `${r.student_first_name} ${r.student_last_name}`
          ? ` · ${r.course_name}`
          : ''}
      </span>
      <span className={styles.muted}>
        {!compact && <>{r.student_username} · </>}
        {r.submitted_at ? dateLabel(r.submitted_at) : 'Отправлено'}
      </span>
    </>
  );
}
export function ReviewRows({
  items,
  search = '',
  compact = false,
}: {
  items: ReviewItem[];
  search?: string;
  compact?: boolean;
}) {
  if (compact)
    return (
      <ul className={styles.dayCompactReview} aria-label="Работы на проверку">
        {items.map((r) => (
          <li key={r.id} className={styles.dayReviewRow}>
            <div className={styles.dayTaskBody}>
              <ReviewInfo item={r} compact />
            </div>
            <LinkButton
              to={reviewPath(r, search)}
              variant="default"
              navigation
              className={styles.dayTaskAction}
              aria-label={`Проверить: ${r.student_first_name} ${r.student_last_name}, ${r.homework_title}`}
            >
              Проверить
            </LinkButton>
          </li>
        ))}
      </ul>
    );
  return (
    <DataList
      variant="review"
      label="Работы на проверку"
      rows={items}
      rowKey={(r) => String(r.id)}
      rowLink={(r) => reviewPath(r, search)}
      renderRow={(r) => (
        <>
          <ReviewInfo item={r} />
          <StatusBadge status="submitted" />
        </>
      )}
    />
  );
}

export function ReviewQueuePage() {
  usePageTitle('На проверку');
  const state = useListState();
  const courseState = useListState('courses-');
  const student = state.params.get('student_user_id') || '';
  const course = state.params.get('course_id') || '';
  const query = useRead<Page<ReviewItem>>(
    '/submissions/review-queue',
    {
      limit: state.limit,
      offset: state.offset,
      student_user_id: student || undefined,
      course_id: course || undefined,
    },
    true,
    60000,
  );
  const courses = useRead<Page<Course>>('/courses', {
    view: 'active',
    student_user_id: student || undefined,
    limit: courseState.limit,
    offset: courseState.offset,
  });
  const selected = useRead<Course>(
    `/courses/${encodeURIComponent(course || '0')}`,
    {},
    !!course,
  );
  const courseOptions = [
    ...new Map(
      [
        ...(courses.data?.items || []),
        ...(selected.data ? [selected.data] : []),
      ].map((c) => [String(c.id), { value: String(c.id), label: c.name }]),
    ).values(),
  ];
  useEffect(() => {
    if (
      query.data &&
      !query.isFetching &&
      !query.isError &&
      state.offset > 0 &&
      state.offset >= query.data.total
    )
      state.update({ offset: 0 });
  }, [query.data, query.isFetching, query.isError, state]);
  return (
    <>
      <header className={styles.heading}>
        <h1>На проверку</h1>
        <p>
          Отправленные решения ваших учеников. Откройте работу, прочитайте ответ
          и поставьте оценку.
        </p>
      </header>
      <section className={styles.panel} aria-label="Фильтры очереди">
        <div className={layout.filters}>
          <OwnStudentSelect
            className={layout.studentFilters}
            value={student}
            onChange={(id) =>
              state.update({
                student_user_id: id,
                course_id: '',
                offset: 0,
                'courses-offset': 0,
              })
            }
          />
          <details className={layout.courseFilter}>
            <summary>
              Курс: {course ? selected.data?.name || `№${course}` : 'все курсы'}
            </summary>
            <SelectField
              label="Курс"
              placeholder="Все курсы"
              clearable
              value={course || null}
              data={courseOptions}
              onChange={(id) =>
                state.update({ course_id: id || '', offset: 0 })
              }
            />
            {courses.isError && (
              <Button variant="default" onClick={() => void courses.refetch()}>
                Повторить загрузку курсов
              </Button>
            )}
            {courses.isFetching && <p role="status">Загружаем курсы…</p>}
            {(courses.data?.total || 0) > courseState.limit && (
              <Pages
                label="Страницы выбора курса"
                state={courseState}
                total={courses.data!.total}
              />
            )}
          </details>
        </div>
        {(student || course) && (
          <Button
            variant="default"
            onClick={() =>
              state.update({
                student_user_id: '',
                course_id: '',
                offset: 0,
                'courses-offset': 0,
              })
            }
          >
            Сбросить фильтры
          </Button>
        )}
      </section>
      <ReadState query={query}>
        {(data) => (
          <section className={styles.panel}>
            {!data.total && (
              <p>
                {student || course
                  ? 'По этим фильтрам нет работ на проверку.'
                  : 'Пока нет работ на проверку. Отправленные учениками решения появятся здесь.'}
              </p>
            )}
            <ReviewRows items={data.items} search={state.params.toString()} />
            <Pages
              total={data.total}
              state={state}
              label="Страницы очереди проверки"
            />
            <Link to="/teacher">В мой день</Link>
          </section>
        )}
      </ReadState>
    </>
  );
}
