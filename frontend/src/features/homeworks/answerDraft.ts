import { UploadQueueModel } from '../../shared/lib/uploadQueue';
import { ApiError } from '../../shared/api/error';
import { request } from '../../shared/api/client';
import { type Answer } from '../../shared/api/files';
import { adapter, saveText } from './api';
export class AnswerDraft extends UploadQueueModel {
  text: string;
  savedText: string;
  saving = false;
  fieldError: string | undefined;
  constructor(
    private homeworkId: number,
    answer: Answer,
  ) {
    let current: () => Answer = () => answer;
    super(
      answer,
      adapter(homeworkId, () => current()),
    );
    current = () => this.state.answer;
    this.text = this.savedText = answer.text_content || '';
  }
  override get dirty() {
    return this.text !== this.savedText || super.dirty;
  }
  setText(text: string) {
    this.fieldError = undefined;
    this.text = text;
    this.publish({});
  }
  reconcile(answer: Answer) {
    if (
      this.saving ||
      this.state.busy ||
      !answer.id ||
      (answer.id === this.state.answer.id &&
        answer.version < this.state.answer.version) ||
      (answer.version === this.state.answer.version &&
        answer.status === this.state.answer.status)
    )
      return;
    if (this.dirty) {
      this.publish({ needsRead: true, conflict: true });
      return;
    }
    this.text = this.savedText = answer.text_content || '';
    this.publish({ answer, blocked: answer.status === 'checked' });
  }
  override async read() {
    await super.read();
    if (!this.state.needsRead)
      this.savedText = this.state.answer.text_content || '';
    this.publish({});
  }
  async save(send = false) {
    if (
      this.saving ||
      this.state.busy ||
      this.state.needsRead ||
      this.state.blocked ||
      this.state.answer.status === 'checked'
    )
      return;
    const generation = this.generation;
    this.fieldError = undefined;
    this.saving = true;
    this.publish({ message: undefined });
    try {
      if (!this.state.answer.id || this.text !== this.savedText) {
        const answer = await saveText(
          this.homeworkId,
          this.text,
          this.state.answer.id ? this.state.answer : undefined,
        );
        if (generation !== this.generation) return;
        this.savedText = this.text;
        this.publish({ answer });
      }
      await this.run();
      if (generation !== this.generation) return;
      if (this.dirty || this.state.needsRead) {
        this.publish({
          message:
            'Решение не отправлено: сохранение файлов не завершено. Проверьте очередь.',
        });
        return;
      }
      if (send && this.state.answer.status === 'draft') {
        const answer = await request<Answer>(
          `/submissions/${this.state.answer.id}/submit`,
          { method: 'POST', params: { homework_id: this.homeworkId } },
        );
        if (generation !== this.generation) return;
        this.publish({ answer });
      }
      this.publish({
        message:
          this.state.answer.status === 'submitted'
            ? 'Решение на проверке. Изменения сохранены.'
            : 'Черновик сохранён. Чтобы преподаватель получил решение, отправьте его.',
      });
    } catch (error) {
      if (generation !== this.generation) return;
      if (error instanceof ApiError && error.status === 422)
        this.fieldError = 'Добавьте текст решения или хотя бы один файл.';
      const uncertain =
        !(error instanceof ApiError) ||
        error.status === 0 ||
        error.status >= 500 ||
        error.status === 401;
      this.publish({
        message:
          error instanceof ApiError
            ? error.status === 422
              ? undefined
              : error.message
            : 'Не удалось подтвердить сохранение',
        needsRead:
          uncertain ||
          (error instanceof ApiError && [403, 404, 409].includes(error.status)),
        conflict: error instanceof ApiError && error.status === 409,
        blocked: error instanceof ApiError && [403, 404].includes(error.status),
      });
    } finally {
      this.saving = false;
      this.publish({});
    }
  }
  override dispose() {
    this.text = this.savedText = '';
    super.dispose();
  }
}
