"""T13 migration preserves existing audit/history and refuses destructive downgrade."""
import pytest
from tests.migrations.test_baseline import database, alembic, assert_schema
from tests.migrations.test_t09 import prior


def test_t13_prior_and_empty_round_trip(database):
    conf, sql = database
    prior(sql)
    alembic('upgrade', '36a8711f7799')
    sql("INSERT INTO lifecycle_audit(actor_user_id,object_type,object_id,action,result,correlation_id) VALUES(10,'course',50,'purge','success',repeat('a',32))")
    before = sql('SELECT * FROM lifecycle_audit')
    users = sql('SELECT * FROM users ORDER BY id')
    alembic('upgrade', 'head')
    assert_schema(conf)
    assert sql('SELECT * FROM lifecycle_audit') == before
    assert sql('SELECT * FROM users ORDER BY id') == users
    assert sql('SELECT count(*) FROM notifications') == [(0,)]
    alembic('downgrade', '36a8711f7799')
    alembic('upgrade', 'head')
    assert_schema(conf)


@pytest.mark.parametrize('kind', ['notification', 'audit'])
def test_t13_refuses_discarding_records(database, kind):
    conf, sql = database
    prior(sql)
    alembic('upgrade', 'head')
    if kind == 'notification':
        sql("INSERT INTO notifications(recipient_user_id,event_type,object_type,object_id,dedupe_key) VALUES(20,'homework_assigned','homework',90,'test')")
    else:
        sql("INSERT INTO audit_events(actor_user_id,action,object_type,object_id,result,correlation_id) VALUES(10,'account_create','user',20,'success',repeat('a',32))")
    revision_before = sql("SELECT version_num FROM alembic_version")
    result = alembic('downgrade', '36a8711f7799', success=False)
    assert 'Refusing to discard notifications or audit events' in result.stderr
    assert sql('SELECT version_num FROM alembic_version') == revision_before
    assert_schema(conf)
