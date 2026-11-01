import { DatePickerInput } from '@mantine/dates';
import { Stack } from '@mantine/core';
import { FormField } from './FormField';
export function DateField({
  label,
  placeholder = 'Выберите дату',
  value,
  onChange,
}: {
  label: string;
  placeholder?: string;
  value: string | null;
  onChange: (value: string | null) => void;
}) {
  return (
    <DatePickerInput
      label={label}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      valueFormat="D MMMM YYYY"
      locale="ru"
      clearable
      clearButtonProps={{
        'aria-label': 'Очистить дату',
        'aria-hidden': false,
        tabIndex: 0,
      }}
      ariaLabels={{
        nextMonth: 'Следующий месяц',
        previousMonth: 'Предыдущий месяц',
        nextYear: 'Следующий год',
        previousYear: 'Предыдущий год',
        nextDecade: 'Следующее десятилетие',
        previousDecade: 'Предыдущее десятилетие',
        monthLevelControl: 'Выбрать месяц',
        yearLevelControl: 'Выбрать год',
      }}
      popoverProps={{
        withinPortal: true,
        position: 'bottom-start',
        middlewares: { flip: true, shift: true },
        transitionProps: { duration: 0 },
      }}
    />
  );
}
export function DateTimeField({
  date,
  time,
  onDateChange,
  onTimeChange,
  error,
  timeId,
}: {
  date: string | null;
  time: string;
  onDateChange: (value: string | null) => void;
  onTimeChange: (value: string) => void;
  error?: string;
  timeId?: string;
}) {
  return (
    <Stack gap="md">
      <DateField label="Дата занятия" value={date} onChange={onDateChange} />
      <FormField
        id={timeId}
        label="Время начала, МСК"
        description="24-часовой формат ЧЧ:ММ"
        placeholder="17:00"
        value={time}
        onChange={(event) => onTimeChange(event.currentTarget.value)}
        inputMode="numeric"
        error={error}
      />
    </Stack>
  );
}
