import { useEffect, useRef, useState } from 'react';
import { Button, Stack } from '@mantine/core';
import { FormField } from '../../shared/ui/FormField';
import { SelectField } from '../../shared/ui/SelectField';
import { useRead, type Page } from '../courses/queries';
import { studentLabel, type Student } from './api';
export function OwnStudentSelect({
  value,
  onChange,
  error,
  className,
}: {
  value: string;
  onChange: (id: string) => void;
  error?: string;
  className?: string;
}) {
  const [search, setSearch] = useState('');
  const [q, setQ] = useState('');
  const [composing, setComposing] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (composing) return;
    const timer = setTimeout(() => setQ(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search, composing]);
  const students = useRead<Page<Student>>('/users/students', {
    q: q || undefined,
    limit: 20,
    offset: 0,
  });
  const selected = useRead<Student>(
    `/users/${encodeURIComponent(value || '0')}`,
    {},
    !!value,
  );
  const data = [
    ...new Map(
      [
        ...(students.data?.items || []),
        ...(selected.data ? [selected.data] : []),
      ].map((s) => [
        String(s.user_id),
        {
          value: String(s.user_id),
          label: `${studentLabel(s)} · ${s.username}`,
        },
      ]),
    ).values(),
  ];
  return (
    <Stack className={className}>
      <FormField
        ref={input}
        label="Найти своего ученика"
        value={search}
        onCompositionStart={() => setComposing(true)}
        onCompositionEnd={() => setComposing(false)}
        onChange={(e) => setSearch(e.currentTarget.value)}
        rightSection={
          search ? (
            <Button
              variant="subtle"
              aria-label="Очистить поиск ученика"
              onClick={() => {
                setSearch('');
                setQ('');
                input.current?.focus();
              }}
            >
              ×
            </Button>
          ) : undefined
        }
      />
      <SelectField
        id="student"
        label="Ученик"
        placeholder="Выберите ученика"
        clearable
        value={value || null}
        data={data}
        error={error}
        onChange={(v) => onChange(v || '')}
        nothingFoundMessage={
          students.isPending ? 'Загружаем…' : 'Ничего не найдено'
        }
      />
      {students.isFetching && <p role="status">Загружаем учеников…</p>}
      {students.isError && (
        <Button variant="default" onClick={() => void students.refetch()}>
          Повторить загрузку учеников
        </Button>
      )}
      {(students.data?.total || 0) > 20 && (
        <p>Показаны первые 20. Уточните имя или логин.</p>
      )}
    </Stack>
  );
}
