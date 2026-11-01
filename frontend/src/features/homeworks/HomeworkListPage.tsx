import { Checkbox, Group } from '@mantine/core';
import { usePageTitle } from '../../app/router';
import { SelectField } from '../../shared/ui/SelectField';
import { LinkButton } from '../../shared/ui/LinkButton';
import { deadlineLabel } from '../../shared/lib/datetime';
import {
  type Homework,
  type Course,
  type Page,
  useRead,
} from '../courses/queries';
import { ReadState, Views, Pages, useListState } from '../courses/ReadUI';
import styles from '../courses/read.module.css';
export function HomeworkListPage() {
  usePageTitle('Домашние задания');
  const state = useListState();
  const status = ['todo', 'submitted', 'checked', 'all'].includes(
    state.params.get('status') || '',
  )
    ? state.params.get('status')!
    : 'todo';
  const course = state.params.get('course_id') || '';
  const courses = useRead<Page<Course>>('/courses', {
    view: 'all',
    limit: 1000,
    offset: 0,
  });
  const query = useRead<Page<Homework>>('/homeworks/my/page', {
    limit: state.limit,
    offset: state.offset,
    view: state.view,
    status,
    course_id: course || undefined,
    overdue_only: state.params.get('overdue') === '1' ? 'true' : 'false',
  });
  return (
    <>
      <header className={styles.heading}>
        <h1>Домашние задания</h1>
        <p>Откройте задание, добавьте решение и отправьте его учителю.</p>
      </header>
      <Views
        value={state.view}
        onChange={(view) => state.update({ view, offset: 0 })}
      />
      {courses.isError && (
        <p role="alert">
          Не удалось загрузить курсы.{' '}
          <button type="button" onClick={() => void courses.refetch()}>
            Повторить загрузку курсов
          </button>
        </p>
      )}
      <Group align="end" mb="lg">
        <SelectField
          label="Статус задания"
          value={status}
          allowDeselect={false}
          data={[
            { value: 'todo', label: 'К выполнению' },
            { value: 'submitted', label: 'На проверке' },
            { value: 'checked', label: 'Проверено' },
            { value: 'all', label: 'Все статусы' },
          ]}
          onChange={(value) =>
            state.update({ status: value || 'todo', offset: 0 })
          }
        />
        <SelectField
          label="Курс"
          value={course || null}
          clearable
          placeholder="Все курсы"
          data={(courses.data?.items || []).map((c) => ({
            value: String(c.id),
            label: c.name,
          }))}
          onChange={(value) =>
            state.update({ course_id: value || '', offset: 0 })
          }
        />
        <Checkbox
          label="Только просроченные"
          checked={state.params.get('overdue') === '1'}
          onChange={(e) =>
            state.update({
              overdue: e.currentTarget.checked ? '1' : '0',
              offset: 0,
            })
          }
        />
      </Group>
      <ReadState query={query}>
        {(data) => (
          <>
            {!data.items.length && (
              <section className={styles.panel}>
                <h2>Заданий по этим условиям нет</h2>
                <LinkButton to="/student/homeworks?view=all&status=all">
                  Показать все задания
                </LinkButton>
              </section>
            )}
            <div className={styles.grid}>
              {data.items.map((item) => (
                <article
                  key={item.id}
                  className={
                    item.submission_status === 'checked'
                      ? styles.result
                      : styles.lesson
                  }
                >
                  <p>
                    {item.course_name}
                    {item.placement_kind === 'debt' ? ' · Долг' : ''}
                  </p>
                  <h2>{item.title}</h2>
                  <p className={styles.copy}>{item.description}</p>
                  <p>{deadlineLabel(item.deadline)}</p>
                  <p>
                    {item.submission_status === 'checked'
                      ? 'Проверено'
                      : item.submission_status === 'submitted'
                        ? 'На проверке'
                        : 'К выполнению'}
                  </p>
                  <LinkButton to={`/student/homeworks/${item.id}`}>
                    {item.submission_status === 'checked'
                      ? 'Посмотреть результат'
                      : 'Открыть задание'}
                  </LinkButton>
                </article>
              ))}
            </div>
            <Pages total={data.total} state={state} />
          </>
        )}
      </ReadState>
    </>
  );
}
