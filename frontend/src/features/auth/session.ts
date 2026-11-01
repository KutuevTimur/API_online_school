import { useSyncExternalStore } from 'react';
export type User = {
  id: number;
  username: string;
  role: 'student' | 'teacher' | 'admin';
};
type State = {
  status: 'boot' | 'ready' | 'signed-out' | 'error';
  user?: User;
  message?: string;
  reauth?: boolean;
};
let state: State = { status: 'boot' };
let access: string | undefined;
let identity: number | undefined;
let flight: Promise<void> | undefined;
const listeners = new Set<() => void>();
const cleanups = new Set<() => void>();
const channel =
  typeof BroadcastChannel !== 'undefined'
    ? new BroadcastChannel('lgg-session')
    : undefined;
const generation = () => {
  try {
    return localStorage.getItem('lgg-logout-generation') || '';
  } catch {
    throw new Error('Разрешите локальное хранилище для безопасной сессии');
  }
};
function emit(next: State) {
  state = next;
  listeners.forEach((fn) => fn());
}
function clear() {
  access = undefined;
  identity = undefined;
  cleanups.forEach((fn) => fn());
  emit({ status: 'signed-out' });
}
channel?.addEventListener('message', (event) => {
  if (
    event.data === 'logout' ||
    (event.data?.type === 'account-change' && event.data.userId !== identity)
  )
    clear();
});
window.addEventListener('storage', (event) => {
  if (event.key === 'lgg-logout-generation') clear();
});
async function locked<T>(fn: () => Promise<T>): Promise<T> {
  if (!navigator.locks) throw new Error('Откройте в современном браузере');
  const before = generation();
  return navigator.locks.request('lgg-session', async () => {
    if (before !== generation())
      throw new Error('Сессия завершена. Войдите снова');
    return fn();
  });
}
class SessionError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}
async function cookie(action: string, body?: URLSearchParams) {
  const response = await fetch(`/api/auth/browser/${action}`, {
    method: 'POST',
    credentials: 'same-origin',
    signal: AbortSignal.timeout(30000),
    headers: {
      'X-LGG-Request': 'browser',
      'Content-Type': body
        ? 'application/x-www-form-urlencoded'
        : 'application/json',
    },
    body: body || '{}',
  });
  if (!response.ok)
    throw new SessionError(
      response.status === 401
        ? 'Неверный логин или пароль либо срок сессии истёк'
        : response.status === 429
          ? 'Слишком много попыток. Попробуйте позже'
          : 'Не удалось войти. Попробуйте ещё раз',
      response.status,
    );
  return response.json();
}
async function identify(token: string) {
  const response = await fetch('/api/users/me', {
    headers: { Authorization: `Bearer ${token}` },
    signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) throw new Error('Сессия недоступна. Войдите снова');
  const user: User = await response.json();
  if (!['student', 'teacher', 'admin'].includes(user.role))
    throw new Error('Нет доступа');
  if (identity !== undefined && identity !== user.id) {
    cleanups.forEach((fn) => fn());
    channel?.postMessage({ type: 'account-change', userId: user.id });
  }
  identity = user.id;
  access = token;
  emit({ status: 'ready', user });
}
export const session = {
  accessToken: () => access,
  expire: () => {
    access = undefined;
    emit({
      status: 'signed-out',
      user: identity !== undefined ? state.user : undefined,
      reauth: identity !== undefined,
      message: 'Срок сессии истёк. Войдите снова',
    });
  },
  cleanup: (fn: () => void) => {
    cleanups.add(fn);
    return () => {
      cleanups.delete(fn);
    };
  },
  refresh: () => {
    if (!flight)
      flight = locked(async () => {
        const result = await cookie('refresh');
        await identify(result.access_token);
      })
        .catch((error) => {
          access = undefined;
          emit({
            status: 'signed-out',
            user: identity !== undefined ? state.user : undefined,
            reauth: identity !== undefined,
            message:
              identity === undefined &&
              error instanceof SessionError &&
              error.status === 401
                ? undefined
                : error instanceof TypeError || error instanceof DOMException
                  ? 'Нет связи или превышено время ожидания. Войдите снова'
                  : error instanceof Error
                    ? error.message
                    : 'Нет связи. Повторите вход',
          });
          throw error;
        })
        .finally(() => {
          flight = undefined;
        });
    return flight;
  },
  login: (username: string, password: string) =>
    locked(async () => {
      const result = await cookie(
        'login',
        new URLSearchParams({ username, password }),
      );
      await identify(result.access_token);
      channel?.postMessage({ type: 'account-change', userId: identity });
    }),
  logout: () =>
    locked(async () => {
      await cookie('logout');
      try {
        localStorage.setItem('lgg-logout-generation', crypto.randomUUID());
      } catch {
        /* Broadcast still clears all live tabs; cookie was revoked. */
      }
      clear();
      channel?.postMessage('logout');
    }),
};
export function useSession() {
  return useSyncExternalStore(
    (fn) => {
      listeners.add(fn);
      return () => {
        listeners.delete(fn);
      };
    },
    () => state,
  );
}
export function home(user: User) {
  return user.role === 'teacher'
    ? '/teacher'
    : user.role === 'admin'
      ? '/admin/users'
      : '/student';
}
export function safeReturn(path: string | null, user: User) {
  return path &&
    (['/profile', '/notifications'].includes(path) ||
      new RegExp(`^/${user.role}(?:/[a-zA-Z0-9_-]+)*$`).test(path))
    ? path
    : home(user);
}
export function currentUser() {
  return state.user;
}
