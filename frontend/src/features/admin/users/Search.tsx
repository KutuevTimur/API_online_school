import { useEffect, useRef, useState } from 'react';
import { Button } from '@mantine/core';
import { FormField } from '../../../shared/ui/FormField';
export function usePrivateSearch() {
  const [text, setText] = useState('');
  const [q, setQ] = useState('');
  const [composing, setComposing] = useState(false);
  useEffect(() => {
    if (composing) return;
    const timer = setTimeout(() => setQ(text.trim()), 300);
    return () => clearTimeout(timer);
  }, [text, composing]);
  return { text, q, setText, setQ, setComposing };
}
export function PrivateSearch({
  search,
  label,
  onChange,
}: {
  search: ReturnType<typeof usePrivateSearch>;
  label: string;
  onChange?: () => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <FormField
      ref={ref}
      label={label}
      value={search.text}
      maxLength={100}
      onCompositionStart={() => search.setComposing(true)}
      onCompositionEnd={() => search.setComposing(false)}
      onChange={(e) => {
        search.setText(e.currentTarget.value);
        onChange?.();
      }}
      rightSection={
        search.text ? (
          <Button
            variant="subtle"
            aria-label={`Очистить: ${label}`}
            onClick={() => {
              search.setText('');
              search.setQ('');
              onChange?.();
              ref.current?.focus();
            }}
          >
            ×
          </Button>
        ) : undefined
      }
    />
  );
}
