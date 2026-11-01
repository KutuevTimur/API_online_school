"""Destructive checks restricted by T01 to the allocated lgg-test target."""
import asyncio
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text, inspect
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from src.core.config import create_config
from src.core.config.test_guard import require_test_config
from src.core.database.database import Base
import src.modules.db_models  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]


def alembic(*args: str, success: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [str(ROOT / ".venv/bin/alembic"), *args], cwd=ROOT,
        env={**os.environ, "MODE": "TEST"}, capture_output=True, text=True,
    )
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    return result


@pytest.fixture
def database(tmp_path):
    conf = create_config(test=True, media_root=tmp_path)
    require_test_config(conf)

    def sql(statement: str):
        async def execute():
            try:
                async with conf.db_connection.engine.begin() as conn:
                    result = await conn.execute(text(statement))
                    return result.fetchall() if result.returns_rows else None
            finally:
                await conf.db_connection.engine.dispose()
        return asyncio.run(execute())

    # The only schema this fixture may reset belongs to the guarded test role.
    sql("DROP SCHEMA public CASCADE")
    sql("CREATE SCHEMA public")
    yield conf, sql
    sql("DROP SCHEMA public CASCADE")
    sql("CREATE SCHEMA public")


def assert_schema(conf):
    async def check():
        try:
            async with conf.db_connection.engine.connect() as conn:
                def compare(connection):
                    inspector = inspect(connection)
                    assert set(inspector.get_table_names()) == set(Base.metadata.tables) | {"alembic_version"}
                    assert compare_metadata(
                        MigrationContext.configure(connection, opts={"compare_server_default": True}),
                        Base.metadata,
                    ) == []
                    # Autogenerate does not compare native enum labels.
                    enums = {e["name"]: e["labels"] for e in inspector.get_enums()}
                    for table in Base.metadata.tables.values():
                        for column in table.columns:
                            if hasattr(column.type, "enums"):
                                assert enums[column.type.name] == column.type.enums
                await conn.run_sync(compare)
        finally:
            await conf.db_connection.engine.dispose()
    asyncio.run(check())


def test_clean_upgrade_and_round_trip(database):
    conf, sql = database
    alembic("upgrade", "head")
    assert_schema(conf)
    alembic("upgrade", "head")
    alembic("downgrade", "d98c55d6402c")
    alembic("upgrade", "head")
    assert_schema(conf)


def test_prior_state_preserves_rows(database):
    conf, sql = database
    alembic("upgrade", "d98c55d6402c")
    sql("""INSERT INTO users (id,email,username,role,hashed_password,is_active)
           VALUES (10,'teacher@synthetic.invalid','teacher','teacher','dummy',true),
                  (20,'student@synthetic.invalid','student','student','dummy',true)""")
    sql("INSERT INTO teachers (id,user_id,first_name,last_name) VALUES (30,10,'T','Test')")
    sql("INSERT INTO students (id,user_id,first_name,last_name) VALUES (40,20,'S','Test')")
    sql("""INSERT INTO courses (id,teacher_id,name,slug,avatar_type,is_active)
           VALUES (50,30,'active','active','default',true),
                  (51,30,'inactive','inactive','default',false)""")
    sql("""INSERT INTO student_courses (id,student_id,course_id,is_active)
           VALUES (60,40,50,true),(61,40,51,false)""")
    sql("INSERT INTO lessons (id,course_id,teacher_id,title) VALUES (70,50,30,'Synthetic')")
    sql("INSERT INTO lesson_students (id,lesson_id,student_id) VALUES (80,70,40)")
    sql("""INSERT INTO homeworks (id,lesson_student_id,title,deadline)
           VALUES (90,80,'Synthetic',now())""")
    sql("""INSERT INTO lectures (id,lesson_student_id,original_file_path,original_file_name,
           original_file_type,pdf_file_path,pdf_file_name)
           VALUES (100,80,'dummy','dummy','pdf','dummy','dummy')""")
    sql("""INSERT INTO homework_submissions (id,homework_id,attempt_number,status,checked_by)
           VALUES (110,90,1,'checked',30)""")
    sql("INSERT INTO homework_submission_files (id,submission_id) VALUES (120,110)")
    sql("""INSERT INTO refresh_tokens (refresh_token_id,user_id,token,expires_at)
           VALUES (130,20,'synthetic-not-a-token',now())""")
    tables = [r[0] for r in sql("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'")]
    before = {t: sql(f"SELECT * FROM {t} ORDER BY 1") for t in tables}
    alembic("upgrade", "head")
    for table in tables:
        after = sql(f"SELECT * FROM {table} ORDER BY 1")
        if table == "users":
            for old, new in zip(before[table], after):
                old_map, new_map = dict(old._mapping), dict(new._mapping)
                assert {k: new_map[k] for k in old_map} == old_map
                assert new_map["auth_version"] == 0
                assert new_map["is_activated"] is True
        elif table == "refresh_tokens":
            import hashlib
            row = dict(after[0]._mapping)
            assert "token" not in row
            assert row["digest"] == hashlib.sha256(b"synthetic-not-a-token").hexdigest()
            assert row["is_revoked"] is True
            assert row["user_id"] == 20
        elif table not in ("courses", "student_courses"):
            for old, new in zip(before[table], after):
                expected = dict(old._mapping)
                if table == "lessons" and expected["duration_minutes"] is None:
                    expected["duration_minutes"] = 55  # Explicit T08 backfill.
                assert {k: new._mapping[k] for k in old._mapping} == expected
            assert len(after) == len(before[table])
            if table == "lessons":
                assert all(not r._mapping['is_deleted'] and r._mapping['deleted_at'] is None for r in after)
        else:
            columns = [c for c in Base.metadata.tables[table].columns.keys()
                       if c not in ("is_deleted", "deleted_at", "access_ended_at", "history_revoked", "call_url")]
            old = sql(f"SELECT {','.join(columns)},is_deleted,deleted_at FROM {table} ORDER BY id")
            assert len(old) == 2
            assert [r[-2:] for r in old] == [(False, None), (True, None)]
            # Compare all legacy non-status columns, including IDs, FKs and timestamps.
            legacy_columns = list(before[table][0]._mapping.keys())
            positions = [legacy_columns.index(c) for c in columns]
            assert [tuple(r[:-2]) for r in old] == [
                tuple(row[i] for i in positions) for row in before[table]]
    assert sql("SELECT teacher_id,student_id FROM teacher_students") == [(30,40)]
    assert_schema(conf)
    alembic("downgrade", "d98c55d6402c")
    for table in tables:
        if table == "refresh_tokens":
            rows = sql("SELECT token,is_revoked FROM refresh_tokens")
            assert rows == [("invalidated-130", True)]
            continue
        expected = [dict(r._mapping) for r in before[table]]
        if table == "lessons":
            for row in expected:
                if row["duration_minutes"] is None:
                    row["duration_minutes"] = 55
        assert [dict(r._mapping) for r in sql(f"SELECT * FROM {table} ORDER BY 1")] == expected
    alembic("upgrade", "head")


def test_main_revision_refused_without_changes(database):
    _, sql = database
    sql("CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY)")
    sql("INSERT INTO alembic_version VALUES ('1c3d40e331ff')")
    result = alembic("upgrade", "head", success=False)
    assert "Unsupported main baseline" in result.stderr
    assert sql("SELECT version_num FROM alembic_version") == [("1c3d40e331ff",)]
    assert sql("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'") == [(1,)]


def test_t05_enum_admin_downgrade_refusal(database):
    conf, sql = database
    alembic('upgrade', 'head')
    sql("""INSERT INTO users(email,username,role,hashed_password,is_active)
        VALUES ('admin@synthetic.invalid','admin','admin','dummy',true)""")
    revision_before = sql("SELECT version_num FROM alembic_version")
    result = alembic('downgrade', 'c3882e989a1e', success=False)
    assert 'Cannot downgrade T05 while admin accounts exist' in result.stderr
    assert sql("SELECT role::text FROM users") == [('admin',)]
    assert sql("SELECT version_num FROM alembic_version") == revision_before
    assert_schema(conf)


def test_t05_backfill_does_not_guess_links(database):
    _, sql = database
    alembic('upgrade', 'c3882e989a1e')
    sql("""INSERT INTO users(id,email,username,role,hashed_password,is_active) VALUES
        (1,'t@synthetic.invalid','t','teacher','dummy',true),
        (2,'s@synthetic.invalid','s','student','dummy',true),
        (3,'u@synthetic.invalid','u','student','dummy',true)""")
    sql("INSERT INTO teachers(id,user_id,first_name,last_name) VALUES (1,1,'T','Test')")
    sql("INSERT INTO students(id,user_id,first_name,last_name) VALUES (1,2,'S','Test'),(2,3,'U','Test')")
    sql("""INSERT INTO courses(id,teacher_id,name,slug,avatar_type,is_deleted)
        VALUES (1,1,'archived','archived','default',true)""")
    sql("INSERT INTO student_courses(student_id,course_id,is_deleted) VALUES (1,1,false)")
    result = alembic('upgrade', 'head')
    assert '1 archived/expired-only pairs require review' in result.stderr
    assert sql('SELECT count(*) FROM teacher_students') == [(0,)]
    assert sql('SELECT count(*) FROM users') == [(3,)]


def test_t05b_preserves_emails_and_checks_collisions(database):
    conf, sql = database
    alembic('upgrade', 'd897e9b55d47')
    sql("""INSERT INTO users(id,email,username,role,hashed_password,is_active) VALUES
        (1,'legacy@synthetic.invalid','original','student','old-hash',true),
        (2,'second@synthetic.invalid','legacy@synthetic.invalid','student','other-hash',false)""")
    before = sql('SELECT id,email,username,hashed_password,is_active,auth_version FROM users ORDER BY id')
    result = alembic('upgrade','head')
    assert '1 legacy username/email cross-collisions' in result.stderr
    assert sql('SELECT id,email,username,hashed_password,is_active,auth_version FROM users ORDER BY id') == before
    assert sql('SELECT is_activated FROM users') == [(True,),(True,)]
    assert_schema(conf)
    alembic('downgrade','d897e9b55d47')
    alembic('upgrade','head')
    assert_schema(conf)


@pytest.mark.parametrize('pending', [False, True])
def test_t05b_downgrade_refuses_data_loss(database, pending):
    conf, sql = database
    alembic('upgrade','head')
    if pending:
        sql("""INSERT INTO users(email,username,role,hashed_password,is_active,is_activated)
            VALUES ('pending@synthetic.invalid','pending','student','dummy',true,false)""")
    else:
        sql("""INSERT INTO users(email,username,role,hashed_password,is_active,is_activated)
            VALUES (NULL,'nullable','student','dummy',true,true)""")
    revision_before = sql("SELECT version_num FROM alembic_version")
    result = alembic('downgrade','d897e9b55d47',success=False)
    assert 'Cannot downgrade T05b' in result.stderr
    assert sql('SELECT version_num FROM alembic_version') == revision_before
    assert sql('SELECT count(*) FROM users') == [(1,)]
    assert_schema(conf)
