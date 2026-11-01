import {
  AdminCoursesPage,
  AdminCoursePage,
} from '../features/admin/courses/CoursesPage';
import { AdminLessonPage } from '../features/admin/courses/LessonPage';
import { AuditPage } from '../features/admin/audit/AuditPage';
import {
  UsersPage,
  UserPage,
  CreateUserPage,
} from '../features/admin/users/UsersPage';
import { ReviewQueuePage } from '../features/review/ReviewQueuePage';
import { ReviewPage } from '../features/review/ReviewPage';
import { TeacherDayPage } from '../features/review/TeacherDayPage';
import { TeacherSchedulePage } from '../features/schedule/TeacherSchedulePage';
import { TeacherLessonPage } from '../features/lessons/TeacherLessonPage';
import {
  createBrowserRouter,
  Navigate,
  useRouteError,
  useNavigate,
  Routes,
  Route,
} from 'react-router';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@mantine/core';
import { useEffect, useState, useContext } from 'react';
import { useLocation } from 'react-router';
import { ReauthOverlay } from '../features/auth/ReauthOverlay';
import { LoginPage } from '../features/auth/LoginPage';
import { ActivationPage } from '../features/auth/ActivationPage';
import { ResetPage } from '../features/auth/ResetPage';
import { DraftContext } from './DraftProvider';
import { ConfirmDialog } from '../shared/ui/ConfirmDialog';
import { session, useSession, home } from '../features/auth/session';
import { LinkButton } from '../shared/ui/LinkButton';
import { AppShell } from '../shared/ui/AppShell';
import styles from '../shared/ui/ui.module.css';
import { StudentsPage, StudentPage } from '../features/students/StudentsPage';
import {
  TeacherCoursesPage,
  TeacherCoursePage,
} from '../features/courses/TeacherCoursesPage';
import { MyDayPage } from '../features/courses/MyDayPage';
import { CoursesPage, CoursePage } from '../features/courses/CoursesPage';
import { LessonPage } from '../features/lessons/LessonPage';
import { HomeworkListPage } from '../features/homeworks/HomeworkListPage';
import { HomeworkPage } from '../features/homeworks/HomeworkPage';
import { SchedulePage } from '../features/schedule/SchedulePage';
import { MaterialPage } from '../features/materials/MaterialsPage';
import { StudentLessonsPage } from '../features/courses/StudentLessonsPage';
import { NotificationsPage } from '../features/notifications/NotificationsPage';
import { ProfilePage } from '../features/profile/ProfilePage';
export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} — LGG`;
  }, [title]);
}
function MissingSection({ role }: { role: 'student' | 'teacher' | 'admin' }) {
  usePageTitle('Страница не найдена');
  return (
    <section className={styles.panel}>
      <h1>Страница не найдена</h1>
      <p>Проверьте адрес или откройте нужный раздел в меню.</p>
      <LinkButton to={role === 'admin' ? '/admin/users' : `/${role}`}>
        {role === 'admin' ? 'К пользователям' : 'В мой день'}
      </LinkButton>
    </section>
  );
}
function Guard() {
  const auth = useSession();
  const queryClient = useQueryClient();
  useEffect(() => {
    if (auth.status === 'ready' && !auth.reauth)
      void queryClient.invalidateQueries({
        predicate: (query) => query.state.status === 'error',
      });
  }, [auth.status, auth.reauth, queryClient]);
  const location = useLocation();
  const [logoutError, setLogoutError] = useState('');
  const [logoutConfirm, setLogoutConfirm] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const drafts = useContext(DraftContext);
  async function logout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await session.logout();
    } catch {
      setLogoutError('Не удалось подтвердить выход. Повторите попытку');
    } finally {
      setLoggingOut(false);
    }
  }
  useEffect(() => {
    if (auth.status === 'boot') void session.refresh().catch(() => {});
  }, [auth.status]);
  useEffect(() => {
    if (
      (!auth.user ||
        !['student', 'teacher', 'admin'].includes(auth.user.role)) &&
      !['/profile', '/notifications'].includes(location.pathname)
    )
      document.title = `${auth.user ? 'Кабинет' : 'Вход'} — LGG`;
  }, [auth.user, location.pathname]);
  if (auth.status === 'boot')
    return (
      <AppShell>
        <p role="status">Восстанавливаем сессию…</p>
      </AppShell>
    );
  if (!auth.user)
    return auth.reauth ? (
      <LoginPage reauth />
    ) : (
      <Navigate
        to={'/login?returnTo=' + encodeURIComponent(location.pathname)}
        replace
      />
    );
  if (location.pathname === '/')
    return <Navigate to={home(auth.user)} replace />;
  const prefix = location.pathname.split('/')[1];
  if (
    ['student', 'teacher', 'admin'].includes(prefix) &&
    prefix !== auth.user.role
  )
    return <ErrorPage code={403} />;
  return (
    <AppShell role={auth.user.role}>
      <ReauthOverlay />
      {location.pathname === '/profile' ? (
        <ProfilePage key={auth.user.id} />
      ) : location.pathname === '/notifications' ? (
        <NotificationsPage key={auth.user.id} />
      ) : prefix === 'student' && auth.user.role === 'student' ? (
        <Routes>
          <Route index element={<MyDayPage />} />
          <Route path="materials" element={<StudentLessonsPage />} />
          <Route path="materials/:lectureId" element={<MaterialPage />} />
          <Route path="homeworks" element={<HomeworkListPage />} />
          <Route path="homeworks/:homeworkId" element={<HomeworkPage />} />
          <Route path="schedule" element={<SchedulePage />} />
          <Route path="courses" element={<CoursesPage />} />
          <Route path="courses/:courseId" element={<CoursePage />} />
          <Route path="lessons/:lessonId" element={<LessonPage />} />
          <Route path="*" element={<MissingSection role="student" />} />
        </Routes>
      ) : prefix === 'teacher' && auth.user.role === 'teacher' ? (
        <Routes key={auth.user.id}>
          <Route index element={<TeacherDayPage />} />
          <Route path="review" element={<ReviewQueuePage />} />
          <Route
            path="review/:submissionId"
            element={
              <ReviewPage
                key={
                  location.pathname +
                  new URLSearchParams(location.search).get('homework_id')
                }
              />
            }
          />
          <Route path="schedule" element={<TeacherSchedulePage />} />
          <Route
            path="lessons/:lessonId"
            element={<TeacherLessonPage key={location.pathname} />}
          />
          <Route path="students" element={<StudentsPage />} />
          <Route
            path="students/:userId"
            element={<StudentPage key={location.pathname} />}
          />
          <Route
            path="courses"
            element={<Navigate to="/teacher/students" replace />}
          />
          <Route path="archive" element={<TeacherCoursesPage archiveOnly />} />
          <Route
            path="courses/new"
            element={<Navigate to="/teacher/students" replace />}
          />
          <Route
            path="courses/:courseId"
            element={<TeacherCoursePage key={location.pathname} />}
          />
          <Route path="*" element={<MissingSection role="teacher" />} />
        </Routes>
      ) : prefix === 'admin' && auth.user.role === 'admin' ? (
        <Routes key={auth.user.id}>
          <Route index element={<Navigate to="/admin/users" replace />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="users/new" element={<CreateUserPage />} />
          <Route
            path="users/:userId"
            element={<UserPage key={location.pathname} />}
          />
          <Route path="courses" element={<AdminCoursesPage />} />
          <Route
            path="courses/:courseId"
            element={<AdminCoursePage key={location.pathname} />}
          />
          <Route
            path="lessons/:lessonId"
            element={<AdminLessonPage key={location.pathname} />}
          />
          <Route path="audit" element={<AuditPage />} />
          <Route path="*" element={<MissingSection role="admin" />} />
        </Routes>
      ) : (
        <section className={styles.panel}>
          <h1>Вход выполнен</h1>
          <p>{auth.user.username}, ваша сессия активна.</p>
          <p>Учебные разделы будут подключены на следующем этапе.</p>
        </section>
      )}
      <div className={styles.sessionActions}>
        <Button
          variant="default"
          loading={loggingOut}
          onClick={() => {
            if (
              [...drafts.values()].some((value) =>
                value && typeof value === 'object' && 'dirty' in value
                  ? value.dirty
                  : true,
              )
            )
              setLogoutConfirm(true);
            else void logout();
          }}
        >
          Выйти
        </Button>
        <ConfirmDialog
          opened={logoutConfirm}
          title="Выйти из кабинета?"
          confirmLabel="Выйти"
          pending={loggingOut}
          error={logoutError}
          onCancel={() => setLogoutConfirm(false)}
          onConfirm={() => {
            void logout();
          }}
        >
          Несохранённая работа в этой вкладке будет удалена.
        </ConfirmDialog>
        {logoutError && <p role="alert">{logoutError}</p>}
      </div>
    </AppShell>
  );
}
export function ErrorPage({ code = 404 }: { code?: number }) {
  const error = useRouteError();
  const navigate = useNavigate();
  const actual = error ? 500 : code;
  const title =
    actual === 403
      ? 'Нет доступа'
      : actual === 404
        ? 'Страница не найдена'
        : 'Не удалось открыть страницу';
  usePageTitle(title);
  return (
    <AppShell>
      <section className={`${styles.panel} ${styles.login}`}>
        <h1>{title}</h1>
        <p>
          {actual === 403
            ? 'Доступ к этому материалу ограничен.'
            : actual === 404
              ? 'Проверьте адрес или вернитесь на предыдущую страницу.'
              : 'Попробуйте открыть страницу ещё раз.'}
        </p>
        <div className={styles.actions}>
          <Button
            variant="default"
            onClick={() => {
              if (window.history.state?.idx > 0) navigate(-1);
              else navigate('/login');
            }}
          >
            Назад
          </Button>
          <LinkButton to="/login">К странице входа</LinkButton>
        </div>
      </section>
    </AppShell>
  );
}
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Guard />,
    errorElement: <ErrorPage />,
  },
  { path: '/login', element: <LoginPage />, errorElement: <ErrorPage /> },
  ...(import.meta.env.DEV
    ? [
        {
          path: '/__ui',
          lazy: () =>
            import('../dev/Gallery').then((module) => ({
              Component: module.Gallery,
            })),
          errorElement: <ErrorPage />,
        },
        {
          path: '/__ui/files',
          lazy: () =>
            import('../dev/FilesLab').then((module) => ({
              Component: module.FilesLab,
            })),
          errorElement: <ErrorPage />,
        },
      ]
    : []),
  { path: '/activate', element: <ActivationPage /> },
  { path: '/reset-password', element: <ResetPage /> },
  { path: '/403', element: <ErrorPage code={403} /> },
  { path: '/student/*', element: <Guard /> },
  { path: '/teacher/*', element: <Guard /> },
  { path: '/admin/*', element: <Guard /> },
  { path: '/profile', element: <Guard /> },
  { path: '/notifications', element: <Guard /> },
  { path: '*', element: <ErrorPage /> },
]);
