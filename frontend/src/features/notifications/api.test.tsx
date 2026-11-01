import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { targetPath, notificationLabel, useNotices } from './api';
import { request } from '../../shared/api/client';
vi.mock('../auth/session', () => ({
  useSession: () => ({ status: 'ready', user: { id: 7, role: 'student' } }),
}));
vi.mock('../../shared/api/client', () => ({ request: vi.fn() }));
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});
describe('notifications boundaries', () => {
  it('maps only authorized available student targets and keeps unknown objects inert', () => {
    expect(
      targetPath(
        { available: false, object_type: 'homework', object_id: 12 },
        'student',
      ),
    ).toBeUndefined();
    expect(
      targetPath(
        { available: true, object_type: 'lesson', object_id: 12 },
        'student',
      ),
    ).toBe('/student/lessons/12');
    expect(
      targetPath(
        {
          available: true,
          object_type: 'submission',
          object_id: 99,
          homework_id: 13,
        },
        'student',
      ),
    ).toBe('/student/homeworks/13');
    expect(
      targetPath(
        { available: true, object_type: 'submission', object_id: 99 },
        'student',
      ),
    ).toBeUndefined();
    expect(
      targetPath(
        { available: true, object_type: 'lesson', object_id: 12 },
        'teacher',
      ),
    ).toBe('/teacher/lessons/12');
    expect(
      targetPath(
        {
          available: true,
          object_type: 'submission',
          object_id: 99,
          homework_id: 13,
        },
        'teacher',
      ),
    ).toBe('/teacher/review/99?homework_id=13');
    expect(
      targetPath(
        { available: true, object_type: 'submission', object_id: 99 },
        'teacher',
      ),
    ).toBeUndefined();
    expect(notificationLabel('solution_checked')).toBe('Работа проверена');
  });
  it('deduplicates badge consumers, pauses and aborts hidden/offline requests, resumes and cleans up', async () => {
    vi.useFakeTimers();
    let visibility = 'visible';
    let online = true;
    vi.spyOn(document, 'visibilityState', 'get').mockImplementation(
      () => visibility as DocumentVisibilityState,
    );
    vi.spyOn(navigator, 'onLine', 'get').mockImplementation(() => online);
    const signals: AbortSignal[] = [];
    vi.mocked(request).mockImplementation((_path, options) => {
      signals.push(options!.signal!);
      return new Promise(() => {});
    });
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    const hook = renderHook(
      () => {
        useNotices('/notifications/unread');
        useNotices('/notifications/unread');
      },
      { wrapper },
    );
    expect(request).toHaveBeenCalledTimes(1);
    await act(async () => {
      visibility = 'hidden';
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(signals[0].aborted).toBe(true);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(120000);
    });
    expect(request).toHaveBeenCalledTimes(1);
    await act(async () => {
      visibility = 'visible';
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(request).toHaveBeenCalledTimes(2);
    await act(async () => {
      online = false;
      window.dispatchEvent(new Event('offline'));
    });
    expect(signals[1].aborted).toBe(true);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(120000);
    });
    expect(request).toHaveBeenCalledTimes(2);
    await act(async () => {
      online = true;
      window.dispatchEvent(new Event('online'));
    });
    expect(request).toHaveBeenCalledTimes(3);
    hook.unmount();
    expect(signals[2].aborted).toBe(true);
    client.clear();
  });
});

it('polls successful data every60s and refreshes on focus without duplicating consumers', async () => {
  vi.useFakeTimers();
  vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('visible');
  vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
  vi.mocked(request).mockReset().mockResolvedValue({ unread: 2 });
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  const hook = renderHook(
    () => {
      useNotices('/notifications/unread');
      useNotices('/notifications/unread');
    },
    { wrapper },
  );
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1);
  });
  expect(request).toHaveBeenCalledTimes(1);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(60000);
  });
  expect(request).toHaveBeenCalledTimes(2);
  await act(async () => {
    window.dispatchEvent(new Event('focus'));
    await vi.advanceTimersByTimeAsync(1);
  });
  expect(request).toHaveBeenCalledTimes(3);
  hook.unmount();
  client.clear();
});
