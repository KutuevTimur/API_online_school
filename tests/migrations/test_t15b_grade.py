"""School grade migration preserves existing students and refuses lossy rollback."""
from tests.migrations.test_baseline import database, alembic, assert_schema


def test_school_grade_upgrade_constraint_and_lossless_downgrade(database):
    conf, sql = database
    alembic('upgrade','2048d2eeeaa8')
    sql("INSERT INTO users(id,username,role,hashed_password,is_active,is_activated,auth_version) VALUES(1,'synthetic_grade','student','synthetic',true,true,0)")
    sql("INSERT INTO students(id,user_id,first_name,last_name) VALUES(1,1,'Synthetic','Grade')")
    alembic('upgrade','head')
    assert_schema(conf)
    assert sql('SELECT first_name,last_name,school_grade FROM students')==[('Synthetic','Grade',None)]
    sql('UPDATE students SET school_grade=10')
    result=alembic('downgrade','2048d2eeeaa8',success=False)
    assert 'Refusing to discard school grades' in result.stderr
    assert sql('SELECT school_grade FROM students')==[(10,)]
    assert_schema(conf)
    sql('UPDATE students SET school_grade=NULL')
    alembic('downgrade','2048d2eeeaa8')
    alembic('upgrade','head')
    assert_schema(conf)
    assert sql('SELECT first_name,last_name,school_grade FROM students')==[('Synthetic','Grade',None)]
