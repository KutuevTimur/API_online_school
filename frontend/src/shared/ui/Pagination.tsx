import { Button, Group } from '@mantine/core';
import { SelectField } from './SelectField';
export function Pagination({
  total,
  offset,
  limit,
  onChange,
  label = 'Страницы списка',
}: {
  label?: string;
  total: number;
  offset: number;
  limit: 20 | 50;
  onChange: (offset: number, limit: 20 | 50) => void;
}) {
  if (total <= limit && offset === 0) return null;
  const page = Math.floor(offset / limit) + 1;
  return (
    <nav aria-label={label}>
      <Group gap="sm">
        <Button
          variant="default"
          disabled={offset === 0}
          onClick={() => onChange(Math.max(0, offset - limit), limit)}
        >
          Назад
        </Button>
        <span aria-live="polite">
          {page} из {Math.max(1, Math.ceil(total / limit))}
        </span>
        <Button
          variant="default"
          disabled={offset + limit >= total}
          onClick={() => onChange(offset + limit, limit)}
        >
          Далее
        </Button>
        <SelectField
          label="На странице"
          allowDeselect={false}
          value={String(limit)}
          data={['20', '50']}
          onChange={(value) => onChange(0, value === '50' ? 50 : 20)}
          w={140}
        />
      </Group>
    </nav>
  );
}
