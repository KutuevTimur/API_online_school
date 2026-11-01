import { useQuery } from '@tanstack/react-query';
import { request, type RequestOptions } from '../../shared/api/client';
import type { components } from '../../shared/api/schema';
export type Course = components['schemas']['CoursesResponseDTO'];
export type Lesson = components['schemas']['LessonResponseDTO'];
export type Homework = components['schemas']['HomeworkResponseDTO'];
export type Lecture = components['schemas']['LectureResponseDTO'];
export type Answer = components['schemas']['HomeworkSubmissionResponseDTO'];
export type Recipient = components['schemas']['LessonRecipientResponseDTO'];
export type Page<T> = { items: T[]; total: number };
export const readKey = (path: string, params: RequestOptions['params'] = {}) =>
  ['student-read', path, params] as const;
export function useRead<T>(
  path: string,
  params: RequestOptions['params'] = {},
  enabled = true,
  refreshMs: number | false = false,
) {
  return useQuery({
    networkMode: 'always',
    queryKey: readKey(path, params),
    queryFn: ({ signal }) => request<T>(path, { params, signal }),
    enabled,
    refetchInterval: () =>
      document.visibilityState === 'visible' && navigator.onLine
        ? refreshMs
        : false,
  });
}
