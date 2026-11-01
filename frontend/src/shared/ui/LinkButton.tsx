import { Button as MantineButton, type ButtonProps } from '@mantine/core';
import { Link, type LinkProps } from 'react-router';
import type { ReactNode } from 'react';
import { ArrowRight } from 'lucide-react';
import styles from './navigationButton.module.css';
// Navigation CTA: Mantine renders a semantic anchor through React Router.
export function LinkButton({
  to,
  children,
  navigation = false,
  className,
  rightSection,
  ...props
}: {
  to: string;
  children: ReactNode;
  navigation?: boolean;
  state?: LinkProps['state'];
  title?: string;
  onClick?: LinkProps['onClick'];
} & ButtonProps) {
  return (
    <MantineButton
      component={Link}
      to={to}
      {...props}
      className={[navigation ? styles.navigation : '', className]
        .filter(Boolean)
        .join(' ')}
      rightSection={
        rightSection ??
        (navigation ? <ArrowRight size={18} aria-hidden="true" /> : undefined)
      }
    >
      {children}
    </MantineButton>
  );
}

// External navigation keeps the same canonical button owner and safe new-tab policy.
export function ExternalLinkButton({
  href,
  children,
  variant,
  leftSection,
  studentAction = false,
}: {
  href: string;
  children: ReactNode;
  variant?: ButtonProps['variant'];
  leftSection?: ReactNode;
  studentAction?: boolean;
}) {
  return (
    <MantineButton
      component="a"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      variant={variant}
      leftSection={leftSection}
      className={studentAction ? styles.navigation : undefined}
    >
      {children}
    </MantineButton>
  );
}
