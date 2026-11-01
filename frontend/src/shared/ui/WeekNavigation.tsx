import { Button, Group } from '@mantine/core';
import { weekStart } from '../lib/datetime';
import styles from './ui.module.css';
export function WeekNavigation({
  week,
  onChange,
}: {
  week: string;
  onChange: (week: string, today: boolean) => void;
}) {
  const start = weekStart(week);
  const offset = start.diff(weekStart(), 'week');
  return (
    <Group
      grow
      gap="xs"
      className={styles.weekNavigation}
      aria-label="Выбор недели"
    >
      {[
        {
          label: 'Предыдущая неделя',
          target: start.subtract(7, 'day'),
          selected: offset < 0,
          today: false,
        },
        {
          label: 'Текущая неделя',
          target: weekStart(),
          selected: offset === 0,
          today: true,
        },
        {
          label: 'Следующая неделя',
          target: start.add(7, 'day'),
          selected: offset > 0,
          today: false,
        },
      ].map(({ label, target, selected, today }) => (
        <Button
          key={label}
          variant={selected ? 'light' : 'default'}
          aria-pressed={selected}
          onClick={() => onChange(target.format('YYYY-MM-DD'), today)}
        >
          {label}
        </Button>
      ))}
    </Group>
  );
}
