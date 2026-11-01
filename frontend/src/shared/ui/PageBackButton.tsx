import { useEffect } from 'react';
import { useLocation, useNavigate, useNavigationType } from 'react-router';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@mantine/core';
import {
  backPlan,
  backStorageKey,
  localBackUrl,
  readBackEntries,
  type BackEntry,
} from '../lib/pageBack';
import styles from './ui.module.css';

export function PageBackButton({
  role,
  preview = false,
}: {
  role?: 'student' | 'teacher' | 'admin';
  preview?: boolean;
}) {
  const location = useLocation(),
    navigate = useNavigate(),
    action = useNavigationType();
  const enabled = !preview && (role === 'student' || role === 'teacher');
  const url = location.pathname + location.search + location.hash;
  const rawIndex = window.history.state?.idx;
  const index =
    Number.isSafeInteger(rawIndex) && rawIndex >= 0
      ? (rawIndex as number)
      : undefined;
  let entries: BackEntry[] = [];
  if (enabled) {
    try {
      entries = readBackEntries(window.sessionStorage, role);
    } catch {
      /* Private storage may be unavailable. */
    }
  }
  const plan = enabled
    ? backPlan(role, url, index, entries, location.state || {})
    : undefined;
  useEffect(() => {
    try {
      if (!enabled) {
        if (!preview) sessionStorage.removeItem(backStorageKey);
        return;
      }
      if (index === undefined || !localBackUrl(url, role)) return;
      const saved = readBackEntries(sessionStorage, role).filter(
        (e) => e.index !== index && (action !== 'PUSH' || e.index < index),
      );
      saved.push({ index, key: location.key, url });
      sessionStorage.setItem(
        backStorageKey,
        JSON.stringify({
          role,
          entries: saved.sort((a, b) => a.index - b.index).slice(-80),
        }),
      );
    } catch {
      /* Storage restrictions keep the explicit origin/parent fallback usable. */
    }
  }, [enabled, preview, role, index, action, location.key, url]);
  if (!enabled || !plan) return null;
  const disabled =
    !plan.delta && plan.to.split(/[?#]/)[0] === location.pathname;
  return (
    <Button
      className={styles.pageBack}
      variant="subtle"
      aria-label="Назад"
      title={disabled ? 'Предыдущей страницы нет' : 'Назад'}
      disabled={disabled}
      onClick={() => {
        if (plan.delta) void navigate(-plan.delta);
        else
          void navigate(plan.to, {
            replace: true,
            state: {
              ...location.state,
              restoreHistoryScroll: location.state?.studentHistoryScroll,
            },
          });
      }}
    >
      <ArrowLeft size={20} aria-hidden="true" />
    </Button>
  );
}
