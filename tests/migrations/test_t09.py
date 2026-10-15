"""T09 backfill preserves historical attempts and protects downgrade semantics."""
import pytest
from tests.migrations.test_baseline import database, alembic, assert_schema
from tests.migrations.test_t07 import seed


def prior(sql):
    alembic('upgrade','711e94443ef3'); seed(sql)
    alembic('upgrade','29e67248e0f3')
    sql("INSERT INTO homeworks(id,lesson_student_id,title,deadline) VALUES(90,80,'H',now())")


def test_t09_prior_history_backfill_and_unique(database):
    conf,sql=database; prior(sql)
    sql("""INSERT INTO homework_submissions(id,homework_id,attempt_number,status,text_content,grade,teacher_comment,submitted_at)
        VALUES(110,90,1,'checked','old checked',5,'preserved',now()),
              (111,90,2,'submitted','old sent',NULL,NULL,now()),
              (112,90,3,'draft','working',NULL,NULL,now())""")
    sql("INSERT INTO homework_submission_files(id,submission_id,original_file_path) VALUES(120,110,'synthetic-old.pdf')")
    before=sql("SELECT id,homework_id,attempt_number,status::text,text_content,grade,teacher_comment FROM homework_submissions ORDER BY id")
    alembic('upgrade','head'); assert_schema(conf)
    assert sql("SELECT id,homework_id,attempt_number,status::text,text_content,grade,teacher_comment FROM homework_submissions ORDER BY id")==before
    assert sql("SELECT id,is_working,version,submitted_at IS NULL FROM homework_submissions ORDER BY id")==[(110,False,1,False),(111,False,1,False),(112,True,1,True)]
    assert sql('SELECT id,submission_id,original_file_path FROM homework_submission_files')==[(120,110,'synthetic-old.pdf')]
    result=alembic('downgrade','29e67248e0f3',success=False)
    assert 'Cannot discard T09' in result.stderr
    assert sql('SELECT version_num FROM alembic_version')==[('36a8711f7799',)]
    with pytest.raises(Exception,match='uix_homework_working_submission'):
        sql("INSERT INTO homework_submissions(homework_id,attempt_number,status) VALUES(90,4,'draft')")
    assert sql('SELECT count(*) FROM homework_submissions')==[(3,)]


def test_t09_safe_round_trip_and_version_guard(database):
    conf,sql=database; prior(sql)
    sql("INSERT INTO homework_submissions(id,homework_id,attempt_number,status,text_content) VALUES(110,90,1,'draft','preserved')")
    alembic('upgrade','head'); assert_schema(conf)
    alembic('downgrade','29e67248e0f3')
    assert sql('SELECT id,text_content FROM homework_submissions')==[(110,'preserved')]
    alembic('upgrade','head'); assert_schema(conf)
    sql('UPDATE homework_submissions SET version=2')
    result=alembic('downgrade','29e67248e0f3',success=False)
    assert 'Cannot discard T09' in result.stderr
    assert_schema(conf)
    with pytest.raises(Exception,match='ck_submission_version'):
        sql('UPDATE homework_submissions SET version=0')
