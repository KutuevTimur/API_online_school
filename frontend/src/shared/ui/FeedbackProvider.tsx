import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { ActionIcon, Button } from '@mantine/core';
import { X } from 'lucide-react';
type FeedbackOptions = {
  durationMs?: number;
  expiresAt?: number;
  action?: { label: string; run: () => Promise<void> };
};
const FeedbackContext = createContext<
  (message: string, options?: FeedbackOptions) => void
>(() => {});
export const useFeedback = () => useContext(FeedbackContext);
export function FeedbackProvider({ children }: { children: ReactNode }) {
  const [notice, setNotice] = useState<{
    message: string;
    options?: FeedbackOptions;
  } | null>(null);
  const [paused, setPaused] = useState(false);
  const [pending, setPending] = useState(false);
  const current = useRef(0);
  const actionBusy = useRef(false);
  const show = useCallback((message: string, options?: FeedbackOptions) => {
    current.current += 1;
    actionBusy.current = false;
    setPending(false);
    setNotice(message ? { message, options } : null);
  }, []);
  useEffect(() => {
    if (!notice?.options?.action || !notice.options.expiresAt || pending)
      return;
    const timer = window.setTimeout(
      () =>
        setNotice((value) =>
          value === notice ? { message: notice.message } : value,
        ),
      Math.max(0, notice.options.expiresAt - Date.now()),
    );
    return () => window.clearTimeout(timer);
  }, [notice, pending]);
  useEffect(() => {
    if (!notice || paused || pending) return;
    const timer = window.setTimeout(
      () => setNotice(null),
      notice.options?.durationMs ?? 4500,
    );
    return () => window.clearTimeout(timer);
  }, [notice, paused, pending]);
  return (
    <FeedbackContext.Provider value={show}>
      {children}
      {notice && (
        <div
          className="feedback"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
          onFocus={() => setPaused(true)}
          onBlur={() => setPaused(false)}
        >
          <span role="status" aria-live="polite">
            {notice.message}
          </span>
          {notice.options?.action && (
            <Button
              variant="subtle"
              loading={pending}
              disabled={pending}
              onClick={() => {
                if (pending || actionBusy.current) return;
                actionBusy.current = true;
                const revision = current.current;
                setPending(true);
                void notice
                  .options!.action!.run()
                  .then(() => {
                    if (revision === current.current)
                      setNotice({ message: 'Предыдущее действие отменено' });
                  })
                  .catch((e: unknown) => {
                    if (revision === current.current)
                      setNotice({
                        message:
                          e instanceof Error
                            ? e.message
                            : 'Не удалось подтвердить возврат. Обновите расписание.',
                      });
                  })
                  .finally(() => {
                    if (revision === current.current) {
                      actionBusy.current = false;
                      setPending(false);
                    }
                  });
              }}
            >
              {notice.options.action.label}
            </Button>
          )}
          <ActionIcon
            size={44}
            variant="subtle"
            color="var(--lgg-success)"
            aria-label="Закрыть сообщение"
            disabled={pending}
            onClick={() => {
              setNotice(null);
              setPaused(false);
            }}
          >
            <X size={18} aria-hidden="true" />
          </ActionIcon>
        </div>
      )}
    </FeedbackContext.Provider>
  );
}
