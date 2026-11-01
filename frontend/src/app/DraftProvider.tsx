import { createContext, useEffect, useState, type ReactNode } from 'react';
import { session } from '../features/auth/session';
export const DraftContext = createContext(new Map<string, unknown>());
export function DraftProvider({ children }: { children: ReactNode }) {
  const [drafts] = useState(() => new Map<string, unknown>());
  useEffect(
    () =>
      session.cleanup(() => {
        for (const value of drafts.values())
          if (value instanceof URL) URL.revokeObjectURL(value.href);
          else if (
            value &&
            typeof value === 'object' &&
            'dispose' in value &&
            typeof value.dispose === 'function'
          )
            value.dispose();
        drafts.clear();
      }),
    [drafts],
  );
  return (
    <DraftContext.Provider value={drafts}>{children}</DraftContext.Provider>
  );
}
