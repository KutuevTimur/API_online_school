import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronLeft,
  Clock3,
  FileText,
  Video,
} from 'lucide-react';
import { Button } from '@mantine/core';
import { useSearchParams } from 'react-router';
import { useEffect, useRef, useState } from 'react';
import { roleNavigation } from '../shared/ui/AppShell';
import { ConfirmDialog } from '../shared/ui/ConfirmDialog';
import styles from './StudentPreview.module.css';

type Example =
  'homework' | 'result' | 'lesson' | 'geometry' | 'courses' | 'assignments';
export function StudentPreview() {
  const [params, setParams] = useSearchParams();
  const [meeting, setMeeting] = useState(false);
  const section = params.get('section');
  const sectionExample =
    section === '/student/courses'
      ? 'courses'
      : section === '/student/homeworks'
        ? 'assignments'
        : section === '/student/schedule'
          ? 'lesson'
          : section && section !== '/student'
            ? 'unavailable'
            : null;
  const example = params.get('example') || sectionExample;
  const sectionLabel =
    Object.values(roleNavigation)
      .flat()
      .find(([, path]) => path === section)?.[0] ||
    (section === '/notifications'
      ? 'Уведомления'
      : section === '/profile'
        ? 'Профиль'
        : 'Конспекты');
  const mounted = useRef(false);
  useEffect(() => {
    if (mounted.current) document.getElementById('preview-heading')?.focus();
    mounted.current = true;
  }, [example]);
  function open(value?: Example) {
    const next = new URLSearchParams(params);
    if (value) next.set('example', value);
    else next.delete('example');
    next.set(
      'section',
      value === 'courses'
        ? '/student/courses'
        : value === 'homework' || value === 'assignments' || value === 'result'
          ? '/student/homeworks'
          : '/student',
    );
    setParams(next);
  }
  return (
    <section className={styles.preview} aria-label="Пример кабинета ученика">
      <div className={styles.notice}>
        <span className={styles.exampleTag}>Пример кабинета</span>
        <span>Искусственные данные · вход ещё не подключён</span>
        <a href="#technical-components">Компоненты</a>
      </div>
      {example ? (
        <>
          <button className={styles.back} onClick={() => open()}>
            <ChevronLeft size={18} aria-hidden="true" />
            Мой день
          </button>
          <div className={styles.heading}>
            <div>
              <h1 id="preview-heading" tabIndex={-1}>
                {example === 'homework'
                  ? 'Квадратные уравнения'
                  : example === 'result'
                    ? 'Результат проверки'
                    : example === 'lesson'
                      ? 'Математика'
                      : example === 'geometry'
                        ? 'Геометрия'
                        : example === 'assignments'
                          ? 'Домашние задания'
                          : example === 'unavailable'
                            ? sectionLabel
                            : 'Мои курсы'}
              </h1>
              <p>
                {example === 'courses'
                  ? 'Занятия, материалы и задания по каждому предмету.'
                  : example === 'geometry'
                    ? 'Геометрия · Анна Смирнова'
                    : example === 'unavailable'
                      ? 'Пример навигации · раздел в разработке'
                      : 'Пример учебных данных'}
              </p>
            </div>
          </div>
          {example === 'homework' && (
            <div className={styles.workGrid}>
              <section className={styles.whitePanel}>
                <div className={styles.subject}>
                  <FileText size={20} aria-hidden="true" />
                  Домашнее задание
                </div>
                <h2>Что нужно сделать</h2>
                <p>
                  Реши уравнения из файла. Запиши ход решения и проверку корней.
                  Прикрепи фотографии тетради или напиши ответ.
                </p>
                <div className={styles.file}>
                  <FileText aria-hidden="true" />
                  <div>
                    <strong>Квадратные уравнения.pdf</strong>
                    <span>PDF · учебный пример, файл не подключён</span>
                  </div>
                </div>
                <p className={styles.deadline}>
                  <Clock3 size={16} aria-hidden="true" />
                  До 16 октября, 17:00 МСК
                </p>
              </section>
              <section className={styles.answerPanel}>
                <h2>Мой ответ</h2>
                <p>
                  Здесь будут текст решения, фотографии и отправка
                  преподавателю.
                </p>
                <p>
                  В этом примере ответ не сохраняется. Отправка появится после
                  подключения кабинета.
                </p>
                <Button variant="default" onClick={() => open()}>
                  Вернуться к заданиям
                </Button>
              </section>
            </div>
          )}
          {example === 'result' && (
            <section className={styles.resultPanel}>
              <span className={styles.checked}>
                <Check size={16} aria-hidden="true" />
                Проверено
              </span>
              <h2>Треугольники</h2>
              <div className={styles.score}>
                4 <span>из 5</span>
              </div>
              <p>
                Ход решения верный. В последнем задании внимательнее запиши
                обоснование — одного ответа недостаточно.
              </p>
              <p className={styles.resultAuthor}>
                Анна Смирнова · пример комментария
              </p>
              <Button variant="default" onClick={() => open()}>
                К моему дню
              </Button>
            </section>
          )}
          {(example === 'lesson' || example === 'geometry') && (
            <section className={styles.lessonPanel}>
              <div className={styles.lessonTop}>
                <span>Сегодня · 15 октября</span>
                <span className={styles.online}>
                  <Video size={15} aria-hidden="true" />
                  Онлайн
                </span>
              </div>
              <h2>
                {example === 'geometry'
                  ? 'Треугольники'
                  : 'Квадратные уравнения'}
              </h2>
              <p>Анна Смирнова · 17:00–17:55 МСК</p>
              <div className={styles.lessonActions}>
                <Button
                  leftSection={<Video size={18} />}
                  onClick={() => setMeeting(true)}
                >
                  Подключиться
                </Button>
                <button
                  className={styles.textAction}
                  onClick={() =>
                    open(example === 'geometry' ? 'result' : 'homework')
                  }
                >
                  {example === 'geometry'
                    ? 'Посмотреть результат'
                    : 'Открыть задание'}
                  <ArrowRight size={17} aria-hidden="true" />
                </button>
              </div>
            </section>
          )}
          {example === 'unavailable' && (
            <section className={styles.whitePanel}>
              <h2>Этот раздел ещё подключается</h2>
              <p>
                Сейчас можно посмотреть главный экран, пример задания, занятия и
                результата проверки.
              </p>
              <Button variant="default" onClick={() => open()}>
                Посмотреть мой день
              </Button>
            </section>
          )}
          {example === 'assignments' && (
            <div className={styles.courseGrid}>
              <section className={styles.answerPanel}>
                <span className={styles.subject}>
                  Математика · к выполнению
                </span>
                <h2>Квадратные уравнения</h2>
                <p>До 16 октября, 17:00 МСК</p>
                <Button onClick={() => open('homework')}>
                  Открыть задание
                </Button>
              </section>
              <section className={styles.resultPanel}>
                <span className={styles.checked}>
                  <Check size={16} aria-hidden="true" />
                  Проверено · 4 из 5
                </span>
                <h2>Треугольники</h2>
                <p>Есть комментарий преподавателя</p>
                <Button variant="default" onClick={() => open('result')}>
                  Посмотреть результат
                </Button>
              </section>
            </div>
          )}
          {example === 'courses' && (
            <CourseCards
              onOpen={(name) =>
                open(name === 'Геометрия' ? 'geometry' : 'lesson')
              }
            />
          )}
        </>
      ) : (
        <>
          <div className={styles.heading}>
            <div>
              <h1 id="preview-heading" tabIndex={-1}>
                Привет, Иван<span>.</span>
              </h1>
              <p>Ближайшее занятие и всё, что нужно сделать.</p>
            </div>
            <span className={styles.date}>Четверг, 15 октября</span>
          </div>
          <div className={styles.overviewGrid}>
            <section
              className={styles.lessonPanel}
              aria-label="Ближайшее занятие"
            >
              <div className={styles.lessonTop}>
                <span>Сегодня · ближайшее занятие</span>
                <span className={styles.online}>
                  <Video size={15} aria-hidden="true" />
                  Онлайн
                </span>
              </div>
              <h2>Математика</h2>
              <p className={styles.topic}>Квадратные уравнения</p>
              <div className={styles.timeRow}>
                <div className={styles.time}>
                  17:00–17:55 <span>МСК</span>
                </div>
                <span className={styles.mathMark} aria-hidden="true">
                  x²
                </span>
              </div>
              <div className={styles.lessonFooter}>
                <div className={styles.teacher}>
                  Преподаватель<strong>Анна Смирнова</strong>
                </div>
                <Button
                  leftSection={<Video size={18} aria-hidden="true" />}
                  onClick={() => setMeeting(true)}
                >
                  Подключиться
                </Button>
              </div>
            </section>
            <section className={styles.tasksPanel} aria-label="Твои задания">
              <div className={styles.sectionHeading}>
                <h2>Твои задания</h2>
                <button
                  className={styles.textAction}
                  onClick={() => open('assignments')}
                >
                  Все задания
                  <ArrowRight size={17} aria-hidden="true" />
                </button>
              </div>
              <article className={styles.task}>
                <p className={styles.deadline}>
                  <Clock3 size={16} aria-hidden="true" />
                  До 16 октября, 17:00 МСК
                </p>
                <h3>Квадратные уравнения</h3>
                <p>Решение ещё не отправлено</p>
                <button
                  className={styles.textAction}
                  onClick={() => open('homework')}
                >
                  Открыть задание
                  <ArrowUpRight size={17} aria-hidden="true" />
                </button>
              </article>
              <article className={styles.task}>
                <span className={styles.checked}>
                  <Check size={16} aria-hidden="true" />
                  Проверено · 4 из 5
                </span>
                <h3>Треугольники</h3>
                <p>Есть комментарий преподавателя</p>
                <button
                  className={styles.textAction}
                  onClick={() => open('result')}
                >
                  Посмотреть результат
                  <ArrowUpRight size={17} aria-hidden="true" />
                </button>
              </article>
            </section>
          </div>
          <div className={`${styles.sectionHeading} ${styles.coursesHeading}`}>
            <h2>Мои курсы</h2>
            <button
              className={styles.textAction}
              onClick={() => open('courses')}
            >
              Все курсы
              <ArrowRight size={17} aria-hidden="true" />
            </button>
          </div>
          <CourseCards
            onOpen={(name) =>
              open(name === 'Геометрия' ? 'geometry' : 'lesson')
            }
          />
        </>
      )}
      <p className={styles.sampleNote}>
        Демонстрация согласованного оформления. Кнопки открывают примеры; данные
        не отправляются на сервер.
      </p>
      <ConfirmDialog
        opened={meeting}
        onCancel={() => setMeeting(false)}
        onConfirm={() => setMeeting(false)}
        title="Пример онлайн-занятия"
        confirmLabel="Понятно"
      >
        В рабочем кабинете здесь откроется ссылка преподавателя на видеовстречу.
        В этом примере встреча не подключена.
      </ConfirmDialog>
    </section>
  );
}
function CourseCards({ onOpen }: { onOpen: (name: string) => void }) {
  return (
    <div className={styles.courseGrid}>
      {[
        { name: 'Математика', mark: 'x²' },
        { name: 'Геометрия', mark: '∠' },
      ].map((course, index) => (
        <button
          key={course.name}
          className={styles.course}
          aria-label={`Открыть курс ${course.name}`}
          onClick={() => onOpen(course.name)}
        >
          <span
            className={styles.courseMark}
            data-mint={index === 1}
            aria-hidden="true"
          >
            {course.mark}
          </span>
          <span className={styles.courseCopy}>
            <strong>{course.name}</strong>
            <span>Анна Смирнова</span>
          </span>
          <ArrowUpRight size={20} aria-hidden="true" />
        </button>
      ))}
    </div>
  );
}
