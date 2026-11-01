import { describe, it, expect } from 'vitest';
import { quotaBytes, formatBytes, userLabel } from './api';
import { invitationURL } from '../../students/api';
describe('admin security and quota boundaries', () => {
  it('uses decimal MB/GB while preserving exact server byte boundaries', () => {
    expect(quotaBytes('20.97152', 'MB')).toBe(20 * 1024 ** 2);
    expect(quotaBytes('1,5', 'GB')).toBe(1_500_000_000);
    expect(quotaBytes('1099.511627776', 'GB')).toBe(1024 ** 4);
    expect(quotaBytes('32', 'MB')).toBe(32_000_000);
    expect(quotaBytes('0.1', 'GB')).toBe(100_000_000);
    for (const value of [
      '',
      '0',
      '-1',
      '20.971519',
      '1099511.627777',
      '1e3',
      'Infinity',
      '20.9715201',
      '1.0000000001',
    ])
      expect(quotaBytes(value, 'MB')).toBeNull();
    expect(quotaBytes('1099.511627777', 'GB')).toBeNull();
    expect(quotaBytes('0.020971519', 'GB')).toBeNull();
  });
  it('shows readable decimal sizes without rounding a present small file to zero', () => {
    expect(formatBytes(0)).toBe('0 Б');
    expect(formatBytes(10)).toBe('10 Б');
    expect(formatBytes(1500)).toBe('1,5 КБ');
    expect(formatBytes(1_000_000)).toBe('1 МБ');
    expect(formatBytes(1_500_000_000)).toBe('1,5 ГБ');
  });
  it('separates reset and activation links, rejecting injected origins, query tokens and stale purposes', () => {
    expect(
      invitationURL(
        '/reset-password#token=synthetic_1',
        'https://school.example',
        'reset',
      ),
    ).toBe('https://school.example/reset-password#token=synthetic_1');
    for (const raw of [
      '/activate#token=x',
      'https://evil.example/reset-password#token=x',
      '/reset-password?token=x',
      '/reset-password#token=x&next=y',
      null,
    ])
      expect(invitationURL(raw, 'https://school.example', 'reset')).toBeNull();
  });
  it('distinguishes namesakes with username without inventing a profile', () => {
    expect(
      userLabel({ first_name: null, last_name: null, username: 'synthetic' }),
    ).toBe(' · synthetic');
    expect(
      userLabel({
        first_name: 'Имя',
        last_name: 'Фамилия',
        username: 'unique',
      }),
    ).toBe('Имя Фамилия · unique');
  });
});
