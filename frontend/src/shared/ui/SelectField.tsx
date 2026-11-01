import { Select as MantineSelect, type SelectProps } from '@mantine/core';
export function SelectField(props: SelectProps) {
  return (
    <MantineSelect
      attributes={{
        dropdown: {
          role: 'region',
          'aria-label':
            typeof props.label === 'string'
              ? `Варианты: ${props.label}`
              : 'Варианты выбора',
        },
      }}
      nothingFoundMessage="Ничего не найдено"
      clearButtonProps={{
        'aria-label': 'Очистить выбор',
        'aria-hidden': false,
        tabIndex: 0,
      }}
      comboboxProps={{
        withinPortal: true,
        offset: 4,
        position: 'bottom-start',
        middlewares: { flip: true, shift: true },
        transitionProps: { duration: 0 },
      }}
      {...props}
    />
  );
}
