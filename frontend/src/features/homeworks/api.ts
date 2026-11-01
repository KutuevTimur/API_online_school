import { request } from '../../shared/api/client';
import { answerAdapter, type Answer } from '../../shared/api/files';
import type { Page } from '../courses/queries';
export const attempts = (id: number, signal?: AbortSignal) =>
  request<Page<Answer>>(`/homeworks/${id}/submissions`, {
    params: { limit: 20, offset: 0 },
    signal,
  });
export function saveText(homeworkId: number, text: string, answer?: Answer) {
  const body = new FormData();
  body.append('text_content', text);
  if (answer) body.append('expected_version', String(answer.version));
  return request<Answer>(
    answer
      ? `/submissions/${answer.id}/student`
      : `/homeworks/${homeworkId}/submissions`,
    {
      method: answer ? 'PATCH' : 'POST',
      params: answer ? { homework_id: homeworkId } : {},
      body,
    },
  );
}
export function adapter(id: number, current: () => Answer) {
  const target = () => answerAdapter(id, current().id);
  return {
    read: async () => {
      // Direct working id comes from homework, independent of history pagination.
      const detail = await request<{ working_submission_id: number | null }>(
        `/homeworks/${id}`,
      );
      if (!detail.working_submission_id)
        return {
          ...current(),
          id: 0,
          version: 1,
          files: [],
          text_content: null,
        };
      return answerAdapter(id, detail.working_submission_id).read();
    },
    append: (...args: Parameters<ReturnType<typeof answerAdapter>['append']>) =>
      target().append(...args),
    replace: (
      ...args: Parameters<ReturnType<typeof answerAdapter>['replace']>
    ) => target().replace(...args),
    remove: (...args: Parameters<ReturnType<typeof answerAdapter>['remove']>) =>
      target().remove(...args),
  };
}
