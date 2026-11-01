import { useState } from 'react';
import { useSearchParams } from 'react-router';
import { Button, Group, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import { LinkButton } from '../shared/ui/LinkButton';
import { AppShell, type Role } from '../shared/ui/AppShell';
import { FormField, TextAreaField } from '../shared/ui/FormField';
import { SelectField } from '../shared/ui/SelectField';
import { DateTimeField } from '../shared/ui/DateTimeField';
import { ConfirmDialog } from '../shared/ui/ConfirmDialog';
import { AsyncState, type AsyncKind } from '../shared/ui/AsyncState';
import { StatusBadge } from '../shared/ui/StatusBadge';
import { ErrorSummary } from '../shared/ui/ErrorSummary';
import { Pagination } from '../shared/ui/Pagination';
import { DataList } from '../shared/ui/DataList';
import { useFeedback } from '../shared/ui/FeedbackProvider';
import { usePageTitle } from '../app/router';
import { moscowToUtc } from '../shared/lib/time';
import styles from '../shared/ui/ui.module.css';
import { StudentPreview } from './StudentPreview';
export function Gallery() {
  usePageTitle('Пример кабинета');
  const [params, setParams] = useSearchParams();
  const raw = params.get('role');
  const role: Role = raw === 'teacher' || raw === 'admin' ? raw : 'student';
  const [selected, setSelected] = useState<string | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [time, setTime] = useState('17:00');
  const [dialog, setDialog] = useState(false);
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState<AsyncKind>('empty');
  const feedback = useFeedback();
  const offset = Math.max(0, Number(params.get('offset')) || 0);
  const limit = params.get('limit') === '50' ? 50 : 20;
  const form = useForm({
    initialValues: { title: '', description: '' },
    validate: { title: (value) => (value.trim() ? null : 'Укажите название') },
  });
  const errors = Object.fromEntries(
    Object.entries(form.errors).map(([key, value]) => [key, String(value)]),
  );
  return (
    <AppShell role={role} preview>
      <StudentPreview />
      <LinkButton to="/__ui/files" variant="default">
        Файлы · техническая галерея
      </LinkButton>
      <details className={styles.technical} id="technical-components">
        <summary>Техническая галерея компонентов</summary>
        <Stack gap={28}>
          <div>
            <h2>Компоненты LGG</h2>
            <p className={styles.muted}>
              Образцы интерфейса · искусственные данные. Это ещё не учебный
              кабинет.
            </p>
            <SelectField
              label="Навигация роли — только образец"
              value={role}
              allowDeselect={false}
              data={[
                { value: 'student', label: 'Ученик' },
                { value: 'teacher', label: 'Преподаватель' },
                { value: 'admin', label: 'Администратор' },
              ]}
              onChange={(value) => setParams({ role: value || 'student' })}
              maw={340}
            />
            {params.get('section') && (
              <p role="status">
                Выбран раздел: {params.get('section')}. Его содержимое появится
                на следующих этапах.
              </p>
            )}
          </div>
          <div className={styles.grid}>
            <section className={`${styles.panel} ${styles.lesson}`}>
              <h2>Занятие → задание → результат</h2>
              <p>
                Голубая поверхность объединяет занятие и работу с ответом.
                Основное действие остаётся на виду.
              </p>
              <Stack gap="md">
                <StatusBadge status="draft" />
                <StatusBadge status="submitted" />
                <div className={styles.actions}>
                  <Button onClick={() => setDialog(true)}>
                    Открыть подтверждение
                  </Button>
                  <Button
                    variant="default"
                    loading={busy}
                    disabled={busy}
                    onClick={() => {
                      setBusy(true);
                      window.setTimeout(() => {
                        setBusy(false);
                        feedback('Пример завершён. Данные не отправлялись.');
                      }, 1000);
                    }}
                  >
                    Проверить ожидание
                  </Button>
                </div>
              </Stack>
            </section>
            <section className={`${styles.panel} ${styles.mint}`}>
              <h2>Понятный результат</h2>
              <StatusBadge status="checked" />
              <p>
                Статус подписан словами. Результат и следующее действие видны
                без подсказки.
              </p>
              <LinkButton variant="default" to="/login">
                Вернуться ко входу
              </LinkButton>
            </section>
          </div>
          <div className={styles.grid}>
            <section className={styles.panel}>
              <h2>Поля и проверка</h2>
              <form
                noValidate
                onSubmit={form.onSubmit(() =>
                  feedback('Поля проверены. Это пример без отправки.'),
                )}
              >
                <Stack gap="md">
                  <ErrorSummary errors={errors} />
                  <FormField
                    id="title"
                    label="Название занятия"
                    required
                    {...form.getInputProps('title')}
                  />
                  <TextAreaField
                    id="description"
                    label="Описание"
                    description="Необязательное поле"
                    {...form.getInputProps('description')}
                  />
                  <SelectField
                    label="Курс"
                    placeholder="Выберите курс"
                    searchable
                    clearable
                    value={selected}
                    onChange={setSelected}
                    data={[
                      'Математика',
                      'Геометрия — длинное название курса для проверки переноса и открытого списка',
                      'Физика',
                      'Русский язык',
                    ]}
                  />
                  <DateTimeField
                    date={date}
                    time={time}
                    onDateChange={setDate}
                    onTimeChange={setTime}
                    error={
                      time && !moscowToUtc(date || '2026-10-16', time)
                        ? 'Введите время от 00:00 до 23:59'
                        : undefined
                    }
                  />
                  <Button type="submit">Проверить поля</Button>
                </Stack>
              </form>
            </section>
            <section className={styles.panel}>
              <h2>Состояния и возврат</h2>
              <SelectField
                label="Состояние блока"
                value={state}
                allowDeselect={false}
                data={[
                  { value: 'loading', label: 'Загрузка' },
                  { value: 'refresh', label: 'Обновление' },
                  { value: 'empty', label: 'Пусто' },
                  { value: 'no-results', label: 'Нет результатов' },
                  { value: 'error', label: 'Ошибка' },
                  { value: 'offline', label: 'Нет связи' },
                  { value: 'readonly', label: 'Архив' },
                ]}
                onChange={(value) => setState(value as AsyncKind)}
              />
              <AsyncState
                kind={state}
                onRetry={
                  ['error', 'offline', 'no-results'].includes(state)
                    ? () => setState('empty')
                    : undefined
                }
              />
              <Group>
                <LinkButton to="/missing-material" variant="default">
                  Проверить 404
                </LinkButton>
                <LinkButton to="/403" variant="default">
                  Проверить 403
                </LinkButton>
              </Group>
            </section>
          </div>
          <section className={styles.panel}>
            <h2>Список и страницы</h2>
            <DataList
              label="Образцы материалов"
              rows={[
                {
                  id: 'example',
                  name: 'Материал с длинным названием, которое остаётся доступным на телефоне',
                },
              ]}
              rowKey={(row) => row.id}
              columns={[
                { label: 'Название', render: (row) => row.name },
                {
                  label: 'Статус',
                  render: () => <StatusBadge status="archived" />,
                },
              ]}
            />
            <Pagination
              total={65}
              offset={offset}
              limit={limit}
              onChange={(next, size) => {
                const updated = new URLSearchParams(params);
                updated.set('offset', String(next));
                updated.set('limit', String(size));
                setParams(updated);
              }}
            />
          </section>
        </Stack>
      </details>
      <ConfirmDialog
        opened={dialog}
        onCancel={() => setDialog(false)}
        onConfirm={() => {
          setDialog(false);
          feedback('Подтверждение закрыто. Это пример без записи.');
        }}
        title="Подтвердить действие в примере"
        confirmLabel="Подтвердить пример"
      >
        Изменения не отправляются на сервер. «Отмена» закрывает окно и
        возвращает фокус.
      </ConfirmDialog>
    </AppShell>
  );
}
