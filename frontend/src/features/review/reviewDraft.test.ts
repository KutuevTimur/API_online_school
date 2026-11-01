import { describe, it, expect, vi } from 'vitest';
import type { Answer } from '../../shared/api/files';
import { ApiError } from '../../shared/api/error';
import { ReviewDraft } from './reviewDraft';
const answer = {
  id: 12,
  homework_id: 5,
  version: 3,
  status: 'submitted',
  text_content: 'old',
  files: [],
  grade: null,
} as unknown as Answer;
const setup = () => {
  const api = { read: vi.fn(), check: vi.fn() };
  return { api, model: new ReviewDraft(answer, api) };
};
describe('final review of an exact answer', () => {
  it('requires an explicit grade, accepts 0, sends the opened version', async () => {
    const { model, api } = setup();
    await model.check();
    expect(api.check).not.toHaveBeenCalled();
    expect(model.snapshot().error).toContain('Выберите оценку');
    model.edit('0', 'Проверь знаки');
    api.check.mockResolvedValue({
      ...answer,
      status: 'checked',
      version: 4,
      grade: 0,
    });
    await model.check();
    expect(api.check).toHaveBeenCalledWith(3, 0, 'Проверь знаки');
    expect(model.snapshot().answer.grade).toBe(0);
    expect(model.dirty).toBe(false);
    await model.check();
    expect(api.check).toHaveBeenCalledTimes(1);
  });
  it('allows 5 without comment and blocks duplicate pending submit', async () => {
    const { model, api } = setup();
    model.edit('5', '');
    let resolve!: (a: Answer) => void;
    api.check.mockReturnValue(
      new Promise<Answer>((r) => {
        resolve = r;
      }),
    );
    const first = model.check();
    await model.check();
    expect(api.check).toHaveBeenCalledTimes(1);
    resolve({ ...answer, status: 'checked', grade: 5 });
    await first;
    expect(model.snapshot().answer.grade).toBe(5);
  });
  it('preserves grading draft on conflict and requires explicit opening of changed answer', async () => {
    const { model, api } = setup();
    model.edit('2', 'Мой комментарий');
    api.check.mockRejectedValue(new ApiError(409, 'conflict'));
    await model.check();
    await model.check();
    expect(api.check).toHaveBeenCalledTimes(1);
    api.read.mockResolvedValue({ ...answer, version: 4, text_content: 'new' });
    await model.refresh();
    expect(model.snapshot()).toMatchObject({
      grade: '2',
      comment: 'Мой комментарий',
      answer: { version: 3 },
      latest: { version: 4 },
    });
    await model.check();
    expect(api.check).toHaveBeenCalledTimes(1);
    model.openLatest();
    api.check.mockResolvedValue({
      ...answer,
      version: 5,
      status: 'checked',
      grade: 2,
    });
    await model.check();
    expect(api.check).toHaveBeenLastCalledWith(4, 2, 'Мой комментарий');
  });
  it('reconciles unknown commit by reading, never repeats a completed grade', async () => {
    const { model, api } = setup();
    model.edit('0', '');
    api.check.mockRejectedValue(new ApiError(0, 'timeout', {}, 'timeout'));
    await model.check();
    api.read.mockRejectedValue(new ApiError(0, 'offline'));
    await model.refresh();
    await model.check();
    expect(model.snapshot().unknown).toBe(true);
    expect(api.check).toHaveBeenCalledTimes(1);
    api.read.mockResolvedValue({
      ...answer,
      status: 'checked',
      grade: 0,
      version: 4,
    });
    await model.refresh();
    await model.check();
    expect(api.check).toHaveBeenCalledTimes(1);
    expect(model.snapshot().answer.grade).toBe(0);
  });
  it('permits conscious retry only after a successful read confirms no commit', async () => {
    const { model, api } = setup();
    model.edit('3', 'draft');
    api.check.mockRejectedValue(new ApiError(503, 'unavailable'));
    await model.check();
    api.read.mockResolvedValue(answer);
    await model.refresh();
    expect(api.check).toHaveBeenCalledTimes(1);
    api.check.mockResolvedValue({ ...answer, status: 'checked', grade: 3 });
    await model.check();
    expect(api.check).toHaveBeenCalledTimes(2);
  });
  it('background refresh keeps opened answer stable; checked by another tab is read only', async () => {
    const { model, api } = setup();
    model.edit('1', 'draft');
    model.reconcile({ ...answer, version: 4 });
    expect(model.snapshot().answer.version).toBe(3);
    expect(model.dirty).toBe(true);
    model.reconcile({ ...answer, version: 5, status: 'checked', grade: 5 });
    await model.check();
    expect(api.check).not.toHaveBeenCalled();
    expect(model.snapshot().answer.grade).toBe(5);
    expect(model.dirty).toBe(false);
  });
  it('revoked access prevents further writes and preserves draft', async () => {
    const { model, api } = setup();
    model.edit('2', 'draft');
    api.check.mockRejectedValue(new ApiError(403, 'Нет доступа'));
    await model.check();
    await model.check();
    expect(api.check).toHaveBeenCalledTimes(1);
    expect(model.snapshot()).toMatchObject({
      blocked: true,
      grade: '2',
      comment: 'draft',
    });
  });
});
