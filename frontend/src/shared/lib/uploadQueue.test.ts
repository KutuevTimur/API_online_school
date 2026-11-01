import { beforeEach, describe, expect, it, vi } from 'vitest';
import { UploadQueueModel } from './uploadQueue';
import { ApiError } from '../api/error';
import {
  validateSelection,
  MiB,
  fileTarget,
  type Answer,
  type UploadAdapter,
} from '../api/files';
const answer = (version = 1): Answer => ({
  id: 1,
  homework_id: 2,
  attempt_number: 1,
  version,
  is_working: true,
  status: 'draft',
  files: [],
  review_files: [],
  created_at: '',
  updated_at: '',
});
const file = (name = 'work.pdf') =>
  new File(['synthetic'], name, { type: 'application/pdf' });
function adapter(): UploadAdapter {
  return {
    read: vi.fn().mockResolvedValue(answer(7)),
    append: vi.fn(),
    replace: vi.fn(),
    remove: vi.fn(),
  };
}
beforeEach(() => {
  URL.createObjectURL = vi.fn(() => 'blob:synthetic');
  URL.revokeObjectURL = vi.fn();
});
describe('sequential upload and recovery', () => {
  it('holds originals until ack and chains the actual acknowledged versions', async () => {
    const api = adapter();
    let ack!: (value: Answer) => void;
    vi.mocked(api.append)
      .mockImplementationOnce((_file, _version, _signal, progress) => {
        progress(10, 10);
        return new Promise((resolve) => {
          ack = resolve;
        });
      })
      .mockResolvedValueOnce(answer(9));
    const queue = new UploadQueueModel(answer(), api);
    queue.add([file(), file()]);
    const run = queue.run();
    expect(queue.state.items[0].status).toBe('processing');
    expect(queue.state.items[0].file).toBeInstanceOf(File);
    expect(api.append).toHaveBeenCalledTimes(1);
    ack(answer(8));
    await run;
    expect(vi.mocked(api.append).mock.calls.map((call) => call[1])).toEqual([
      1, 8,
    ]);
    expect(
      queue.state.items.every((item) => !item.file && item.status === 'saved'),
    ).toBe(true);
    expect(queue.state.answer.version).toBe(9);
  });
  it('keeps other ready files after timeout; reads before a conscious manual retry', async () => {
    const api = adapter();
    vi.mocked(api.append)
      .mockRejectedValueOnce(new ApiError(0, 'timeout', {}, 'timeout'))
      .mockResolvedValue(answer(8));
    const queue = new UploadQueueModel(answer(), api);
    queue.add([file(), file('second.pdf')]);
    await queue.run();
    expect(queue.state.items.map((item) => item.status)).toEqual([
      'uncertain',
      'ready',
    ]);
    await queue.run();
    queue.retry(queue.state.items[0].id);
    expect(api.append).toHaveBeenCalledTimes(1);
    await queue.read();
    queue.removeLocal(queue.state.items[0].id);
    await queue.run();
    expect(vi.mocked(api.append).mock.calls[1][1]).toBe(7);
  });
  it('continues independent ready files after 413 and preserves the failed original', async () => {
    const api = adapter();
    vi.mocked(api.append)
      .mockRejectedValueOnce(new ApiError(413, 'quota'))
      .mockResolvedValueOnce(answer(2));
    const queue = new UploadQueueModel(answer(), api);
    queue.add([file(), file()]);
    await queue.run();
    expect(queue.state.items[0].status).toBe('error');
    expect(queue.state.items[0].file).toBeInstanceOf(File);
    expect(queue.state.items[1].status).toBe('saved');
  });
  it('keeps exact replace and remove IDs across files with the same filename', async () => {
    const api = adapter();
    vi.mocked(api.replace).mockResolvedValue(answer(2));
    vi.mocked(api.remove).mockResolvedValue(answer(3));
    const queue = new UploadQueueModel(answer(), api);
    queue.add([file()], 42);
    await queue.run();
    await queue.removeServer(51);
    expect(vi.mocked(api.replace).mock.calls[0].slice(0, 1)).toEqual([42]);
    expect(api.remove).toHaveBeenCalledWith(51, 2);
  });
  it('stops on conflict and preserves the pending files, then reads authoritative version', async () => {
    const api = adapter();
    vi.mocked(api.append).mockRejectedValue(new ApiError(409, 'conflict'));
    const queue = new UploadQueueModel(answer(), api);
    queue.add([file(), file()]);
    await queue.run();
    expect(queue.state.needsRead).toBe(true);
    expect(queue.dirty).toBe(true);
    await queue.read();
    expect(queue.state.answer.version).toBe(7);
  });
  it('cannot resurrect private originals after logout while ack is in flight', async () => {
    const api = adapter();
    let ack!: (value: Answer) => void;
    vi.mocked(api.append).mockImplementation(
      () =>
        new Promise((resolve) => {
          ack = resolve;
        }),
    );
    const queue = new UploadQueueModel(answer(), api);
    queue.add([new File(['photo'], 'photo.png', { type: 'image/png' })]);
    const run = queue.run();
    queue.dispose();
    ack(answer(2));
    await run;
    expect(queue.state.items).toEqual([]);
    expect(queue.state.blocked).toBe(true);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:synthetic');
  });
  it('rejects only an excessive selection without dropping the first ten files', () => {
    const queue = new UploadQueueModel(answer(), adapter());
    queue.add(Array.from({ length: 10 }, () => file()));
    queue.add([file()]);
    expect(queue.state.items).toHaveLength(10);
    expect(queue.state.message).toContain('10');
    expect(
      validateSelection({ name: 'large.pdf', size: 21 * MiB } as File, 0, 0),
    ).toContain('20');
    expect(validateSelection(file(), 0, 100 * MiB)).toContain('100');
    expect(validateSelection(file('bad.svg'), 0, 0)).toContain('PDF');
  });
  it('rejects external targets and token parameters', () => {
    expect(() => fileTarget('https://evil/file')).toThrow();
    expect(() => fileTarget('//evil/file')).toThrow();
    expect(() => fileTarget('/file?token=secret')).toThrow();
    expect(fileTarget('/submissions/1/files/2?homework_id=3')).toEqual({
      path: '/submissions/1/files/2',
      params: { homework_id: '3' },
    });
  });
  it('does not resurrect a private answer when a read finishes after logout', async () => {
    const api = adapter();
    let resolve!: (value: Answer) => void;
    vi.mocked(api.read).mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const queue = new UploadQueueModel(answer(), api);
    const reading = queue.read();
    queue.dispose();
    resolve({ ...answer(5), text_content: 'private', files: [] });
    await reading;
    expect(queue.state.answer.text_content).toBeNull();
    expect(queue.state.blocked).toBe(true);
  });
  it('can recover a failed reconciliation GET without replaying uploads', async () => {
    const api = adapter();
    vi.mocked(api.read)
      .mockRejectedValueOnce(new ApiError(0, 'offline', {}, 'network'))
      .mockResolvedValueOnce(answer(3));
    const queue = new UploadQueueModel(answer(), api);
    queue.add([file()]);
    await queue.read();
    expect(queue.state.needsRead).toBe(true);
    expect(queue.state.blocked).toBe(false);
    await queue.read();
    expect(queue.state.needsRead).toBe(false);
    expect(queue.state.answer.version).toBe(3);
    expect(api.append).not.toHaveBeenCalled();
  });
});
