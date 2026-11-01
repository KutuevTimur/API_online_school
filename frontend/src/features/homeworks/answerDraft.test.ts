import { describe, it, expect, vi } from 'vitest';
import type { Answer } from '../../shared/api/files';
import { ApiError } from '../../shared/api/error';
import { AnswerDraft } from './answerDraft';
import { saveText } from './api';
import { request } from '../../shared/api/client';
vi.mock('./api', () => ({
  saveText: vi.fn(),
  adapter: vi.fn(() => ({
    read: vi.fn(),
    append: vi.fn(),
    replace: vi.fn(),
    remove: vi.fn(),
  })),
}));
vi.mock('../../shared/api/client', () => ({ request: vi.fn() }));
const answer = {
  id: 1,
  homework_id: 3,
  version: 1,
  status: 'draft',
  text_content: 'old',
  files: [],
} as unknown as Answer;
describe('answer lifecycle', () => {
  it('opening creates no draft; save then submit uses acknowledged answer only', async () => {
    vi.mocked(saveText).mockClear();
    vi.mocked(request).mockClear();
    const model = new AnswerDraft(3, { ...answer, id: 0, text_content: null });
    expect(saveText).not.toHaveBeenCalled();
    model.setText('solution');
    vi.mocked(saveText).mockResolvedValue({
      ...answer,
      text_content: 'solution',
    });
    vi.mocked(request).mockResolvedValue({ ...answer, status: 'submitted' });
    await model.save(true);
    expect(saveText).toHaveBeenCalledWith(3, 'solution', undefined);
    expect(request).toHaveBeenCalledWith(
      '/submissions/1/submit',
      expect.anything(),
    );
    expect(model.state.answer.status).toBe('submitted');
    expect(model.dirty).toBe(false);
  });
  it('409 preserves local content and blocks blind retry', async () => {
    const model = new AnswerDraft(3, answer);
    model.setText('local');
    vi.mocked(saveText).mockRejectedValue(new ApiError(409, 'conflict'));
    await model.save();
    expect(model.text).toBe('local');
    expect(model.state.needsRead).toBe(true);
    const count = vi.mocked(saveText).mock.calls.length;
    await model.save();
    expect(saveText).toHaveBeenCalledTimes(count);
  });
  it('omission differs from explicit clearing; checked refresh retains dirty local text', async () => {
    const model = new AnswerDraft(3, answer);
    model.setText('');
    vi.mocked(saveText).mockResolvedValue({
      ...answer,
      version: 2,
      text_content: null,
    });
    await model.save();
    expect(saveText).toHaveBeenLastCalledWith(3, '', answer);
    model.setText('unsaved');
    model.reconcile({ ...answer, version: 3, status: 'checked', grade: 0 });
    expect(model.text).toBe('unsaved');
    expect(model.state.conflict).toBe(true);
  });
  it('logout while saving does not restore content after response', async () => {
    let resolve!: (a: Answer) => void;
    vi.mocked(saveText).mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    const model = new AnswerDraft(3, answer);
    model.setText('local');
    const pending = model.save();
    model.dispose();
    resolve({ ...answer, text_content: 'local' });
    await pending;
    expect(model.text).toBe('');
    expect(model.state.answer.text_content).toBeNull();
  });
});
it('ignores older cache versions and does not announce a timed-out save as success', async () => {
  const model = new AnswerDraft(3, {
    ...answer,
    version: 4,
    text_content: 'current',
  });
  model.reconcile({ ...answer, version: 2, text_content: 'stale' });
  expect(model.text).toBe('current');
  expect(model.state.answer.version).toBe(4);
  model.setText('unconfirmed');
  vi.mocked(saveText).mockRejectedValue(
    new ApiError(0, 'Превышено время ожидания', {}, 'timeout'),
  );
  await model.save(true);
  expect(model.state.needsRead).toBe(true);
  expect(model.text).toBe('unconfirmed');
  expect(model.state.answer.status).toBe('draft');
});
