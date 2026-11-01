import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { PlainTextLinks } from './PlainTextLinks';

it('accepts an empty or missing optional description', () => {
  const { container } = render(<PlainTextLinks text={null} />);
  expect(container.textContent).toBe('');
  expect(screen.queryByRole('link')).toBeNull();
});

it('preserves text/newlines and trims prose punctuation without breaking balanced URL brackets', () => {
  const text =
    'Задания: (https://example.com/a_(b)).\nhttp://example.org/x?q=1&n=2, затем HTTPS://example.net/!';
  const { container } = render(<PlainTextLinks text={text} />);
  expect(container.textContent).toBe(text);
  const links = screen.getAllByRole('link');
  expect(links.map((link) => link.getAttribute('href'))).toEqual([
    'https://example.com/a_(b)',
    'http://example.org/x?q=1&n=2',
    'HTTPS://example.net/',
  ]);
  for (const link of links) {
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(link).toHaveAccessibleName(/откроется в новой вкладке/);
  }
});

it.each([
  'javascript:alert(1) data:text/html,test file:///tmp/a //example.org/path',
  'javascript:https://example.org data:https://example.org file:https://example.org',
  'https:// https://[bad http://example.org\\evil',
  '<img src=x onerror="alert(1)"><script>alert(1)</script>',
])('leaves unsupported, malformed and HTML input inert: %s', (text) => {
  const { container } = render(<PlainTextLinks text={text} />);
  expect(container.textContent).toBe(text);
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
  expect(container.querySelector('img,script,iframe,embed')).toBeNull();
});

it('keeps full long URLs copyable and links without interpreting surrounding HTML', () => {
  const url = 'https://example.com/' + 'long'.repeat(100);
  const text = `<b>Условие</b>\n${url}`;
  const { container } = render(<PlainTextLinks text={text} />);
  expect(container.textContent).toBe(text);
  expect(screen.getByRole('link')).toHaveTextContent(url);
  expect(container.querySelector('b')).toBeNull();
});
