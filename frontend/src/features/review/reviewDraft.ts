import { validateSelection, type Answer } from '../../shared/api/files';
import { ApiError } from '../../shared/api/error';
import type { reviewAPI } from './api';
export class ReviewDraft {
  private listeners = new Set<() => void>();
  private state: {
    answer: Answer;
    latest: Answer | null;
    files: File[];
    grade: string;
    comment: string;
    busy: boolean;
    unknown: boolean;
    blocked: boolean;
    error: string;
  };
  constructor(
    answer: Answer,
    private api: ReturnType<typeof reviewAPI>,
  ) {
    this.state = {
      answer,
      latest: null,
      files: [],
      grade: '',
      comment: '',
      busy: false,
      unknown: false,
      blocked: false,
      error: '',
    };
  }
  snapshot = () => this.state;
  subscribe = (fn: () => void) => {
    this.listeners.add(fn);
    return () => {
      this.listeners.delete(fn);
    };
  };
  get dirty() {
    return (
      this.state.answer.status !== 'checked' &&
      (this.state.files.length > 0 ||
        this.state.grade !== '' ||
        this.state.comment !== '' ||
        this.state.unknown)
    );
  }
  private patch(values: Partial<typeof this.state>) {
    this.state = { ...this.state, ...values };
    this.listeners.forEach((fn) => fn());
  }
  edit(grade: string, comment: string) {
    this.patch({ grade, comment, error: '' });
  }
  attach(files: File[], replaceIndex?: number) {
    if (
      this.state.busy ||
      this.state.unknown ||
      this.state.blocked ||
      this.state.answer.status === 'checked'
    )
      return;
    const next = this.state.files.filter((_, i) => i !== replaceIndex);
    for (const file of files) {
      const error = validateSelection(
        file,
        next.length,
        next.reduce((n, f) => n + f.size, 0),
      );
      if (error) {
        this.patch({ error });
        return;
      }
      next.push(file);
    }
    this.patch({ files: next, error: '' });
  }
  removeFile(index: number) {
    if (!this.state.busy && !this.state.unknown)
      this.patch({ files: this.state.files.filter((_, i) => i !== index) });
  }
  reconcile(answer: Answer) {
    if (answer.status === 'checked')
      this.patch({
        answer,
        latest: null,
        unknown: false,
        error: '',
        files: [],
      });
    else if (answer.version !== this.state.answer.version)
      this.patch({ latest: answer });
  }
  openLatest() {
    if (this.state.latest)
      this.patch({ answer: this.state.latest, latest: null, error: '' });
  }
  async refresh() {
    if (this.state.busy) return;
    this.patch({ busy: true, error: '' });
    try {
      const answer = await this.api.read();
      this.reconcile(answer);
      this.patch({
        unknown: false,
        error:
          answer.status === 'checked'
            ? ''
            : 'Проверка ещё не завершена. Прочитайте ответ и подтвердите оценку.',
      });
    } catch (e) {
      this.patch({
        error:
          e instanceof ApiError
            ? e.message
            : 'Не удалось получить результат. Повторите чтение перед проверкой.',
      });
    } finally {
      this.patch({ busy: false });
    }
  }
  async check() {
    const { answer, grade, comment, busy, unknown, latest, blocked } =
      this.state;
    if (busy || unknown || latest || blocked || answer.status !== 'submitted')
      return;
    if (!/^[0-5]$/.test(grade)) {
      this.patch({ error: 'Выберите оценку от 0 до 5' });
      return;
    }
    this.patch({ busy: true, error: '' });
    try {
      const saved = await this.api.check(
        answer.version,
        Number(grade),
        comment,
        ...(this.state.files.length ? [this.state.files] : []),
      );
      this.patch({ answer: saved, latest: null, files: [] });
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        // The teacher's draft remains separate from the newly fetched answer.
        this.patch({
          unknown: true,
          error: 'Ответ изменился или уже проверен. Получите текущую версию.',
        });
      } else if (
        e instanceof ApiError &&
        [400, 401, 403, 404, 422].includes(e.status)
      ) {
        this.patch({
          blocked: [403, 404].includes(e.status),
          error: e.message,
        });
      } else
        this.patch({
          unknown: true,
          error:
            'Не удалось подтвердить проверку. Сначала проверьте результат на сервере.',
        });
    } finally {
      this.patch({ busy: false });
    }
  }
}
