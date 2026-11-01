import { useEffect } from 'react';
// Mantine owns focus trapping/return. Native inert additionally isolates our app
// document from pointer and screen-reader access while body portals are open.
let owners = 0;
let previous: { inert: boolean; hidden: string | null } | undefined;
export function useModalIsolation(opened: boolean) {
  useEffect(() => {
    if (!opened) return;
    const root = document.getElementById('root');
    if (!root) return;
    if (owners++ === 0) {
      previous = {
        inert: root.inert,
        hidden: root.getAttribute('aria-hidden'),
      };
      root.inert = true;
      root.setAttribute('aria-hidden', 'true');
    }
    return () => {
      if (--owners === 0 && previous) {
        root.inert = previous.inert;
        if (previous.hidden === null) root.removeAttribute('aria-hidden');
        else root.setAttribute('aria-hidden', previous.hidden);
        previous = undefined;
      }
    };
  }, [opened]);
}
