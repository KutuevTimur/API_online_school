import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { useState } from 'react';
import { Button, Checkbox, Stack } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { useRead, type Page } from '../courses/queries';
import { ReadState } from '../courses/ReadUI';
import { FormField } from '../../shared/ui/FormField';
import { DateField } from '../../shared/ui/DateTimeField';
import { SelectField } from '../../shared/ui/SelectField';
import { request } from '../../shared/api/client';
import { weekStart } from '../../shared/lib/datetime';
import { normLabel, planningRefresh, type PlanningStudent } from './planning';
export function NormEditor({
  studentId,
  embedded = false,
}: {
  studentId: number;
  embedded?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [week, setWeek] = useState(weekStart().format('YYYY-MM-DD'));
  const [kind, setKind] = useState('exception');
  const [target, setTarget] = useState('');
  const [paused, setPaused] = useState(false);
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [blocked, setBlocked] = useState(false);
  const client = useQueryClient();
  const query = useRead<Page<PlanningStudent>>('/teacher-planning/students', {
    week,
    student_user_id: studentId,
    limit: 100,
    offset: 0,
  });
  const Container = embedded ? 'section' : 'details';
  return (
    <Container>
      {embedded ? <h3>Недельная норма</h3> : <summary>Недельная норма</summary>}
      <Stack>
        <DateField
          label="Неделя, МСК"
          value={week}
          onChange={(v) => {
            if (editing) {
              setError(
                'Завершите или отмените изменение нормы перед выбором другой недели.',
              );
              return;
            }
            setWeek(weekStart(v).format('YYYY-MM-DD'));
            setBlocked(false);
          }}
        />
        <ReadState query={query}>
          {(data) => {
            const s = data.items.find((x) => x.user_id === studentId);
            return s ? (
              <>
                <p>{normLabel(s)} · все курсы этого преподавателя</p>
                {!editing && (
                  <Button
                    variant="default"
                    onClick={() => {
                      setTarget(s.target == null ? '' : String(s.target));
                      setPaused(s.paused);
                      setEditing(true);
                    }}
                  >
                    Изменить недельную норму
                  </Button>
                )}
                {editing && (
                  <>
                    {(target !== (s.target == null ? '' : String(s.target)) ||
                      paused !== s.paused) && <DirtyFormGuard dirty />}
                    <Button
                      variant="default"
                      onClick={() => {
                        setEditing(false);
                        setTarget(s.target == null ? '' : String(s.target));
                        setPaused(s.paused);
                      }}
                    >
                      Отменить изменение нормы
                    </Button>
                    <SelectField
                      label="Изменить норму"
                      value={kind}
                      data={[
                        {
                          value: 'exception',
                          label: 'Только выбранная неделя',
                        },
                        {
                          value: 'regular',
                          label: 'Обычная норма с выбранной недели',
                        },
                      ]}
                      onChange={(v) => setKind(v || 'exception')}
                    />
                    <p>
                      Обычная норма меняется со следующей недели. Текущая —
                      отдельным исключением. Прошлые недели сохраняются.
                    </p>
                    <FormField
                      label="Занятий в неделю (пусто — норма не задана)"
                      value={target}
                      inputMode="numeric"
                      onChange={(e) => setTarget(e.currentTarget.value)}
                    />
                    <Checkbox
                      label="Пауза без недобора"
                      checked={paused}
                      onChange={(e) => setPaused(e.currentTarget.checked)}
                    />
                    <Button
                      loading={pending}
                      disabled={blocked}
                      onClick={() => {
                        if (pending) return;
                        if (
                          target &&
                          (!Number.isInteger(Number(target)) ||
                            Number(target) < 1)
                        ) {
                          setError('Введите положительное целое число');
                          return;
                        }
                        busy(true);
                        setError('');
                        void request(
                          `/teacher-planning/students/${studentId}/norm`,
                          {
                            method: 'PUT',
                            body: {
                              week,
                              kind,
                              target: target ? Number(target) : null,
                              paused,
                              expected_revision: s.norm_revision,
                            },
                          },
                        )
                          .then(async () => {
                            await client.invalidateQueries(planningRefresh);
                            setError('Норма сохранена');
                          })
                          .catch(() => {
                            setBlocked(true);
                            setError(
                              'Не удалось подтвердить изменение. Проверьте неделю и загрузите актуальную норму.',
                            );
                          })
                          .finally(() => busy(false));
                      }}
                    >
                      Сохранить норму
                    </Button>
                    {blocked && (
                      <Button
                        variant="default"
                        onClick={() =>
                          void query.refetch().then((r) => {
                            if (!r.isError) {
                              setBlocked(false);
                              setError(
                                'Актуальные значения загружены. Сравните их со своим выбором перед повтором.',
                              );
                            }
                          })
                        }
                      >
                        Загрузить актуальную норму
                      </Button>
                    )}
                  </>
                )}
              </>
            ) : (
              <p>Активное обучение не найдено.</p>
            );
          }}
        </ReadState>
        {error && <p role="status">{error}</p>}
      </Stack>
    </Container>
  );
}
