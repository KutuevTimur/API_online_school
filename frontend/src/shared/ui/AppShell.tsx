import { PageBackButton } from './PageBackButton';
import { NotificationCount } from '../../features/notifications/NotificationCount';
import {
  ArrowUpRight,
  Bell,
  House,
  CalendarDays,
  BookOpen,
  NotebookPen,
  GraduationCap,
  UserRound,
  MoreHorizontal,
  UsersRound,
  ClipboardCheck,
} from 'lucide-react';
import {
  Link,
  useLocation,
  useSearchParams,
  ScrollRestoration,
} from 'react-router';
import { useState, type ReactNode } from 'react';
import { Menu, Drawer, Button as MantineButton } from '@mantine/core';
import styles from './ui.module.css';
export type Role = 'student' | 'teacher' | 'admin';
export const roleNavigation: Record<Role, readonly [string, string][]> = {
  student: [
    ['Мой день', '/student'],
    ['Расписание', '/student/schedule'],
    ['Занятия', '/student/materials'],
    ['Д/з', '/student/homeworks'],
    ['Курсы', '/student/courses'],
  ],
  teacher: [
    ['Мой день', '/teacher'],
    ['Ученики', '/teacher/students'],
    ['Расписание', '/teacher/schedule'],
    ['На проверку', '/teacher/review'],
  ],
  admin: [
    ['Пользователи', '/admin/users'],
    ['Курсы', '/admin/courses'],
    ['Журнал действий', '/admin/audit'],
  ],
};
const navigationIcons = {
  '/student': House,
  '/student/schedule': CalendarDays,
  '/student/materials': BookOpen,
  '/student/homeworks': NotebookPen,
  '/student/courses': GraduationCap,
  '/notifications': Bell,
  '/profile': UserRound,
  '/teacher': House,
  '/teacher/schedule': CalendarDays,
  '/teacher/students': UsersRound,
  '/teacher/review': ClipboardCheck,
};
function NavIcon({ path }: { path: string }) {
  const Icon = navigationIcons[path as keyof typeof navigationIcons];
  return Icon ? <Icon size={18} aria-hidden="true" /> : null;
}
export function AppShell({
  children,
  role,
  preview = false,
}: {
  children: ReactNode;
  role?: Role;
  preview?: boolean;
}) {
  const [menuOpened, setMenuOpened] = useState(false);
  const location = useLocation();
  const [params] = useSearchParams();
  // Detail pages keep their owning section visible in both navigation layouts.
  const pathname = location.pathname.replace(/\/+$/, '') || '/';
  const compact = role === 'student' || role === 'teacher';
  const section =
    role === 'student' &&
    /^\/student\/(lessons|homeworks)\//.test(pathname) &&
    typeof location.state?.studentHistoryReturnTo === 'string' &&
    /^\/student\/materials(?:\?|$)/.test(location.state.studentHistoryReturnTo)
      ? '/student/materials'
      : role === 'admin' && /^\/admin\/lessons\//.test(pathname)
        ? '/admin/courses'
        : /^\/(student|teacher)\/lessons\//.test(pathname)
          ? `/${role}/schedule`
          : role === 'teacher' &&
              /^\/teacher\/(courses|archive)(\/|$)/.test(pathname)
            ? '/teacher/students'
            : pathname;
  const active = (path: string) =>
    import.meta.env.DEV && preview
      ? (params.get('section') || (role ? roleNavigation[role][0][1] : '')) ===
        path
      : section === path ||
        (path !== `/${role}` && section.startsWith(path + '/'));
  const current = (path: string) =>
    active(path) ? (pathname === path ? 'page' : 'location') : undefined;
  const items = role ? roleNavigation[role] : [];
  const href = (path: string) =>
    import.meta.env.DEV && preview
      ? `/__ui?role=${role}&section=${encodeURIComponent(path)}`
      : path;
  const mobile =
    role === 'student'
      ? [items[0], items[2], items[1]]
      : role === 'teacher'
        ? [items[0], items[2], items[3]]
        : items.slice(0, 3);
  return (
    <div
      className={
        role === 'student'
          ? styles.studentShell
          : role === 'teacher'
            ? styles.teacherShell
            : undefined
      }
      data-role={role}
    >
      <ScrollRestoration />
      <a className={styles.skip} href="#main">
        Перейти к содержимому
      </a>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.brandGroup}>
            <PageBackButton role={role} preview={preview} />
            <Link
              className={styles.logo}
              to={role ? href(roleNavigation[role][0][1]) : '/login'}
              aria-label={role ? 'LGG — в свой кабинет' : 'LGG — вход'}
            >
              LGG
              <ArrowUpRight size={25} aria-hidden="true" />
            </Link>
          </div>
          {role ? (
            <nav className={styles.nav} aria-label="Основные разделы">
              {items.map(([label, path]) => (
                <Link key={path} to={href(path)} aria-current={current(path)}>
                  {compact && <NavIcon path={path} />}
                  {label}
                </Link>
              ))}
            </nav>
          ) : (
            <span className={styles.muted}>Онлайн-школа</span>
          )}
          {role && (
            <div
              className={`${styles.account} ${preview ? styles.previewAccount : ''}`}
            >
              <Link
                to={href('/notifications')}
                className={compact ? styles.noticeLink : undefined}
                aria-current={current('/notifications')}
                aria-label={preview ? 'Уведомления' : undefined}
                title="Уведомления"
              >
                {compact && !preview ? (
                  <>
                    <Bell size={20} aria-hidden="true" />
                    <span className={styles.srOnly}>Уведомления</span>
                    <NotificationCount variant="badge" />
                  </>
                ) : import.meta.env.DEV && preview ? (
                  <Bell size={20} aria-hidden="true" />
                ) : (
                  <>
                    Уведомления
                    <NotificationCount />
                  </>
                )}
              </Link>
              <Link
                to={href('/profile')}
                className={compact ? styles.profileLink : undefined}
                aria-current={current('/profile')}
                aria-label="Профиль"
                title="Профиль"
              >
                {import.meta.env.DEV && preview ? (
                  <span className={styles.previewAvatar} aria-hidden="true">
                    {role === 'student'
                      ? 'ИП'
                      : role === 'teacher'
                        ? 'АС'
                        : 'АД'}
                  </span>
                ) : (
                  <>
                    {compact && <UserRound size={20} aria-hidden="true" />}
                    <span>Профиль</span>
                  </>
                )}
              </Link>
            </div>
          )}
          {role === 'admin' && (
            <MantineButton
              className={styles.adminMenu}
              variant="default"
              onClick={() => setMenuOpened(true)}
            >
              Меню
            </MantineButton>
          )}
        </div>
      </header>
      {role === 'admin' && (
        <Drawer
          opened={menuOpened}
          onClose={() => setMenuOpened(false)}
          title="Разделы"
          closeButtonProps={{ 'aria-label': 'Закрыть меню' }}
        >
          <nav className={styles.drawerNav} aria-label="Разделы администратора">
            {items
              .concat([
                ['Уведомления', '/notifications'],
                ['Профиль', '/profile'],
              ])
              .map(([label, path]) => (
                <Link
                  key={path}
                  to={href(path)}
                  onClick={() => setMenuOpened(false)}
                >
                  {label}
                </Link>
              ))}
          </nav>
        </Drawer>
      )}
      <main
        id="main"
        tabIndex={-1}
        className={`${styles.main} ${role === 'teacher' && pathname === '/teacher/schedule' ? styles.teacherScheduleMain : ''}`}
      >
        {children}
      </main>
      {role && role !== 'admin' && (
        <nav className={styles.mobile} aria-label="Разделы на телефоне">
          {mobile.map(([label, path]) => (
            <Link key={path} to={href(path)} aria-current={current(path)}>
              {compact && <NavIcon path={path} />}
              {role === 'teacher' && path === '/teacher/review'
                ? 'Проверка'
                : label === 'Домашние задания'
                  ? 'Домашки'
                  : label}
            </Link>
          ))}
          <Menu
            position="top-end"
            withinPortal={!compact}
            withInitialFocusPlaceholder={!compact}
          >
            <Menu.Target>
              <MantineButton
                variant="subtle"
                data-active={
                  items
                    .filter((item) => !mobile.includes(item))
                    .some(([, path]) => active(path)) ||
                  active('/profile') ||
                  active('/notifications') ||
                  undefined
                }
              >
                {compact && <MoreHorizontal size={18} aria-hidden="true" />}
                <span>Ещё</span>
              </MantineButton>
            </Menu.Target>
            <Menu.Dropdown>
              {items
                .filter((item) => !mobile.includes(item))
                .concat([
                  ['Уведомления', '/notifications'],
                  ['Профиль', '/profile'],
                ])
                .map(([label, path]) => (
                  <Menu.Item
                    key={path}
                    component={Link}
                    leftSection={compact ? <NavIcon path={path} /> : undefined}
                    to={href(path)}
                    aria-current={current(path)}
                  >
                    {label}
                  </Menu.Item>
                ))}
            </Menu.Dropdown>
          </Menu>
        </nav>
      )}
    </div>
  );
}
