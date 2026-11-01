import type { components } from '../../../shared/api/schema';
export type AdminUser = components['schemas']['AdminUserResponseDTO'];
export type AdminLink = components['schemas']['AdminTeacherStudentResponseDTO'];
export type Quota = components['schemas']['StorageQuotaResponse'];
export const roles = [
  { value: 'teacher', label: 'Преподаватель' },
  { value: 'student', label: 'Ученик' },
  { value: 'admin', label: 'Администратор' },
];
export const userLabel = (
  u: Pick<AdminUser, 'first_name' | 'last_name' | 'username'>,
) => `${[u.first_name, u.last_name].filter(Boolean).join(' ')} · ${u.username}`;
export function quotaBytes(value: string, unit: 'MB' | 'GB'): number | null {
  const match = /^(\d+)(?:[.,](\d{1,9}))?$/.exec(value.trim());
  if (!match) return null;
  const fraction = match[2] || '';
  const divisor = 10n ** BigInt(fraction.length);
  const numerator =
    BigInt(match[1] + fraction) * (unit === 'MB' ? 1000000n : 1000000000n);
  if (numerator % divisor !== 0n) return null;
  const bytes = Number(numerator / divisor);
  return Number.isSafeInteger(bytes) &&
    bytes >= 20 * 1024 ** 2 &&
    bytes <= 1024 ** 4
    ? bytes
    : null;
}
export function formatBytes(bytes: number): string {
  const units = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
  const index =
    bytes > 0 ? Math.min(4, Math.floor(Math.log(bytes) / Math.log(1000))) : 0;
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 3 }).format(bytes / 1000 ** index)} ${units[index]}`;
}
