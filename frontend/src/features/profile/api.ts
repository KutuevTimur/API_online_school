import type { components } from '../../shared/api/schema';
export type PublicProfile = components['schemas']['PublicProfileResponseDTO'];
export type MinimalProfile = components['schemas']['MinimalProfileResponseDTO'];
export type Account = components['schemas']['UserResponse'];
export function normalizeProfile(data: PublicProfile | MinimalProfile) {
  if ('user_id' in data)
    return {
      id: data.user_id,
      username: data.username,
      email: null,
      first_name: data.first_name ?? '',
      last_name: data.last_name ?? '',
      middle_name: '',
      avatar_path: data.avatar_path,
      editable: false,
    };
  const profile = data.student || data.teacher;
  return {
    id: data.id,
    username: data.username ?? '',
    email: data.email ?? null,
    first_name: profile?.first_name ?? '',
    last_name: profile?.last_name ?? '',
    middle_name: profile?.middle_name ?? '',
    avatar_path: profile?.avatar_path,
    editable: !!profile,
  };
}
export type Profile = ReturnType<typeof normalizeProfile>;
export function validateProfile(values: Record<string, string>) {
  const errors: Record<string, string> = {};
  if (!values.username.trim() || values.username.length > 255)
    errors.username = 'Логин: от 1 до 255 символов';
  if (values.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email))
    errors.email = 'Проверьте адрес почты';
  for (const key of ['first_name', 'last_name', 'middle_name'])
    if (values[key].length > 255) errors[key] = 'Не больше 255 символов';
  return errors;
}
