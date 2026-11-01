import { useModalIsolation } from '../lib/modalIsolation';
import { Modal, Button, Group, Text } from '@mantine/core';
export function ConfirmDialog({
  opened,
  onCancel,
  onConfirm,
  title,
  children,
  confirmLabel = 'Подтвердить',
  pending = false,
  error,
  confirmDisabled = false,
  destructive = false,
}: {
  opened: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  title: string;
  children: React.ReactNode;
  confirmLabel?: string;
  pending?: boolean;
  error?: string;
  confirmDisabled?: boolean;
  destructive?: boolean;
}) {
  useModalIsolation(opened);
  return (
    <Modal
      opened={opened}
      zIndex="var(--lgg-z-dialog)"
      onClose={() => {
        if (!pending) onCancel();
      }}
      title={title}
      closeButtonProps={{ 'aria-label': 'Закрыть' }}
      closeOnEscape={!pending}
      closeOnClickOutside={!pending}
    >
      <Text component="div" mb="lg">
        {children}
      </Text>
      {error && (
        <Text role="alert" c="var(--lgg-danger)" mb="md">
          {error}
        </Text>
      )}
      <Group justify="flex-end">
        <Button
          variant="default"
          onClick={onCancel}
          disabled={pending}
          data-autofocus
        >
          Отмена
        </Button>
        <Button
          color={destructive ? 'var(--lgg-danger)' : undefined}
          onClick={onConfirm}
          loading={pending}
          disabled={pending || confirmDisabled}
        >
          {confirmLabel}
        </Button>
      </Group>
    </Modal>
  );
}
