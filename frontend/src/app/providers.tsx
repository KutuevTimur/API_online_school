import { MantineProvider } from '@mantine/core';
import { DatesProvider } from '@mantine/dates';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import 'dayjs/locale/ru';
import { theme, tokens } from './theme';
import { ApiError } from '../shared/api/error';
import { useEffect } from 'react';
import { session } from '../features/auth/session';
import { DraftProvider } from './DraftProvider';
import { FeedbackProvider } from '../shared/ui/FeedbackProvider';
const client = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (count, error) =>
        count < 1 &&
        (!(error instanceof ApiError) ||
          error.kind === 'network' ||
          error.status >= 500),
      staleTime: 30000,
    },
  },
});
export function Providers({ children }: { children: ReactNode }) {
  useEffect(() => session.cleanup(() => client.clear()), []);
  return (
    <MantineProvider
      theme={theme}
      forceColorScheme="light"
      cssVariablesResolver={() => ({
        variables: {
          '--mantine-color-dimmed': tokens.muted,
          '--mantine-color-placeholder': tokens.muted,
          '--mantine-color-error': tokens.danger,
        },
        light: { '--mantine-color-error': tokens.danger },
        dark: {},
      })}
    >
      <DatesProvider
        settings={{ locale: 'ru', firstDayOfWeek: 1, weekendDays: [0, 6] }}
      >
        <QueryClientProvider client={client}>
          <DraftProvider>
            <FeedbackProvider>{children}</FeedbackProvider>
          </DraftProvider>
        </QueryClientProvider>
      </DatesProvider>
    </MantineProvider>
  );
}
