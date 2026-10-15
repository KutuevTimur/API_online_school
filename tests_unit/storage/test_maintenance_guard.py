from types import SimpleNamespace
from sqlalchemy.engine import URL
import pytest
from src.modules.files.maintenance import require_local_maintenance


def configuration():
    engine=SimpleNamespace(url=URL.create('postgresql+asyncpg',host='127.0.0.1',port=55431,database='lgg_dev',username='lgg_dev_app'))
    return SimpleNamespace(env=SimpleNamespace(mode='DEV',db_host='127.0.0.1',db_port='55431',db_name='lgg_dev',db_user='lgg_dev_app'),
        db_connection=SimpleNamespace(engine=engine,session_local=SimpleNamespace(kw={'bind':engine})))


def test_local_guard_matches_actual_engine_and_session():
    conf=configuration();require_local_maintenance(conf)
    conf.db_connection.engine.url=conf.db_connection.engine.url.set(database='other')
    with pytest.raises(RuntimeError,match='mismatch'):require_local_maintenance(conf)
    conf=configuration();conf.db_connection.session_local.kw['bind']=object()
    with pytest.raises(RuntimeError,match='mismatch'):require_local_maintenance(conf)
    conf=configuration();conf.env.mode='PROD'
    with pytest.raises(RuntimeError,match='isolated'):require_local_maintenance(conf)
