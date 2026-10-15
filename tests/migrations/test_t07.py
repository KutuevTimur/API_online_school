"""T07 backfill, ambiguity refusal and rollback protection on synthetic PostgreSQL."""
import pytest
from tests.migrations.test_baseline import database, alembic, assert_schema


def seed(sql):
    sql("""INSERT INTO users (id,username,role,hashed_password,is_active,is_activated,auth_version)
           VALUES (10,'teacher','teacher','dummy',true,true,0),(20,'student','student','dummy',true,true,0)""")
    sql("INSERT INTO teachers(id,user_id,first_name,last_name) VALUES(30,10,'T','Test')")
    sql("INSERT INTO students(id,user_id,first_name,last_name) VALUES(40,20,'S','Test')")
    sql("INSERT INTO courses(id,teacher_id,name,slug,avatar_type,is_deleted) VALUES(50,30,'C','c','default',false)")
    sql("""INSERT INTO student_courses(id,student_id,course_id,is_deleted,deleted_at)
           VALUES(60,40,50,true,'2026-01-01T00:00:00Z')""")
    sql("INSERT INTO lessons(id,course_id,teacher_id,title) VALUES(70,50,30,'L')")
    sql("INSERT INTO lesson_students(id,lesson_id,student_id) VALUES(80,70,40)")


def test_t07_prior_state_cutoff_and_downgrade_guard(database):
    conf,sql=database
    alembic('upgrade','711e94443ef3'); seed(sql)
    alembic('upgrade','head'); assert_schema(conf)
    assert sql("SELECT access_ended_at=deleted_at,history_revoked FROM student_courses")==[(True,False)]
    assert sql("SELECT is_deleted,deleted_at FROM lessons")==[(False,None)]
    sql("UPDATE lessons SET is_deleted=true,deleted_at=now()")
    result=alembic('downgrade','711e94443ef3',success=False)
    assert 'discard' in result.stderr
    assert sql('SELECT version_num FROM alembic_version')==[('8a575436b7db',)]
    assert sql('SELECT count(*) FROM lesson_students')==[(1,)]


def test_t07_duplicate_memberships_refused_before_ddl(database):
    conf,sql=database
    alembic('upgrade','711e94443ef3'); seed(sql)
    sql("INSERT INTO student_courses(id,student_id,course_id,is_deleted) VALUES(61,40,50,false)")
    result=alembic('upgrade','head',success=False)
    assert 'Duplicate course memberships' in result.stderr
    assert sql("SELECT to_regclass('public.file_deletions')")==[(None,)]
    assert sql('SELECT count(*) FROM student_courses')==[(2,)]


def test_t07_dangling_personal_grant_refused_before_ddl(database):
    conf,sql=database
    alembic('upgrade','711e94443ef3');seed(sql)
    sql('DELETE FROM student_courses')
    result=alembic('upgrade','head',success=False)
    assert 'without course membership' in result.stderr
    assert sql("SELECT to_regclass('public.enrollment_gaps')")==[(None,)]
    assert sql('SELECT count(*) FROM lesson_students')==[(1,)]
