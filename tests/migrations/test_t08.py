"""T08 migration: prior rows, invalid legacy data, enum lifecycle and no silent loss."""
import pytest
from tests.migrations.test_baseline import database, alembic, assert_schema
from tests.migrations.test_t07 import seed


def test_t08_prior_state_backfill_and_round_trip(database):
    conf, sql = database
    alembic('upgrade', '711e94443ef3')
    seed(sql)
    alembic('upgrade', '811d7911d0b4')
    sql("INSERT INTO lessons(id,course_id,teacher_id,title,duration_minutes,is_deleted) VALUES(71,50,30,'Explicit',90,false)")
    alembic('upgrade', 'head')
    assert sql('SELECT id,duration_minutes,status::text,call_url_override FROM lessons ORDER BY id') == [
        (70,55,'scheduled',None), (71,90,'scheduled',None)]
    assert sql('SELECT call_url FROM courses') == [(None,)]
    assert sql('SELECT count(*) FROM lesson_students') == [(1,)]
    assert_schema(conf)
    alembic('downgrade', '811d7911d0b4')
    assert sql("SELECT count(*) FROM pg_type WHERE typname='lesson_status'") == [(0,)]
    assert sql('SELECT duration_minutes FROM lessons ORDER BY id') == [(55,), (90,)]
    alembic('upgrade', 'head')
    assert_schema(conf)


@pytest.mark.parametrize('value', [0, -5])
def test_t08_invalid_legacy_duration_refused_before_ddl(database, value):
    _, sql = database
    alembic('upgrade', '711e94443ef3')
    seed(sql)
    alembic('upgrade', '811d7911d0b4')
    sql(f'UPDATE lessons SET duration_minutes={value}')
    result = alembic('upgrade', 'head', success=False)
    assert 'Invalid legacy lesson duration' in result.stderr
    assert sql("SELECT count(*) FROM information_schema.columns WHERE table_name='courses' AND column_name='call_url'") == [(0,)]
    assert sql('SELECT duration_minutes FROM lessons') == [(value,)]
    assert sql('SELECT version_num FROM alembic_version') == [('811d7911d0b4',)]


@pytest.mark.parametrize('mutation', ["UPDATE lessons SET status='completed'", "UPDATE lessons SET status='cancelled'",
    "UPDATE lessons SET call_url_override='https://example.com/lesson'", "UPDATE courses SET call_url='https://example.com/course'"])
def test_t08_downgrade_refuses_loss_before_ddl(database, mutation):
    conf, sql = database
    alembic('upgrade', '711e94443ef3')
    seed(sql)
    alembic('upgrade', '811d7911d0b4')
    alembic('upgrade', 'head')
    sql(mutation)
    revision_before = sql("SELECT version_num FROM alembic_version")
    result = alembic('downgrade', '811d7911d0b4', success=False)
    assert 'Cannot discard T08' in result.stderr
    assert sql('SELECT version_num FROM alembic_version') == revision_before
    assert sql('SELECT count(*) FROM lesson_students') == [(1,)]
    assert_schema(conf)
