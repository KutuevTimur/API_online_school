import { useState } from 'react';
import type { components } from '../../shared/api/schema';
import { answerFiles } from '../../shared/api/files';
import { dateLabel, deadlineLabel } from '../../shared/lib/datetime';
import { ReadFiles, ReadState, Pages, useListState } from '../courses/ReadUI';
import { type Answer, type Page, useRead } from '../courses/queries';
export function SubmissionHistory({ homeworkId }: { homeworkId: number }) {
  const [open, setOpen] = useState(false);
  const state = useListState();
  const history = useRead<Page<Answer>>(
    `/homeworks/${homeworkId}/submissions`,
    { limit: state.limit, offset: state.offset },
    open,
  );
  return (
    <details onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>Исторические попытки</summary>
      {open && (
        <ReadState query={history}>
          {(data) => (
            <>
              {data.items
                .filter((a) => !a.is_working)
                .map((a) => (
                  <article key={a.id}>
                    <h3>Попытка {a.attempt_number}</h3>
                    <p>
                      {dateLabel(a.created_at)} ·{' '}
                      {a.status === 'checked' ? 'Проверено' : 'История'}
                    </p>
                    <p>{a.text_content}</p>
                    {a.grade !== null && (
                      <p>
                        Оценка: {a.grade} из 5 · {a.teacher_comment}
                      </p>
                    )}
                    <ReadFiles files={answerFiles(a)} />
                  </article>
                ))}
              {!data.items.some((a) => !a.is_working) && (
                <p>
                  На этой странице исторических попыток нет. Текущее решение
                  показано выше.
                </p>
              )}
              <Pages total={data.total} state={state} />
            </>
          )}
        </ReadState>
      )}
    </details>
  );
}
export function DeadlineHistory({ homeworkId }: { homeworkId: number }) {
  const [open, setOpen] = useState(false);
  const history = useRead<components['schemas']['PlacementResponseDTO'][]>(
    `/homeworks/${homeworkId}/placements`,
    {},
    open,
  );
  return (
    <details onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>Сроки и переносы задания</summary>
      {open && (
        <ReadState query={history}>
          {(data) => (
            <>
              {data.map((p) => (
                <article key={p.id}>
                  <h3>
                    {p.kind === 'debt' ? 'Долг' : 'Первоначальное задание'}
                  </h3>
                  <p>
                    {deadlineLabel(p.due_at)}
                    {p.frozen ? ' · Срок зафиксирован' : ''}
                  </p>
                  <ul>
                    {p.events.map((e) => (
                      <li key={e.id}>
                        {dateLabel(e.created_at)} · {deadlineLabel(e.due_at)}
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </>
          )}
        </ReadState>
      )}
    </details>
  );
}
