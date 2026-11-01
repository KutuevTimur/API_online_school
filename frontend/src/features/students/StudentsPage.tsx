import { useEffect, useRef, useState } from 'react';
import { Link, useParams, useLocation } from 'react-router';
import { Button, Stack, Group } from '@mantine/core';
import { usePageTitle } from '../../app/router';
import { request } from '../../shared/api/client';
import { ApiError } from '../../shared/api/error';
import { FormField } from '../../shared/ui/FormField';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { InvitationDialog } from '../../shared/ui/InvitationDialog';
import { DirtyFormGuard } from '../../shared/ui/DirtyFormGuard';
import { DataList } from '../../shared/ui/DataList';
import { ErrorSummary, focusFirstError } from '../../shared/ui/ErrorSummary';
import { useRead, type Page } from '../courses/queries';
import { Pages, ReadState, useListState } from '../courses/ReadUI';
import { StudentWorkspace } from './StudentWorkspace';
import { SelectField } from '../../shared/ui/SelectField';
import { gradeOptions, type Student, type Invitation } from './api';
import { parseRublesToKopecks } from './pricing';
import styles from '../courses/read.module.css';
import { ChevronRight, UserRoundPlus, Archive, Search, X } from 'lucide-react';
import studentStyles from './students.module.css';
function AddStudent({
  onCreated,
  onClose,
}: {
  onCreated: (data: Invitation) => void;
  onClose: () => void;
}) {
  const [values, set] = useState({
    username: '',
    first_name: '',
    last_name: '',
    email: '',
    school_grade: '',
    lesson_price_rubles: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [pending, busy] = useState(false);
  const [message, setMessage] = useState('');
  const [uncertain, setUncertain] = useState(false);
  const [discard, setDiscard] = useState(false);
  const dirty = Object.values(values).some(Boolean);
  return (
    <>
      <DirtyFormGuard dirty={dirty} />
      <ConfirmDialog
        opened
        title={discard ? 'Отменить создание ученика?' : 'Добавить ученика'}
        confirmLabel={discard ? 'Удалить введённые данные' : 'Создать ученика'}
        pending={pending}
        confirmDisabled={!discard && uncertain}
        onCancel={() => {
          if (discard) setDiscard(false);
          else if (dirty) setDiscard(true);
          else onClose();
        }}
        onConfirm={() => {
          if (discard) {
            onClose();
            return;
          }
          void (async () => {
            if (pending || uncertain) return;
            const invalid = Object.fromEntries(
              Object.entries(values)
                .filter(
                  ([key, value]) =>
                    !['email', 'school_grade', 'lesson_price_rubles'].includes(
                      key,
                    ) && !value.trim(),
                )
                .map(([key]) => [key, 'Заполните поле']),
            );
            if (
              values.email &&
              !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)
            )
              invalid.email = 'Проверьте почту';
            if (!values.school_grade)
              invalid.school_grade = 'Укажите класс ученика';
            let lessonPrice: number | null = null;
            try {
              lessonPrice = parseRublesToKopecks(values.lesson_price_rubles);
            } catch (e) {
              invalid.lesson_price_rubles =
                e instanceof Error ? e.message : 'Проверьте цену занятия';
            }
            setErrors(invalid);
            focusFirstError(invalid);
            if (Object.keys(invalid).length) return;
            busy(true);
            setMessage('');
            try {
              const result = await request<Invitation>('/auth/register', {
                method: 'POST',
                body: {
                  username: values.username,
                  first_name: values.first_name,
                  last_name: values.last_name,
                  email: values.email || null,
                  role: 'student',
                  school_grade: values.school_grade
                    ? Number(values.school_grade)
                    : null,
                  lesson_price_kopecks: lessonPrice,
                },
              });
              onCreated(result);
            } catch (e) {
              if (e instanceof ApiError) {
                setErrors(e.fields);
                focusFirstError(e.fields);
                if (e.status === 409)
                  setMessage(
                    'Логин или почта уже используются. Обратитесь к администратору для подключения существующего ученика.',
                  );
                else if (!e.status || e.status >= 500 || e.status === 401) {
                  setUncertain(true);
                  setMessage(
                    'Не удалось подтвердить создание. Закройте окно и проверьте список своих учеников перед новым созданием.',
                  );
                } else setMessage(e.message);
              }
            } finally {
              busy(false);
            }
          })();
        }}
      >
        {discard ? (
          <p>
            Несохранённые имя, логин и почта будут удалены из формы. Сохранённые
            аккаунты не изменятся.
          </p>
        ) : (
          <Stack>
            <ErrorSummary errors={errors} />
            {(['username', 'first_name', 'last_name', 'email'] as const).map(
              (key) => (
                <FormField
                  key={key}
                  id={key}
                  name={key}
                  label={
                    {
                      username: 'Логин',
                      first_name: 'Имя',
                      last_name: 'Фамилия',
                      email: 'Почта (необязательно)',
                    }[key]
                  }
                  value={values[key]}
                  type={key === 'email' ? 'email' : 'text'}
                  maxLength={key === 'username' ? 255 : 100}
                  error={errors[key]}
                  onChange={(e) =>
                    set({ ...values, [key]: e.currentTarget.value })
                  }
                />
              ),
            )}
            <SelectField
              id="school_grade"
              error={errors.school_grade}
              label="Класс"
              placeholder="Не указан"
              clearable
              data={gradeOptions}
              value={values.school_grade || null}
              onChange={(v) => set({ ...values, school_grade: v || '' })}
            />
            <div>
              <FormField
                id="lesson_price_rubles"
                name="lesson_price_rubles"
                label="Цена занятия, ₽"
                value={values.lesson_price_rubles}
                inputMode="decimal"
                placeholder="Например, 800 или 800,50"
                error={errors.lesson_price_rubles}
                onChange={(e) =>
                  set({ ...values, lesson_price_rubles: e.currentTarget.value })
                }
              />
              <p className={styles.muted}>
                Необязательно. Пустое поле означает, что цена пока неизвестна.
                Новая цена применяется только к новым занятиям.
              </p>
            </div>
            <p role="alert">{message}</p>
          </Stack>
        )}
      </ConfirmDialog>
    </>
  );
}
export function StudentsPage() {
  usePageTitle('Свои ученики');
  const state = useListState();
  const [search, setSearch] = useState(state.params.get('q') || '');
  const [q, setQ] = useState(state.params.get('q') || '');
  const [composing, setComposing] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const [adding, setAdding] = useState(false);
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  useEffect(() => {
    if (composing) return;
    const timer = setTimeout(() => {
      setQ(search.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [search, composing]);
  const rawGrade = state.params.get('school_grade') || '';
  const grade = gradeOptions.includes(rawGrade) ? rawGrade : '';
  const sortOptions = [
    { value: 'attention', label: 'Требуют внимания сначала' },
    { value: 'recent', label: 'Недавно добавленные' },
    { value: 'grade_asc', label: 'Класс: по возрастанию' },
    { value: 'grade_desc', label: 'Класс: по убыванию' },
    { value: 'name', label: 'По имени' },
  ];
  const sort = sortOptions.some((o) => o.value === state.params.get('sort'))
    ? state.params.get('sort')!
    : 'recent';
  const query = useRead<Page<Student>>('/users/students', {
    sort,
    attention: state.params.get('attention') || undefined,
    school_grade: grade || undefined,
    q: q || undefined,
    limit: state.limit,
    offset: state.offset,
  });
  return (
    <div className={studentStyles.studentListPage}>
      <header className={studentStyles.listHeading}>
        <h1>Свои ученики</h1>
        <Group>
          <Button
            leftSection={<UserRoundPlus size={18} aria-hidden="true" />}
            onClick={() => setAdding(true)}
          >
            Добавить ученика
          </Button>
          <Link to="/teacher/archive">
            <Archive size={18} aria-hidden="true" />
            Архив обучения
          </Link>
        </Group>
      </header>
      <div className={studentStyles.filters}>
        <FormField
          className={studentStyles.searchFilter}
          ref={input}
          flex={1}
          leftSection={<Search size={18} aria-hidden="true" />}
          label="Поиск по имени или логину"
          value={search}
          onCompositionStart={() => setComposing(true)}
          onCompositionEnd={() => setComposing(false)}
          onChange={(e) => {
            setSearch(e.currentTarget.value);
            state.update({ offset: 0 });
          }}
          rightSection={
            search ? (
              <Button
                variant="subtle"
                aria-label="Очистить поиск"
                onClick={() => {
                  setSearch('');
                  setQ('');
                  state.update({ offset: 0 });
                  input.current?.focus();
                }}
              >
                <X size={16} aria-hidden="true" />
              </Button>
            ) : undefined
          }
        />
        <SelectField
          label="Класс"
          placeholder="Все"
          clearable
          data={gradeOptions}
          value={grade || null}
          onChange={(v) => state.update({ school_grade: v || '', offset: 0 })}
        />
        <SelectField
          label="Сортировка"
          data={sortOptions}
          value={sort}
          onChange={(v) => state.update({ sort: v || 'recent', offset: 0 })}
        />
        <SelectField
          className={studentStyles.materialsFilter}
          label="Материалы занятий"
          value={state.params.get('attention') || ''}
          data={[
            { value: '', label: 'Все ученики' },
            { value: 'homework', label: 'Без ДЗ' },
            { value: 'lecture', label: 'Без конспекта' },
          ]}
          onChange={(v) => state.update({ attention: v || '', offset: 0 })}
        />
      </div>
      <ReadState query={query}>
        {(data) => (
          <>
            {!data.items.length && (
              <p>
                {q
                  ? 'Ничего не найдено. Очистите поиск.'
                  : grade
                    ? 'В этом классе ученики не найдены. Измените или очистите фильтр класса.'
                    : 'Пока нет учеников. Добавьте первого ученика.'}
              </p>
            )}
            <DataList
              label="Свои ученики"
              rows={data.items}
              rowKey={(s) => String(s.user_id)}
              rowState={{ studentListSearch: state.params.toString() }}
              rowLink={(s) => `/teacher/students/${s.user_id}`}
              renderRow={(s) => (
                <>
                  <span className={studentStyles.identity}>
                    <span className={studentStyles.name}>
                      {s.first_name} {s.last_name}
                    </span>
                    <span className={styles.muted}>{s.username}</span>
                    {((s.missing_homework || 0) > 0 ||
                      (s.missing_lecture || 0) > 0) && (
                      <span className={studentStyles.materialAttention}>
                        {(s.missing_homework || 0) > 0 && (
                          <span>Без ДЗ: {s.missing_homework}</span>
                        )}
                        {(s.missing_lecture || 0) > 0 && (
                          <span>Без конспекта: {s.missing_lecture}</span>
                        )}
                      </span>
                    )}
                  </span>
                  {s.school_grade && (
                    <span
                      className={studentStyles.grade}
                      aria-label={`Класс ${s.school_grade}`}
                    >
                      {s.school_grade}
                    </span>
                  )}
                  <ChevronRight size={20} aria-hidden="true" />
                </>
              )}
            />
            <Pages total={data.total} state={state} />
          </>
        )}
      </ReadState>
      {adding && (
        <AddStudent
          onClose={() => {
            setAdding(false);
            void query.refetch();
          }}
          onCreated={(data) => {
            setAdding(false);
            setInvitation(data);
            void query.refetch();
          }}
        />
      )}
      {invitation && (
        <InvitationDialog
          invitation={invitation}
          onClose={() => setInvitation(null)}
        />
      )}
    </div>
  );
}
export function StudentPage() {
  const { userId = '' } = useParams();
  const location = useLocation();
  const listSearch =
    typeof location.state?.studentListSearch === 'string'
      ? location.state.studentListSearch
      : '';
  const listParams = new URLSearchParams(listSearch);
  const returnParams = new URLSearchParams();
  for (const key of [
    'sort',
    'school_grade',
    'offset',
    'limit',
    'attention',
    'q',
  ]) {
    const value = listParams.get(key);
    if (value) returnParams.set(key, value);
  }
  const query = useRead<Student>(`/users/${encodeURIComponent(userId)}`);
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [pending, busy] = useState(false);
  const [error, setError] = useState('');
  const [unavailable, setUnavailable] = useState(false);
  usePageTitle('Карточка ученика');
  return (
    <>
      <Link
        to={`/teacher/students${returnParams.size ? `?${returnParams}` : ''}`}
      >
        Свои ученики
      </Link>
      <ReadState query={query}>
        {(s) => (
          <>
            <StudentWorkspace
              heading={
                <header className={studentStyles.studentHeading}>
                  <h1>
                    {s.first_name} {s.last_name}
                    {s.school_grade && (
                      <span
                        className={studentStyles.grade}
                        aria-label={`Класс ${s.school_grade}`}
                      >
                        {s.school_grade} класс
                      </span>
                    )}
                  </h1>
                  <p className={styles.muted}>Логин: {s.username}</p>
                </header>
              }
              student={s}
              onStudentRefresh={async () => {
                const result = await query.refetch();
                if (result.error) throw result.error;
              }}
            >
              <details
                className={`${styles.row} ${styles.secondaryDisclosure}`}
              >
                <summary>Приглашение и доступ</summary>
                <Button
                  disabled={unavailable}
                  loading={pending}
                  onClick={() => {
                    if (pending) return;
                    busy(true);
                    setError('');
                    void request<Invitation>('/account_invitations/issue', {
                      method: 'POST',
                      body: { user_id: Number(userId), purpose: 'invite' },
                    })
                      .then((result) => {
                        setInvitation(result);
                        setUnavailable(!result.activation_link);
                      })
                      .catch(() =>
                        setError(
                          'Не удалось получить приглашение. Повторная выдача отменит прежнюю ссылку.',
                        ),
                      )
                      .finally(() => busy(false));
                  }}
                >
                  Выдать новое приглашение до активации
                </Button>
                <p>
                  После активации восстановить доступ может администратор. Общий
                  профиль изменяет сам ученик. Школьный класс также может менять
                  его преподаватель.
                </p>
                <p role="alert">{error}</p>
              </details>
            </StudentWorkspace>
          </>
        )}
      </ReadState>
      {invitation && (
        <InvitationDialog
          invitation={invitation}
          onClose={() => setInvitation(null)}
        />
      )}
    </>
  );
}
