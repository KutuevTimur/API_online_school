import { useBeforeUnload, useBlocker } from 'react-router';
import { useCallback, useContext, useEffect, useId } from 'react';
import { DraftContext } from '../../app/DraftProvider';
import { ConfirmDialog } from './ConfirmDialog';
export function DirtyFormGuard({
  dirty,
  onDiscard,
  allowPreviewQuery = false,
}: {
  dirty: boolean;
  onDiscard?: () => void;
  allowPreviewQuery?: boolean;
}) {
  const drafts = useContext(DraftContext);
  const key = 'dirty-guard:' + useId();
  useEffect(() => {
    if (dirty) drafts.set(key, { dirty: true });
    else drafts.delete(key);
    return () => {
      drafts.delete(key);
    };
  }, [dirty, drafts, key]);
  const blocker = useBlocker(({ currentLocation, nextLocation }) => {
    if (!dirty) return false;
    if (
      allowPreviewQuery &&
      currentLocation.pathname === nextLocation.pathname
    ) {
      const before = new URLSearchParams(currentLocation.search);
      const after = new URLSearchParams(nextLocation.search);
      for (const key of [
        'file',
        'condition-file',
        'review-file',
        'material-file',
        'file-owner',
      ]) {
        before.delete(key);
        after.delete(key);
      }
      if (before.toString() === after.toString()) return false;
    }
    return true;
  });
  useBeforeUnload(
    useCallback(
      (event) => {
        if (dirty) {
          event.preventDefault();
          event.returnValue = '';
        }
      },
      [dirty],
    ),
  );
  return (
    <ConfirmDialog
      opened={blocker.state === 'blocked'}
      title="Уйти без сохранения?"
      confirmLabel="Уйти без сохранения"
      onCancel={() => blocker.reset?.()}
      onConfirm={() => {
        onDiscard?.();
        blocker.proceed?.();
      }}
    >
      Несохранённые файлы и текст в этой вкладке будут потеряны. «Отмена» вернёт
      к работе.
    </ConfirmDialog>
  );
}
