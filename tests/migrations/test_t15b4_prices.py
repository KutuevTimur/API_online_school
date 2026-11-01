from tests.migrations.test_baseline import database, alembic, assert_schema


def test_price_migration_preserves_legacy_and_refuses_history_loss(database):
    conf,sql=database
    alembic('upgrade','11ffc0656a8a')
    sql("INSERT INTO users(id,username,role,hashed_password,is_active) VALUES(1,'synthetic_price_t','teacher','synthetic',true)")
    sql("INSERT INTO teachers(id,user_id,first_name,last_name) VALUES(1,1,'Synthetic','Price')")
    sql("INSERT INTO courses(id,teacher_id,name,slug,avatar_type,is_deleted) VALUES(1,1,'Synthetic','synthetic_price','default',false)")
    sql("INSERT INTO lessons(id,teacher_id,course_id,title,status,is_deleted) VALUES(1,1,1,'Prior completed','completed',false)")
    alembic('upgrade','head');assert_schema(conf)
    assert sql('SELECT lesson_price_kopecks FROM lessons')==[(None,)]
    sql('UPDATE lessons SET lesson_price_kopecks=0')
    assert 'Refusing to discard lesson price history' in alembic('downgrade','11ffc0656a8a',success=False).stderr
    assert sql('SELECT lesson_price_kopecks FROM lessons')==[(0,)]
    sql('UPDATE lessons SET lesson_price_kopecks=NULL')
    alembic('downgrade','11ffc0656a8a');alembic('upgrade','head');assert_schema(conf)
