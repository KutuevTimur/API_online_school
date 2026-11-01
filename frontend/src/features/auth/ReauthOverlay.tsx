import { Modal } from '@mantine/core';
import { useSession } from './session';
import { LoginPage } from './LoginPage';
import { useModalIsolation } from '../../shared/lib/modalIsolation';
export function ReauthOverlay() {
  const auth = useSession();
  const opened = !!auth.reauth;
  useModalIsolation(opened);
  return (
    <Modal
      opened={opened}
      onClose={() => {}}
      withCloseButton={false}
      closeOnEscape={false}
      closeOnClickOutside={false}
      title="Войдите снова"
      zIndex="var(--lgg-z-reauth)"
    >
      <LoginPage reauth embedded />
    </Modal>
  );
}
