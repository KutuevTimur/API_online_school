import {
  studentAnswerLabels,
  type StudentAnswerState,
} from '../lib/studentAnswerState';
import styles from './ui.module.css';
const statuses = {
  draft: ['Черновик', 'neutral'],
  submitted: ['На проверке', 'neutral'],
  checked: ['Проверено', 'success'],
  archived: ['В архиве', 'neutral'],
  error: ['Ошибка', 'error'],
} as const;
export function StatusBadge({ status }: { status: keyof typeof statuses }) {
  const [label, tone] = statuses[status];
  return (
    <span className={styles.badge} data-tone={tone}>
      {label}
    </span>
  );
}

// Student waiting means their part is complete; teacher queue tones stay unchanged.
export function StudentAnswerBadge({ state }: { state: StudentAnswerState }) {
  return (
    <span className={styles.studentAnswerBadge} data-state={state}>
      {studentAnswerLabels[state]}
    </span>
  );
}
