import { describe, it, expect, vi } from 'vitest';
import {
  execute,
  receipt,
  provisional,
  accessLabel,
  type Booking,
} from './api';
import { request } from '../../shared/api/client';
vi.mock('../../shared/api/client', () => ({ request: vi.fn() }));
describe('booking typed API', () => {
  it('keeps one operation id and browser guard on an explicit mutation', async () => {
    await execute(
      {
        path: '/teacher-planning/bookings/id/materialize',
        action: 'booking_materialize',
        body: { expected_revision: 2 },
      },
      'stable-id',
    );
    expect(request).toHaveBeenCalledWith(
      '/teacher-planning/bookings/id/materialize',
      expect.objectContaining({
        method: 'POST',
        body: { expected_revision: 2, operation_id: 'stable-id' },
        headers: { 'X-LGG-Request': 'browser' },
      }),
    );
    await receipt('stable-id', 'booking_materialize');
    expect(request).toHaveBeenLastCalledWith(
      '/users/me/integrations/vk/operations/stable-id',
      { params: { action: 'booking_materialize' } },
    );
  });
  it('replaces the provisional row only when the same materialized lesson is readable', () => {
    const rows = [
      { booking_id: 'a', status: 'confirmed', lesson_id: null },
      { booking_id: 'b', status: 'confirmed', lesson_id: 3 },
      { booking_id: 'c', status: 'cancelled', lesson_id: null },
    ] as Booking[];
    expect(provisional(rows, []).map((b) => b.booking_id)).toEqual(['a', 'b']);
    expect(provisional(rows, [3]).map((b) => b.booking_id)).toEqual(['a']);
  });
  it('separates access and booking status', () => {
    expect(accessLabel('unresolved')).toBe('Кабинет не подключён');
    expect(accessLabel('active')).toBe('Кабинет подключён');
    expect(accessLabel('blocked')).toContain('архиве');
  });
});
