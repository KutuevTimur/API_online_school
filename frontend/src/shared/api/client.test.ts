import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiUrl, pathId, request, upload } from './client';
import { ApiError, responseError } from './error';
afterEach(() => vi.unstubAllGlobals());
describe('HTTP contracts', () => {
  it('encodes identifiers and query values and prefixes exactly once', () => {
    expect(
      apiUrl(`/courses/${pathId('a/b')}`, { course: 'a&b', offset: 0 }),
    ).toBe('/api/courses/a%2Fb?course=a%26b&offset=0');
    expect(apiUrl('/api/courses')).toBe('/api/courses');
    expect(() => apiUrl('//foreign')).toThrow();
    expect(() => apiUrl('/a/../b')).toThrow();
  });
  it('sends query parameters through the request transport', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response('{}'));
    vi.stubGlobal('fetch', fetch);
    await request('/courses', { params: { course: 'a&b', offset: 0 } });
    expect(fetch.mock.calls[0][0]).toBe('/api/courses?course=a%26b&offset=0');
  });
  it('rejects malformed successful JSON as a structured error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('<html>proxy</html>')),
    );
    await expect(request('/courses')).rejects.toMatchObject({
      status: 200,
      kind: 'http',
    });
  });
  it('maps 422 to safe Russian field errors without leaking detail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [
              {
                loc: ['body', 'title'],
                type: 'missing',
                msg: 'internal secret',
              },
            ],
          }),
          { status: 422 },
        ),
      ),
    );
    await expect(request('/courses')).rejects.toMatchObject({
      status: 422,
      fields: { title: 'Заполните поле' },
      message: 'Проверьте отмеченные поля',
    });
  });
  it('handles string detail and non-JSON proxy errors safely', async () => {
    expect(responseError(403, { detail: 'secret traceback' }).message).toBe(
      'Нет доступа к этому материалу',
    );
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response('<h1>proxy failure</h1>', { status: 502 }),
        ),
    );
    await expect(request('/courses')).rejects.toMatchObject({
      status: 502,
      fields: {},
    });
  });
  it('accepts 204 without parsing JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    expect(await request('/courses', { method: 'DELETE' })).toBeUndefined();
  });
  it('passes FormData without a manual boundary and supports blob', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response('pdf'));
    vi.stubGlobal('fetch', fetch);
    const body = new FormData();
    body.append('file', new Blob(['x']), 'test.pdf');
    expect(
      await request('/files', { method: 'POST', body, response: 'blob' }),
    ).toBeInstanceOf(Blob);
    const options = fetch.mock.calls[0][1];
    expect(options.body).toBe(body);
    expect(options.headers.has('Content-Type')).toBe(false);
  });
  it('serializes JSON and makes no token persistence', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response('{}'));
    vi.stubGlobal('fetch', fetch);
    await request('/courses', { method: 'POST', body: { title: 'Курс' } });
    expect(fetch.mock.calls[0][1].body).toBe('{"title":"Курс"}');
    expect(fetch.mock.calls[0][1].headers.get('Authorization')).toBeNull();
  });
  it('cancels a request and preserves abort semantics', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_url, options) =>
          new Promise((_resolve, reject) => {
            options.signal.addEventListener('abort', () =>
              reject(new DOMException('aborted', 'AbortError')),
            );
            if (options.signal.aborted)
              reject(new DOMException('aborted', 'AbortError'));
          }),
      ),
    );
    const controller = new AbortController();
    const promise = request('/courses', { signal: controller.signal });
    controller.abort();
    await expect(promise).rejects.toMatchObject({ kind: 'abort' });
  });
  it('distinguishes timeout from caller cancellation', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_url, options) =>
          new Promise((_resolve, reject) =>
            options.signal.addEventListener('abort', () =>
              reject(new Error('timeout')),
            ),
          ),
      ),
    );
    await expect(request('/courses', { timeoutMs: 5 })).rejects.toMatchObject({
      kind: 'timeout',
    });
  });
  it('reports network failure as structured error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    );
    await expect(request('/courses')).rejects.toBeInstanceOf(ApiError);
  });
  it('XHR measures byte progress and handles 204', async () => {
    let instance: FakeXHR;
    class FakeXHR {
      status = 204;
      responseText = '';
      timeout = 0;
      upload: { onprogress?: (event: unknown) => void } = {};
      onload?: () => void;
      open = vi.fn();
      setRequestHeader = vi.fn();
      getResponseHeader = () => null;
      send() {
        this.upload.onprogress?.({
          loaded: 2,
          total: 4,
          lengthComputable: true,
        });
        this.onload?.();
      }
      constructor() {
        /* Test double captures transport instance. */
        // eslint-disable-next-line @typescript-eslint/no-this-alias
        instance = this;
      }
    }
    vi.stubGlobal('XMLHttpRequest', FakeXHR);
    const progress = vi.fn();
    expect(
      await upload('/files', new FormData(), { onProgress: progress }),
    ).toBeUndefined();
    expect(progress).toHaveBeenCalledWith(2, 4);
    expect(instance!.setRequestHeader).not.toHaveBeenCalled();
  });
});

describe('bounded protected preview', () => {
  it('stops streaming before retaining an oversized unknown-length archive', async () => {
    const cancel = vi.fn();
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(new Uint8Array(8));
        controller.enqueue(new Uint8Array(8));
      },
      cancel,
    });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(body, {
          headers: { 'Content-Type': 'application/pdf' },
        }),
      ),
    );
    await expect(
      request('/file', { response: 'blob', maxBytes: 10 }),
    ).rejects.toMatchObject({ status: 413 });
    expect(cancel).toHaveBeenCalledOnce();
  });
  it('retains the final response MIME rather than descriptor or filename guesses', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response('image', { headers: { 'Content-Type': 'image/webp' } }),
        ),
    );
    const result = await request<Blob>('/file', {
      response: 'blob',
      maxBytes: 10,
    });
    expect(result.type).toBe('image/webp');
    expect(result.size).toBe(5);
  });
  it('classifies XHR timeout and abort without resending a mutation', async () => {
    let instance: FakeXHR;
    class FakeXHR {
      upload = {};
      timeout = 0;
      ontimeout?: () => void;
      onabort?: () => void;
      constructor() {
        // Test double captures the transport for explicit timeout/abort events.
        // eslint-disable-next-line @typescript-eslint/no-this-alias
        instance = this;
      }
      open = vi.fn();
      setRequestHeader = vi.fn();
      send = vi.fn();
      abort() {
        this.onabort?.();
      }
    }
    vi.stubGlobal('XMLHttpRequest', FakeXHR);
    const pending = upload('/file', new FormData());
    instance!.ontimeout?.();
    await expect(pending).rejects.toMatchObject({ kind: 'timeout' });
    expect(instance!.send).toHaveBeenCalledOnce();
    const controller = new AbortController();
    const cancelled = upload('/file', new FormData(), {
      signal: controller.signal,
    });
    controller.abort();
    await expect(cancelled).rejects.toMatchObject({ kind: 'abort' });
    expect(instance!.send).toHaveBeenCalledOnce();
  });
});
