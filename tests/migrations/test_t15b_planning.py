"""Norm/reminder migration preserves prior recipient rows and refuses history loss."""
from tests.migrations.test_baseline import database, alembic, assert_schema


def test_norm_upgrade_prior_state_constraints_and_history_guard(database):
    conf, sql = database
    alembic('upgrade', 'bc4873ad378e')
    sql("INSERT INTO users(id,username,role,hashed_password,is_active) VALUES(1,'synthetic_norm_t','teacher','synthetic',true),(2,'synthetic_norm_s','student','synthetic',true)")
    sql("INSERT INTO teachers(id,user_id,first_name,last_name) VALUES(1,1,'Synthetic','Teacher')")
    sql("INSERT INTO students(id,user_id,first_name,last_name) VALUES(1,2,'Synthetic','Student')")
    sql("INSERT INTO courses(id,teacher_id,name,slug,avatar_type,is_deleted) VALUES(1,1,'Synthetic','synthetic_norm','default',false)")
    sql("INSERT INTO lessons(id,teacher_id,course_id,title,is_deleted) VALUES(1,1,1,'Prior lesson',false)")
    sql("INSERT INTO lesson_students(id,lesson_id,student_id) VALUES(1,1,1)")
    alembic('upgrade','head');assert_schema(conf)
    assert sql('SELECT homework_not_needed,lecture_not_needed FROM lesson_students') == [(False, False)]
    sql("INSERT INTO weekly_lesson_norms(teacher_id,student_id,week,kind,target) VALUES(1,1,'2026-10-19','exception',2)")
    revision_before = sql("SELECT version_num FROM alembic_version")
    failed=alembic('downgrade','bc4873ad378e',success=False)
    assert 'Refusing to discard weekly norm or reminder history' in failed.stderr
    assert sql('SELECT version_num FROM alembic_version')==revision_before
    sql('DELETE FROM weekly_lesson_norms')
    sql('UPDATE lesson_students SET homework_not_needed=true')
    assert 'Refusing to discard weekly norm or reminder history' in alembic('downgrade','bc4873ad378e',success=False).stderr
    sql('UPDATE lesson_students SET homework_not_needed=false')
    alembic('downgrade','bc4873ad378e')
    assert sql('SELECT lesson_id,student_id FROM lesson_students')==[(1,1)]
    alembic('upgrade','head');assert_schema(conf)
