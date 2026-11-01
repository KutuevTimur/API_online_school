export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fields: Record<string, string> = {},
    public kind: 'http' | 'network' | 'timeout' | 'abort' = 'http',
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
export function responseError(status: number, payload: unknown): ApiError {
  if (
    payload &&
    typeof payload === 'object' &&
    'code' in payload &&
    payload.code === 'lecture_limit'
  )
    return new ApiError(
      status,
      'К занятию можно добавить до 4 файлов материалов. Удалите лишний файл перед загрузкой.',
    );
  const fields: Record<string, string> = {};
  const detail =
    payload && typeof payload === 'object' && 'detail' in payload
      ? payload.detail
      : null;
  if (Array.isArray(detail))
    for (const item of detail) {
      if (item && Array.isArray(item.loc)) {
        const path = item.loc
          .filter(
            (part: unknown) =>
              part !== 'body' && part !== 'query' && part !== 'path',
          )
          .join('.');
        fields[path] =
          item.type === 'missing' ? 'Заполните поле' : 'Проверьте значение';
      }
    }
  const messages: Record<number, string> = {
    400: 'Проверьте введённые данные',
    401: 'Нужно войти снова',
    403: 'Нет доступа к этому материалу',
    404: 'Материал больше недоступен',
    409: 'Данные изменились. Откройте обновлённую версию',
    413: 'Превышен размер файла или квота хранилища. Уменьшите файл или обратитесь к администратору',
    422: 'Проверьте отмеченные поля',
  };
  // Preserve structured status/field information; raw backend/proxy text is never user copy.
  return new ApiError(
    status,
    messages[status] || 'Не удалось загрузить данные. Попробуйте ещё раз',
    fields,
  );
}
