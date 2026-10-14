from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import pytest
from src.core.config.test_guard import guarded_operation, remove_test_media

URL = "postgresql+asyncpg://lgg_test_app:dummy@127.0.0.1:55432/lgg_test"


def env(**updates):
    values = dict(mode="TEST", db_name="lgg_test", db_user="lgg_test_app",
                  db_host="127.0.0.1", db_port="55432", allow_test_db_reset="1")
    values.update(updates)
    return SimpleNamespace(**values)


@pytest.mark.parametrize("updates", [dict(mode="LOCAL"), dict(db_name="lgg_dev"),
    dict(db_user="postgres"), dict(db_host="remote.example"), dict(db_port="5432"),
    dict(allow_test_db_reset="0")])
def test_rejected_before_connection_and_removal(updates, tmp_path):
    factory, remover = Mock(), Mock()
    with pytest.raises(RuntimeError):
        guarded_operation(env(**updates), URL, factory)
    with pytest.raises(RuntimeError):
        remove_test_media(env(**updates), URL, tmp_path, tmp_path, remover)
    factory.assert_not_called()
    remover.assert_not_called()


@pytest.mark.parametrize("url", [URL.replace("127.0.0.1", "remote.example"),
    URL.replace("lgg_test", "other_test"), URL + "?host=remote.example"])
def test_actual_url_is_checked(url):
    factory = Mock()
    with pytest.raises(RuntimeError):
        guarded_operation(env(), url, factory)
    factory.assert_not_called()


def test_allowed_target(tmp_path):
    factory, remover = Mock(return_value="ok"), Mock()
    assert guarded_operation(env(), URL, factory) == "ok"
    remove_test_media(env(), URL, tmp_path, tmp_path, remover)
    factory.assert_called_once()
    remover.assert_called_once_with(tmp_path)


def test_media_outside_allocation(tmp_path):
    remover = Mock()
    with pytest.raises(RuntimeError):
        remove_test_media(env(), URL, tmp_path.parent, tmp_path, remover)
    remover.assert_not_called()


def test_test_config_never_falls_back_to_dev(monkeypatch, tmp_path):
    from src.core.config import base, Config
    monkeypatch.setattr(base, "ROOT", tmp_path)
    (tmp_path / ".env").write_text("MODE=LOCAL\nDB_NAME=real_database\n")
    monkeypatch.setenv("DB_NAME", "real_database")
    with pytest.raises(KeyError):
        Config(test=True, media_root=tmp_path / "media")


@pytest.mark.asyncio
async def test_application_lifecycle_disposes_single_engine(tmp_path):
    from src.core.config import create_config
    from src.modules.api.app import init_fastapi_app
    conf = create_config(test=True, media_root=tmp_path / "media")
    real_engine = conf.db_connection.engine
    fake = Mock()
    fake.dispose = AsyncMock()
    conf.db_connection.engine = fake
    try:
        app = init_fastapi_app(config=conf)
        async with app.router.lifespan_context(app):
            assert app.state.config is conf
        fake.dispose.assert_awaited_once()
    finally:
        await real_engine.dispose()


def test_engine_and_session_bind_are_checked(tmp_path):
    from src.core.config import create_config
    from src.core.config.test_guard import require_test_config
    conf = create_config(test=True, media_root=tmp_path / "media")
    require_test_config(conf)
    original = conf.db_connection.session_local.kw["bind"]
    conf.db_connection.session_local.kw["bind"] = Mock()
    with pytest.raises(RuntimeError):
        require_test_config(conf)
    conf.db_connection.session_local.kw["bind"] = original
