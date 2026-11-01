import { Link, useLocation } from 'react-router';

export function studentHistoryOrigin(value: unknown): string | undefined {
  return typeof value === 'string' &&
    /^\/student\/materials(?:\?[^#\\]*)?$/.test(value)
    ? value
    : undefined;
}

// Only history metadata travels with the route; no document bytes or credentials.
export function useStudentHistoryOrigin() {
  const location = useLocation();
  const returnTo = studentHistoryOrigin(location.state?.studentHistoryReturnTo);
  return {
    returnTo,
    state: returnTo ? location.state : undefined,
  };
}

export function StudentHistoryReturn() {
  const origin = useStudentHistoryOrigin();
  return origin.returnTo ? (
    <Link
      to={origin.returnTo}
      state={{ restoreHistoryScroll: origin.state?.studentHistoryScroll }}
      preventScrollReset
    >
      К моим занятиям
    </Link>
  ) : null;
}
