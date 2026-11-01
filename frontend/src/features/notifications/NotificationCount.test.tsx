import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { NotificationCount } from './NotificationCount';
const { read } = vi.hoisted(() => ({ read: vi.fn() }));
vi.mock('./api', () => ({ useNotices: read }));
it('badge follows unread count without displaying zero or losing the full count', () => {
  read.mockReturnValue({ data: { unread: 0 } });
  const { container, rerender } = render(<NotificationCount variant="badge" />);
  expect(container).toBeEmptyDOMElement();
  for (const count of [1, 3, 99, 120]) {
    read.mockReturnValue({ data: { unread: count } });
    rerender(<NotificationCount variant="badge" />);
    expect(screen.getByLabelText(`Непрочитанных: ${count}`)).toHaveTextContent(
      count > 99 ? '99+' : String(count),
    );
  }
});
it('does not invent a count during loading or a metadata error; keeps cached count', () => {
  read.mockReturnValue({ isPending: true });
  const { container, rerender } = render(<NotificationCount variant="badge" />);
  expect(container).toBeEmptyDOMElement();
  read.mockReturnValue({ isError: true });
  rerender(<NotificationCount variant="badge" />);
  expect(
    screen.getByText('Число непрочитанных недоступно'),
  ).toBeInTheDocument();
  expect(screen.queryByLabelText(/Непрочитанных:/)).not.toBeInTheDocument();
  read.mockReturnValue({ isError: true, data: { unread: 2 } });
  rerender(<NotificationCount variant="badge" />);
  expect(screen.getByLabelText('Непрочитанных: 2')).toHaveTextContent('2');
});
it('preserves the teacher default text including zero', () => {
  read.mockReturnValue({ data: { unread: 0 } });
  render(<NotificationCount />);
  expect(screen.getByLabelText('Непрочитанных: 0')).toHaveTextContent('(0)');
});
