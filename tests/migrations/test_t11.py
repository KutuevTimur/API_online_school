"""Prior T10 deadlines are retained before the automatic rule is installed."""
import pytest
from tests.migrations.test_baseline import database, alembic, assert_schema
from tests.migrations.test_t09 import prior


def test_t11_prior_manual_deadlines_and_checked_preserved(database):
    conf,sql=database; prior(sql)
    alembic('upgrade','8a575436b7db')
    sql('UPDATE student_courses SET is_deleted=false,access_ended_at=NULL,deleted_at=NULL')
    sql("UPDATE lessons SET scheduled_at='2026-10-19T12:00:00Z' WHERE id=70")
    sql("UPDATE homeworks SET deadline='2026-10-21T12:00:00Z' WHERE id=90")
    sql("INSERT INTO homeworks(id,lesson_student_id,title,deadline) VALUES(91,80,'Checked','2026-10-20T12:00:00Z')")
    sql("INSERT INTO homework_submissions(id,homework_id,attempt_number,status,grade,checked_at) VALUES(110,91,1,'checked',4,'2026-10-20T14:00:00Z')")
    sql("INSERT INTO lessons(id,course_id,teacher_id,title,scheduled_at,is_deleted) VALUES(71,50,30,'Next','2026-10-22T12:00:00Z',false)")
    sql("INSERT INTO lesson_students(id,lesson_id,student_id) VALUES(81,71,40)")
    before=sql('SELECT id,deadline FROM homeworks ORDER BY id')
    alembic('upgrade','head'); assert_schema(conf)
    rows=sql('SELECT id,deadline,deadline_frozen_at IS NOT NULL FROM homeworks ORDER BY id')
    assert rows[0][1].isoformat()=='2026-10-22T12:00:00+00:00' and rows[0][2] is False
    assert rows[1][1]==before[1][1] and rows[1][2] is True
    assert sql("SELECT count(*) FROM homework_deadline_events WHERE reason='legacy_import'")==[(2,)]
    assert sql('SELECT count(*) FROM homework_placements')==[(2,)]
    assert sql('SELECT grade::int FROM homework_submissions')==[(4,)]
    # Pristine migration backfill can restore legacy manual deadlines without loss.
    alembic('downgrade','8a575436b7db')
    assert sql('SELECT id,deadline FROM homeworks ORDER BY id')==before
    alembic('upgrade','head'); assert_schema(conf)


def test_t11_null_no_next_and_history_downgrade_guard(database):
    conf,sql=database; prior(sql)
    alembic('upgrade','8a575436b7db')
    sql('UPDATE student_courses SET is_deleted=false,access_ended_at=NULL,deleted_at=NULL')
    alembic('upgrade','head'); assert_schema(conf)
    assert sql('SELECT deadline FROM homeworks')==[(None,)]
    pid=sql('SELECT id FROM homework_placements')[0][0]
    sql(f"INSERT INTO homework_deadline_events(placement_id,lesson_student_id,reason) VALUES({pid},80,'lesson_updated')")
    result=alembic('downgrade','8a575436b7db',success=False)
    assert 'Cannot discard T11' in result.stderr
    assert sql('SELECT version_num FROM alembic_version')==[('36a8711f7799',)]
    assert_schema(conf)
    with pytest.raises(Exception,match='uq_homework_placement|uix_homework_original_placement'):
        sql("INSERT INTO homework_placements(homework_id,lesson_student_id,kind) VALUES(90,80,'original')")
    with pytest.raises(Exception,match='ck_placement_kind'):
        sql("UPDATE homework_placements SET kind='cycle'")


def test_t11_detached_and_archived_legacy_deadline_remains_history(database):
    conf,sql=database; prior(sql)
    before=sql('SELECT deadline FROM homeworks')
    alembic('upgrade','head'); assert_schema(conf)
    assert sql('SELECT deadline FROM homeworks')==before
    assert sql('SELECT due_lesson_id,due_at FROM homework_placements')==[(None,before[0][0])]
    assert sql('SELECT reason FROM homework_deadline_events')==[('legacy_import',)]
