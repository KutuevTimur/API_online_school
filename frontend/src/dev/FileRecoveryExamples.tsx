import { useState } from 'react';
import { Button, Group, Progress } from '@mantine/core';
import { SelectField } from '../shared/ui/SelectField';
import { ErrorSummary } from '../shared/ui/ErrorSummary';
import { FormField } from '../shared/ui/FormField';
import { ConflictCompare } from '../shared/ui/ConflictCompare';
const examples = {
  processing:
    'Байты отправлены. Обрабатываем файл… Подтверждения сохранения ещё нет.',
  interrupted:
    'Загрузка прервана. Результат неизвестен: перечитайте список перед повтором.',
  quota: 'Превышен размер или квота хранилища. Другие файлы и текст сохранены.',
  forbidden:
    'Нет доступа к материалу. Отправка остановлена; уточните доступ у преподавателя.',
  conflict: 'Ответ на сервере изменился. Локальную версию не перезаписываем.',
  session:
    'Срок сессии истёк. Войдите тем же пользователем; несохранённые файлы остаются только в этой вкладке.',
  validation:
    'Проверьте отмеченное поле. Остальные значения остаются на месте.',
};
export function FileRecoveryExamples() {
  const [kind, setKind] = useState<keyof typeof examples>('interrupted');
  const [title, setTitle] = useState('Локальный ответ');
  const [read, setRead] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  return (
    <details>
      <summary>Состояния файлов · примеры без отправки</summary>
      <h2>Примеры восстановления</h2>
      <p>Искусственные примеры интерфейса. Они не меняют файлы и сессию.</p>
      <SelectField
        label="Пример состояния"
        value={kind}
        allowDeselect={false}
        data={[
          { value: 'processing', label: 'Обработка после 100%' },
          { value: 'interrupted', label: 'Прерванная загрузка' },
          { value: 'quota', label: 'Размер / квота' },
          { value: 'forbidden', label: 'Нет доступа' },
          { value: 'conflict', label: 'Конфликт версий' },
          { value: 'session', label: 'Сессия истекла' },
          { value: 'validation', label: 'Ошибка поля 422' },
        ]}
        onChange={(value) => {
          setKind(value as keyof typeof examples);
          setRead(false);
          setErrors({});
        }}
      />
      <p role="status">{examples[kind]}</p>
      {kind === 'processing' && (
        <Progress value={100} aria-label="Байты отправлены — пример" />
      )}
      {kind === 'interrupted' && (
        <>
          <Button variant="default" onClick={() => setRead(true)}>
            Перечитать список · пример
          </Button>
          {read && (
            <p>
              На сервере: photo-1.webp. В очереди: photo-1.png, photo-2.png.
              Проверьте содержимое перед повтором.
            </p>
          )}
        </>
      )}
      {kind === 'conflict' && (
        <ConflictCompare
          local={<p>{title}</p>}
          server={
            <p>
              {read ? 'Обновлённая серверная версия 3' : 'Серверная версия 2'}
            </p>
          }
          onReload={() => setRead(true)}
        />
      )}
      {kind === 'validation' && (
        <form
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            setErrors({ 'file-example-title': 'Укажите название материала' });
          }}
        >
          <ErrorSummary errors={errors} />
          <FormField
            id="file-example-title"
            label="Название · пример"
            value={title}
            onChange={(event) => setTitle(event.currentTarget.value)}
            error={errors['file-example-title']}
          />
          <Group mt="md">
            <Button type="submit">Показать ошибку поля</Button>
          </Group>
        </form>
      )}
    </details>
  );
}
