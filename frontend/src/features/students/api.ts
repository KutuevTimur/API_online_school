import type { components } from '../../shared/api/schema';
export type Student = components['schemas']['MinimalProfileResponseDTO'] &
  Partial<
    Pick<
      components['schemas']['TeacherStudentProfileResponseDTO'],
      'missing_homework' | 'missing_lecture'
    >
  >;
export type Invitation = components['schemas']['InvitationResponse'];
export type Membership = components['schemas']['StudentCourseResponseDTO'];
export function invitationURL(
  link: string | null | undefined,
  origin: string,
  purpose: 'invite' | 'reset' = 'invite',
): string | null {
  const route = purpose === 'reset' ? 'reset-password' : 'activate';
  if (!link || !new RegExp(`^/${route}#token=[A-Za-z0-9_-]+$`).test(link))
    return null;
  let base: URL;
  try {
    base = new URL(origin);
  } catch {
    return null;
  }
  if (
    !['http:', 'https:'].includes(base.protocol) ||
    base.username ||
    base.password
  )
    return null;
  return new URL(link, base.origin).href;
}
export function courseSlug(name: string) {
  const base =
    name
      .toLowerCase()
      .replace(/[^a-z0-9а-яё]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 60) || 'course';
  return `${base}-${crypto.randomUUID().slice(0, 8)}`;
}

export function activeMembership(member: Membership, now = Date.now()) {
  return (
    !member.is_deleted &&
    !member.access_ended_at &&
    !member.history_revoked &&
    new Date(member.started_at).getTime() <= now &&
    (!member.expires_at || new Date(member.expires_at).getTime() > now)
  );
}

export const gradeOptions = Array.from({ length: 11 }, (_, i) => String(i + 1));
export function studentLabel(
  student: Pick<Student, 'first_name' | 'last_name' | 'school_grade'>,
) {
  return `${student.first_name} ${student.last_name}${student.school_grade ? ` · ${student.school_grade}` : ''}`;
}
