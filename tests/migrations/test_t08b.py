"""Regular batches preserve prior lessons and refuse lossy history downgrade."""
from tests.migrations.test_baseline import database, alembic, assert_schema


def test_regular_upgrade_prior_rows_constraints_and_downgrade(database):
    conf, sql=database
    alembic('upgrade','26ec46040b4c')
    sql("INSERT INTO users(id,username,role,hashed_password,is_active,is_activated,auth_version) VALUES(1,'synthetic_t08b_teacher','teacher','synthetic',true,true,0),(2,'synthetic_t08b_student','student','synthetic',true,true,0)")
    sql("INSERT INTO teachers(id,user_id,first_name,last_name) VALUES(1,1,'Synthetic','Teacher')")
    sql("INSERT INTO students(id,user_id,first_name,last_name) VALUES(1,2,'Synthetic','Student')")
    sql("INSERT INTO courses(id,teacher_id,name,slug,avatar_type,is_deleted) VALUES(1,1,'Synthetic','synthetic_t08b','default',false)")
    sql("INSERT INTO lessons(id,teacher_id,course_id,title,scheduled_at,is_deleted) VALUES(1,1,1,'Prior lesson','2028-12-25T12:00:00Z',false)")
    before=sql('SELECT id,title,scheduled_at FROM lessons')
    alembic('upgrade','head'); assert_schema(conf)
    assert sql('SELECT id,title,scheduled_at FROM lessons')==before
    assert sql('SELECT regular_series_id,regular_original_at FROM lessons')==[(None,None)]
    constraints=sql("SELECT conname FROM pg_constraint WHERE conrelid='lessons'::regclass")
    assert {'ck_lesson_regular_pair','uq_lesson_regular_occurrence','fk_lesson_regular_series'} <= {r[0] for r in constraints}
    sid='00000000-0000-0000-0000-000000000008'
    sql(f"INSERT INTO regular_lesson_series(id,teacher_id,course_id,student_user_id,spec,anchor_at,through_at) VALUES('{sid}',1,1,2,'{{}}','2028-12-25T12:00:00Z','2028-12-25T12:00:00Z')")
    sql(f"UPDATE lessons SET regular_series_id='{sid}',regular_original_at=scheduled_at")
    revision_before = sql("SELECT version_num FROM alembic_version")
    failed=alembic('downgrade','26ec46040b4c',success=False)
    assert 'Refusing to discard regular scheduling history' in failed.stderr
    assert sql('SELECT version_num FROM alembic_version')==revision_before
    assert_schema(conf)
    sql('UPDATE lessons SET regular_series_id=NULL,regular_original_at=NULL')
    sql('DELETE FROM regular_lesson_series')
    alembic('downgrade','26ec46040b4c')
    assert sql('SELECT id,title,scheduled_at FROM lessons')==before
    alembic('upgrade','head');assert_schema(conf)
