import type { ReactNode } from 'react';
import styles from './plainTextLinks.module.css';

// Text nodes keep HTML inert. Only standalone, absolute HTTP(S) URLs become links.
export function PlainTextLinks({ text: value }: { text?: string | null }) {
  const text = value ?? '';
  const parts: ReactNode[] = [];
  const pattern = /(^|[\s([{«])https?:\/\/[^\s<>"'»]+/gi;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    const start = match.index + match[1].length;
    let url = match[0].slice(match[1].length);
    // Keep balanced brackets in URLs, but leave sentence punctuation as text.
    while (url) {
      const last = url.at(-1)!;
      const opening =
        last === ')' ? '(' : last === ']' ? '[' : last === '}' ? '{' : '';
      if (
        /[.,!?;:]/.test(last) ||
        (opening && url.split(last).length > url.split(opening).length)
      )
        url = url.slice(0, -1);
      else break;
    }
    try {
      const parsed = new URL(url);
      if (
        !['http:', 'https:'].includes(parsed.protocol) ||
        !parsed.hostname ||
        url.includes('\\') ||
        Array.from(url).some(
          (char) => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127,
        )
      )
        continue;
    } catch {
      continue;
    }
    parts.push(text.slice(cursor, start));
    parts.push(
      <a
        key={start}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`${url} (откроется в новой вкладке)`}
      >
        {url}
      </a>,
    );
    cursor = start + url.length;
  }
  parts.push(text.slice(cursor));
  return <span className={styles.text}>{parts}</span>;
}
