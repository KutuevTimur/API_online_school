import { ApiError } from '../api/error';
import {
  answerFiles,
  validateSelection,
  type Answer,
  type UploadAdapter,
} from '../api/files';
export type QueueItem = {
  id: string;
  file?: File;
  name: string;
  size: number;
  localUrl?: string;
  replaceId?: number;
  status:
    'ready' | 'uploading' | 'processing' | 'saved' | 'error' | 'uncertain';
  progress: number;
  error?: string;
};
export type QueueState = {
  items: QueueItem[];
  answer: Answer;
  busy: boolean;
  message?: string;
  needsRead: boolean;
  blocked: boolean;
  conflict?: boolean;
};
export class UploadQueueModel {
  private listeners = new Set<() => void>();
  private controller?: AbortController;
  protected generation = 0;
  private originalSizes = new Map<number, number>();
  state: QueueState;
  constructor(
    answer: Answer,
    private adapter: UploadAdapter,
  ) {
    this.state = {
      answer,
      items: [],
      busy: false,
      needsRead: false,
      blocked: false,
    };
  }
  subscribe = (fn: () => void) => {
    this.listeners.add(fn);
    return () => {
      this.listeners.delete(fn);
    };
  };
  snapshot = () => this.state;
  protected publish(patch: Partial<QueueState>) {
    this.state = { ...this.state, ...patch };
    this.listeners.forEach((fn) => fn());
  }
  private update(id: string, patch: Partial<QueueItem>) {
    this.publish({
      items: this.state.items.map((item) =>
        item.id === id ? { ...item, ...patch } : item,
      ),
    });
  }
  get dirty() {
    return this.state.items.some((item) => item.file);
  }
  add(files: File[], replaceId?: number) {
    if (this.state.busy || this.state.blocked || this.state.needsRead) return;
    for (const file of files) {
      const pending = this.state.items.filter(
        (item) => item.file && item.replaceId === undefined,
      );
      const existing = answerFiles(this.state.answer);
      const error = validateSelection(
        file,
        replaceId === undefined ? existing.length + pending.length : 0,
        existing
          .filter((item) => item.id !== replaceId)
          .reduce(
            (n, item) =>
              n + (this.originalSizes.get(item.id) ?? item.size_bytes ?? 0),
            0,
          ) + pending.reduce((n, item) => n + item.size, 0),
      );
      if (error) {
        this.publish({ message: `${file.name}: ${error}` });
        continue;
      }
      if (
        replaceId !== undefined &&
        this.state.items.some(
          (item) => item.file && item.replaceId === replaceId,
        )
      ) {
        this.publish({ message: 'Для этого файла уже выбрана замена' });
        continue;
      }
      this.publish({
        message: undefined,
        items: [
          ...this.state.items,
          {
            id: crypto.randomUUID(),
            file,
            name: file.name,
            size: file.size,
            replaceId,
            status: 'ready',
            progress: 0,
            localUrl: /^image\/(jpeg|png|webp)$/.test(file.type)
              ? URL.createObjectURL(file)
              : undefined,
          },
        ],
      });
    }
  }
  removeLocal(id: string) {
    const item = this.state.items.find((entry) => entry.id === id);
    if (!item || this.state.busy || this.state.needsRead) return;
    if (item.localUrl) URL.revokeObjectURL(item.localUrl);
    this.publish({
      items: this.state.items.filter((entry) => entry.id !== id),
    });
  }
  retry(id: string) {
    if (this.state.busy || this.state.needsRead || this.state.blocked) return;
    this.update(id, { status: 'ready', error: undefined, progress: 0 });
  }
  abort = () => this.controller?.abort();
  async read() {
    if (this.state.busy) return;
    const generation = this.generation;
    this.publish({ busy: true });
    try {
      const answer = await this.adapter.read();
      if (generation !== this.generation) return;
      this.publish({
        answer,
        needsRead: false,
        blocked: this.state.blocked || answer.status === 'checked',
        message:
          'Список обновлён. Сравните файлы ниже с локальной очередью. Уберите уже сохранённый файл из очереди или повторите его явно.',
      });
    } catch (error) {
      if (generation !== this.generation) return;
      this.publish({
        message:
          error instanceof ApiError
            ? error.message
            : 'Не удалось обновить список',
        needsRead: true,
        blocked:
          this.state.blocked ||
          (error instanceof ApiError && [403, 404].includes(error.status)),
      });
    } finally {
      if (generation === this.generation) this.publish({ busy: false });
    }
  }
  async run() {
    if (this.state.busy || this.state.needsRead || this.state.blocked) return;
    const generation = this.generation;
    this.publish({ busy: true, message: undefined });
    try {
      for (const candidate of this.state.items.filter(
        (item) => item.status === 'ready',
      )) {
        if (!candidate.file || generation !== this.generation) break;
        this.controller = new AbortController();
        this.update(candidate.id, { status: 'uploading', progress: 0 });
        try {
          const progress = (loaded: number, total: number | null) => {
            if (generation !== this.generation) return;
            this.update(candidate.id, {
              progress: total ? Math.min(100, (loaded / total) * 100) : 0,
              status: total && loaded >= total ? 'processing' : 'uploading',
            });
          };
          const answer =
            candidate.replaceId === undefined
              ? await this.adapter.append(
                  candidate.file,
                  this.state.answer.version,
                  this.controller.signal,
                  progress,
                )
              : await this.adapter.replace(
                  candidate.replaceId,
                  candidate.file,
                  this.state.answer.version,
                  this.controller.signal,
                  progress,
                );
          if (generation !== this.generation) break;
          const previousIds = new Set(
            answerFiles(this.state.answer).map((item) => item.id),
          );
          if (candidate.replaceId !== undefined)
            this.originalSizes.delete(candidate.replaceId);
          for (const descriptor of answerFiles(answer)) {
            if (
              !previousIds.has(descriptor.id) ||
              descriptor.id === candidate.replaceId
            )
              this.originalSizes.set(descriptor.id, candidate.size);
          }
          if (candidate.localUrl) URL.revokeObjectURL(candidate.localUrl);
          this.update(candidate.id, {
            status: 'saved',
            file: undefined,
            localUrl: undefined,
            progress: 100,
          });
          this.publish({ answer });
        } catch (error) {
          if (generation !== this.generation) break;
          const uncertain =
            !(error instanceof ApiError) ||
            error.status === 0 ||
            error.status >= 500 ||
            error.status === 401 ||
            (error.status >= 200 && error.status < 300);
          this.update(candidate.id, {
            status: uncertain ? 'uncertain' : 'error',
            error:
              error instanceof ApiError
                ? error.message
                : 'Сохранение не подтверждено',
          });
          if (
            uncertain ||
            (error instanceof ApiError &&
              [403, 404, 409].includes(error.status))
          ) {
            this.publish({
              needsRead: true,
              conflict: error instanceof ApiError && error.status === 409,
              blocked:
                error instanceof ApiError && [403, 404].includes(error.status),
            });
            break;
          }
        }
      }
    } finally {
      this.controller = undefined;
      if (generation === this.generation) this.publish({ busy: false });
    }
  }
  async removeServer(id: number) {
    if (this.state.busy || this.state.needsRead || this.state.blocked) return;
    const generation = this.generation;
    this.publish({ busy: true });
    try {
      const answer = await this.adapter.remove(id, this.state.answer.version);
      if (generation !== this.generation) return;
      this.originalSizes.delete(id);
      this.publish({ answer });
    } catch (error) {
      if (generation !== this.generation) return;
      this.publish({
        needsRead: true,
        conflict: error instanceof ApiError && error.status === 409,
        message:
          error instanceof ApiError
            ? error.message
            : 'Удаление не подтверждено',
      });
      throw error;
    } finally {
      if (generation === this.generation) this.publish({ busy: false });
    }
  }
  dispose() {
    this.generation += 1;
    this.originalSizes.clear();
    this.abort();
    for (const item of this.state.items)
      if (item.localUrl) URL.revokeObjectURL(item.localUrl);
    this.publish({
      items: [],
      busy: false,
      needsRead: true,
      blocked: true,
      answer: { ...this.state.answer, files: [], text_content: null },
    });
  }
}
