import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import type { components } from '../../../shared/api/schema';
import { Button, Stack } from '@mantine/core';
import { useRead } from '../../courses/queries';
import { ReadState } from '../../courses/ReadUI';
import { FormField } from '../../../shared/ui/FormField';
import { SelectField } from '../../../shared/ui/SelectField';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { request } from '../../../shared/api/client';
import { ApiError } from '../../../shared/api/error';
import { type Quota, formatBytes, quotaBytes } from './api';
export function Storage({
  userId,
  onDirty,
}: {
  userId: number;
  onDirty: (dirty: boolean) => void;
}) {
  const query = useRead<Quota>(`/users/${userId}/storage`);
  const [value, setValue] = useState('');
  const [unit, setUnit] = useState<'MB' | 'GB'>('GB');
  const [confirm, setConfirm] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const bytes = quotaBytes(value, unit);
  const dirty = !!value;
  useEffect(() => onDirty(dirty), [dirty, onDirty]);
  return (
    <section>
      <h2>Место для файлов ученика</h2>
      <p>
        Общий объём учебных файлов во всех курсах ученика, включая архив:
        материалы преподавателей, задания, ответы и файлы проверки. Это не лимит
        одного файла.
      </p>
      <ReadState query={query}>
        {(data) => (
          <>
            <p>
              Использовано: {formatBytes(data.used_bytes)}. Лимит:{' '}
              {formatBytes(data.limit_bytes)}.
            </p>
            {data.warning && (
              <p role="status">
                {data.warning === 'full'
                  ? 'Место закончилось'
                  : data.warning === 'critical'
                    ? 'Критически мало места'
                    : 'Место скоро закончится'}
                . Чтение сохранённых материалов доступно.
              </p>
            )}
            <details>
              <summary>Изменить лимит места</summary>
              <Stack>
                <FormField
                  label="Новый лимит"
                  inputMode="decimal"
                  value={value}
                  onChange={(e) => setValue(e.currentTarget.value)}
                  error={
                    value && bytes === null
                      ? 'Укажите объём от 20,97152 МБ до 1 099,511627776 ГБ без долей байта'
                      : undefined
                  }
                />
                <SelectField
                  label="Единица измерения"
                  value={unit}
                  data={[
                    { value: 'MB', label: 'МБ' },
                    { value: 'GB', label: 'ГБ' },
                  ]}
                  onChange={(v) => setUnit(v === 'MB' ? 'MB' : 'GB')}
                />
                <p>
                  Изменение лимита не освобождает место и не удаляет файлы. Если
                  лимит меньше занятого места, новые загрузки будут недоступны.
                </p>
                <Button
                  disabled={bytes === null}
                  onClick={() => {
                    setError('');
                    setConfirm(true);
                  }}
                >
                  Проверить новый лимит
                </Button>
              </Stack>
            </details>
          </>
        )}
      </ReadState>
      <p role="status">{message}</p>
      <ConfirmDialog
        opened={confirm}
        title="Изменить лимит места?"
        confirmLabel="Изменить лимит места"
        pending={pending}
        error={error}
        onCancel={() => setConfirm(false)}
        onConfirm={() => {
          if (pending || bytes === null) return;
          setPending(true);
          setError('');
          void request(`/admin/users/${userId}/storage-quota`, {
            method: 'PATCH',
            body: { limit_bytes: bytes },
          })
            .then(() => {
              setConfirm(false);
              setValue('');
              setMessage('Лимит изменён');
              void query.refetch();
            })
            .catch((e) => {
              setError(
                e instanceof ApiError
                  ? e.message
                  : 'Не удалось подтвердить изменение.',
              );
              void query.refetch();
            })
            .finally(() => setPending(false));
        }}
      >
        <p>
          Новый лимит: {bytes !== null && formatBytes(bytes)}. Файлы и занятое
          место сохранятся.
        </p>
      </ConfirmDialog>
    </section>
  );
}

export function TeacherStorage({ userId }: { userId: number }) {
  const query = useRead<components['schemas']['TeacherStorageResponse']>(
    `/admin/users/${userId}/course-storage`,
  );
  return (
    <section>
      <h2>Файлы в курсах преподавателя</h2>
      <p>
        Все учебные файлы в курсах этого преподавателя, включая архив:
        материалы, задания, ответы учеников и файлы проверки. Место учитывается
        в лимитах учеников.
      </p>
      <ReadState query={query}>
        {(data) => (
          <>
            <p>Всего занято: {formatBytes(data.used_bytes)}.</p>
            {!data.courses.length ? (
              <p>В курсах пока нет учебных файлов.</p>
            ) : (
              <details>
                <summary>Посмотреть по курсам</summary>
                <ul>
                  {data.courses.map((c) => (
                    <li key={c.course_id}>
                      <Link to={`/admin/courses/${c.course_id}`}>
                        {c.course_name}
                      </Link>{' '}
                      — {formatBytes(c.bytes)}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </>
        )}
      </ReadState>
    </section>
  );
}
