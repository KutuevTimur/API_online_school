import { apiUrl, request, upload } from './client';
import type { components } from './schema';
export type FileDescriptor = components['schemas']['FileDescriptorDTO'];
export type Answer = components['schemas']['HomeworkSubmissionResponseDTO'];
export const MiB = 1024 * 1024;
export const acceptedFiles = '.pdf,.jpg,.jpeg,.png,.webp,.heic,.heif';
export function validateSelection(
  file: File,
  count: number,
  bytes: number,
): string | undefined {
  if (count >= 10) return 'Можно прикрепить не более 10 файлов';
  if (!/\.(pdf|jpe?g|png|webp|heic|heif)$/i.test(file.name))
    return 'Выберите PDF или фото JPEG, PNG, WebP, HEIC';
  if (!file.size) return 'Файл пуст';
  if (file.size > 20 * MiB) return 'Размер файла больше 20 МиБ';
  if (bytes + file.size > 100 * MiB)
    return 'Общий размер исходников больше 100 МиБ';
}
// Descriptors may contain a query, but may never select a different origin or API namespace.
export function fileTarget(raw: string) {
  if (!raw.startsWith('/') || raw.startsWith('//') || /[\\#]/.test(raw))
    throw new Error('Недопустимый адрес файла');
  const [path, query = ''] = raw.split('?');
  apiUrl(path);
  const params = Object.fromEntries(new URLSearchParams(query));
  if (
    Object.keys(params).some(
      (key) => !['homework_id', 'lesson_id', 'student_user_id'].includes(key),
    )
  )
    throw new Error('Недопустимые параметры файла');
  return { path, params };
}
export function fetchFile(
  file: FileDescriptor,
  signal: AbortSignal,
  maxBytes = 20 * MiB,
) {
  const { path, params } = fileTarget(file.download_url);
  return request<Blob>(path, { params, response: 'blob', signal, maxBytes });
}
export function answerFiles(answer: Answer): FileDescriptor[] {
  return answer.files.flatMap((item) => (item.file ? [item.file] : []));
}
export function answerAdapter(homeworkId: number, submissionId: number) {
  const params = { homework_id: homeworkId };
  const path = `/submissions/${submissionId}`;
  return {
    read: () => request<Answer>(path, { params }),
    append: (
      file: File,
      version: number,
      signal: AbortSignal,
      onProgress: (loaded: number, total: number | null) => void,
    ) => {
      const body = new FormData();
      body.append('files', file);
      body.append('expected_version', String(version));
      return upload<Answer>(`${path}/student`, body, {
        params,
        method: 'PATCH',
        signal,
        onProgress,
      });
    },
    replace: (
      id: number,
      file: File,
      version: number,
      signal: AbortSignal,
      onProgress: (loaded: number, total: number | null) => void,
    ) => {
      const body = new FormData();
      body.append('file', file);
      body.append('expected_version', String(version));
      return upload<Answer>(`${path}/files/${id}`, body, {
        params,
        method: 'PUT',
        signal,
        onProgress,
      });
    },
    remove: (id: number, version: number) =>
      request<Answer>(`${path}/files/${id}`, {
        method: 'DELETE',
        params: { ...params, expected_version: version },
      }),
  };
}
export type UploadAdapter = ReturnType<typeof answerAdapter>;
