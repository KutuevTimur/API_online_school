import { Link } from 'react-router';
import { useEffect, useState } from 'react';
import { Button, Stack } from '@mantine/core';
import { request } from '../../../shared/api/client';
import { ApiError } from '../../../shared/api/error';
import { FormField, TextAreaField } from '../../../shared/ui/FormField';
import { SelectField } from '../../../shared/ui/SelectField';
import { ErrorSummary, focusFirstError } from '../../../shared/ui/ErrorSummary';
import { useFeedback } from '../../../shared/ui/FeedbackProvider';
import { validateProfile } from '../../profile/api';
import type { Invitation } from '../../students/api';
import { roles, type AdminUser } from './api';
export function UserForm({
  user,
  onSaved,
  onDirty,
}: {
  user?: AdminUser;
  onDirty: (dirty: boolean) => void;
  onSaved: (invitation?: Invitation) => void | Promise<void>;
}) {
  const [values, setValues] = useState({
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    middle_name: user?.middle_name || '',
    description: user?.description || '',
  });
  const [baseline, setBaseline] = useState(JSON.stringify(values));
  const [role, setRole] = useState('student');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const feedback = useFeedback();
  const dirty =
    JSON.stringify(values) !== baseline || (!user && role !== 'student');
  useEffect(() => onDirty(dirty), [dirty, onDirty]);
  return (
    <>
      <form
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          if (pending || uncertain) return;
          const invalid = validateProfile(values);
          if (!values.first_name.trim()) invalid.first_name = 'Укажите имя';
          if (!values.last_name.trim()) invalid.last_name = 'Укажите фамилию';
          setErrors(invalid);
          focusFirstError(invalid);
          if (Object.keys(invalid).length) return;
          setPending(true);
          setMessage('');
          void request<Invitation>(
            user ? `/users/${user.user_id}` : '/auth/register_by_admin',
            {
              method: user ? 'PATCH' : 'POST',
              body: {
                ...values,
                email: values.email || null,
                ...(!user ? { role } : {}),
              },
            },
          )
            .then((result) => {
              setBaseline(JSON.stringify(values));
              setRole('student');
              feedback(user ? 'Профиль сохранён' : 'Пользователь создан');
              onSaved(user ? undefined : (result ?? {}));
            })
            .catch((error) => {
              if (error instanceof ApiError) {
                const fields =
                  error.status === 409
                    ? {
                        username:
                          'Логин или почта уже используются. Укажите другие.',
                      }
                    : error.fields;
                setErrors(fields);
                focusFirstError(fields);
                const unknown =
                  !error.status || error.status >= 500 || error.status === 401;
                setUncertain(unknown);
                setMessage(
                  unknown
                    ? 'Не удалось подтвердить сохранение. Проверьте актуальную карточку или список перед повтором.'
                    : error.message,
                );
              }
            })
            .finally(() => setPending(false));
        }}
      >
        <Stack>
          <ErrorSummary errors={errors} />
          {!user && (
            <SelectField
              disabled={pending}
              label="Роль нового пользователя"
              value={role}
              data={roles.filter((r) => r.value !== 'admin')}
              onChange={(v) => setRole(v || 'student')}
            />
          )}
          {(
            [
              'username',
              'first_name',
              'last_name',
              'middle_name',
              'email',
            ] as const
          ).map((key) => (
            <FormField
              disabled={pending}
              key={key}
              id={key}
              name={key}
              label={
                {
                  username: 'Логин',
                  first_name: 'Имя',
                  last_name: 'Фамилия',
                  middle_name: 'Отчество (необязательно)',
                  email: 'Почта (необязательно)',
                }[key]
              }
              type={key === 'email' ? 'email' : 'text'}
              value={values[key]}
              error={errors[key]}
              onChange={(e) =>
                setValues({ ...values, [key]: e.currentTarget.value })
              }
            />
          ))}
          {(user?.role === 'teacher' || (!user && role === 'teacher')) && (
            <TextAreaField
              label="Описание преподавателя"
              value={values.description}
              disabled={pending}
              onChange={(e) =>
                setValues({ ...values, description: e.currentTarget.value })
              }
            />
          )}
          <p role="alert">{message}</p>
          <Button type="submit" loading={pending} disabled={uncertain}>
            {user ? 'Сохранить профиль' : 'Создать пользователя'}
          </Button>
          {uncertain && user && (
            <Button
              variant="default"
              onClick={() => {
                void Promise.resolve(onSaved())
                  .then(() => setUncertain(false))
                  .catch(() =>
                    setMessage(
                      'Не удалось перечитать профиль. Проверьте соединение.',
                    ),
                  );
              }}
            >
              Перечитать данные перед повтором
            </Button>
          )}
          {uncertain && !user && (
            <Link to="/admin/users">Проверить список пользователей</Link>
          )}
        </Stack>
      </form>
    </>
  );
}
