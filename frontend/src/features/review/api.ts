import { request, upload } from '../../shared/api/client';
import type { Answer } from '../../shared/api/files';
import type { components } from '../../shared/api/schema';
export type ReviewItem = components['schemas']['ReviewQueueItemDTO'];
export const reviewAPI = (homeworkId: number, submissionId: number) => ({
  read: () =>
    request<Answer>(`/submissions/${submissionId}`, {
      params: { homework_id: homeworkId },
    }),
  check: (
    version: number,
    grade: number,
    comment: string,
    files: File[] = [],
  ) => {
    if (!files.length)
      return request<Answer>(`/submissions/${submissionId}/teacher`, {
        method: 'PATCH',
        params: { homework_id: homeworkId },
        body: {
          expected_version: version,
          grade,
          teacher_comment: comment || null,
        },
      });
    const body = new FormData();
    body.append('expected_version', String(version));
    body.append('grade', String(grade));
    body.append('teacher_comment', comment);
    for (const file of files) body.append('files', file);
    return upload<Answer>(`/submissions/${submissionId}/review`, body, {
      method: 'PATCH',
      params: { homework_id: homeworkId },
    });
  },
});

export function reviewPath(
  item: Pick<ReviewItem, 'id' | 'homework_id'>,
  search = '',
) {
  const params = new URLSearchParams(search);
  params.delete('file');
  params.delete('condition-file');
  params.delete('review-file');
  params.set('homework_id', String(item.homework_id));
  return `/teacher/review/${item.id}?${params}`;
}
