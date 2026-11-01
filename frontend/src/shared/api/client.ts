import { session } from '../../features/auth/session';
import { ApiError, responseError } from './error';
export type RequestOptions = {
  params?: Record<string, string | number | undefined>;
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
  response?: 'json' | 'blob';
  sessionRetried?: boolean;
  maxBytes?: number;
};
export function apiUrl(
  path: string,
  params: Record<string, string | number | undefined> = {},
) {
  if (
    !path.startsWith('/') ||
    path.startsWith('//') ||
    /[?#\\]/.test(path) ||
    path.split('/').some((p) => {
      try {
        return ['.', '..'].includes(decodeURIComponent(p));
      } catch {
        return true;
      }
    })
  )
    throw new Error('Expected an API path');
  const url = new URL(
    `/api${path.replace(/^\/api(?=\/|$)/, '')}`,
    'http://localhost',
  );
  for (const [key, value] of Object.entries(params))
    if (value !== undefined) url.searchParams.set(key, String(value));
  return url.pathname + url.search;
}
export const pathId = (value: string | number) =>
  encodeURIComponent(String(value));
function headers(body: unknown) {
  const result = new Headers();
  const token = session.accessToken();
  if (token) result.set('Authorization', `Bearer ${token}`);
  if (body !== undefined && !(body instanceof FormData))
    result.set('Content-Type', 'application/json');
  return result;
}
export async function decodeResponse(
  response: Response,
  mode: 'json' | 'blob' = 'json',
) {
  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    throw responseError(response.status, payload);
  }
  if (response.status === 204) return undefined;
  if (mode === 'blob') return response.blob();
  try {
    return await response.json();
  } catch {
    throw new ApiError(
      response.status,
      'Не удалось прочитать ответ сервера. Попробуйте ещё раз',
    );
  }
}
export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  options.signal?.addEventListener('abort', abort, { once: true });
  if (options.signal?.aborted) controller.abort();
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, options.timeoutMs ?? 30000);
  try {
    const sentToken = session.accessToken();
    const response = await fetch(apiUrl(path, options.params), {
      method: options.method ?? 'GET',
      headers: headers(options.body),
      body:
        options.body === undefined
          ? undefined
          : options.body instanceof FormData
            ? options.body
            : JSON.stringify(options.body),
      signal: controller.signal,
      credentials: 'same-origin',
    });
    if (response.status === 401 && !options.sessionRetried) {
      if (!session.accessToken() || sentToken === session.accessToken()) {
        try {
          await session.refresh();
        } catch {
          throw new ApiError(401, 'Нужно войти снова');
        }
      }
      if ((options.method ?? 'GET') === 'GET')
        return request<T>(path, { ...options, sessionRetried: true });
      throw new ApiError(
        401,
        'Сессия восстановлена. Проверьте состояние перед повтором действия',
      );
    }
    if (response.status === 401) session.expire();
    if (response.ok && options.response === 'blob' && options.maxBytes) {
      const tooLarge = () =>
        new ApiError(
          413,
          'Файл больше лимита предпросмотра. Доступно скачивание',
        );
      if (Number(response.headers.get('Content-Length')) > options.maxBytes) {
        await response.body?.cancel();
        throw tooLarge();
      }
      const reader = response.body?.getReader();
      if (reader) {
        const chunks: Uint8Array<ArrayBuffer>[] = [];
        let bytes = 0;
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          bytes += value.byteLength;
          if (bytes > options.maxBytes) {
            await reader.cancel();
            throw tooLarge();
          }
          chunks.push(new Uint8Array(value));
        }
        return new Blob(chunks, {
          type: response.headers.get('Content-Type') || '',
        }) as T;
      }
    }
    return (await decodeResponse(response, options.response)) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (controller.signal.aborted)
      throw new ApiError(
        0,
        timedOut ? 'Превышено время ожидания' : 'Запрос отменён',
        {},
        timedOut ? 'timeout' : 'abort',
      );
    throw new ApiError(0, 'Нет связи. Проверьте подключение', {}, 'network');
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener('abort', abort);
  }
}
export function upload<T>(
  path: string,
  body: FormData,
  options: {
    signal?: AbortSignal;
    timeoutMs?: number;
    method?: 'POST' | 'PATCH' | 'PUT';
    params?: Record<string, string | number | undefined>;
    onProgress?: (loaded: number, total: number | null) => void;
  } = {},
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const abort = () => xhr.abort();
    const cleanup = () => options.signal?.removeEventListener('abort', abort);
    const fail = (error: ApiError) => {
      cleanup();
      reject(error);
    };
    xhr.open(options.method ?? 'POST', apiUrl(path, options.params));
    xhr.timeout = options.timeoutMs ?? 60000;
    headers(body).forEach((value, key) => xhr.setRequestHeader(key, value));
    xhr.upload.onprogress = (e) =>
      options.onProgress?.(e.loaded, e.lengthComputable ? e.total : null);
    xhr.onerror = () =>
      fail(
        new ApiError(
          0,
          'Нет связи. Проверьте список файлов перед повтором',
          {},
          'network',
        ),
      );
    xhr.ontimeout = () =>
      fail(
        new ApiError(
          0,
          'Не удалось подтвердить сохранение. Проверьте список файлов',
          {},
          'timeout',
        ),
      );
    xhr.onabort = () =>
      fail(
        new ApiError(
          0,
          'Загрузка отменена. Проверьте список файлов',
          {},
          'abort',
        ),
      );
    xhr.onload = () => {
      cleanup();
      const response = new Response(
        xhr.status === 204 ? null : xhr.responseText,
        {
          status: xhr.status,
          headers: {
            'Content-Type': xhr.getResponseHeader('Content-Type') || '',
          },
        },
      );
      if (xhr.status === 401) {
        void session.refresh().catch(() => session.expire());
      }
      decodeResponse(response).then((value) => resolve(value as T), reject);
    };
    if (options.signal?.aborted) {
      fail(new ApiError(0, 'Загрузка отменена', {}, 'abort'));
      return;
    }
    options.signal?.addEventListener('abort', abort, { once: true });
    xhr.send(body);
  });
}
