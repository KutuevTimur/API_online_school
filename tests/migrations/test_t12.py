"""File metadata upgrade leaves legacy bytes/paths alone; no destructive downgrade."""
from tests.migrations.test_baseline import database, alembic, assert_schema
from tests.migrations.test_t09 import prior


def test_t12_prior_paths_and_round_trip(database):
    conf, sql = database
    prior(sql)
    alembic('upgrade', '689ceabc2b0c')
    sql("UPDATE homeworks SET original_file_path='/legacy/original.pdf',pdf_file_path='/legacy/download.pdf'")
    before = sql('SELECT id,original_file_path,pdf_file_path FROM homeworks')
    alembic('upgrade', 'head')
    assert_schema(conf)
    assert sql('SELECT id,original_file_path,pdf_file_path FROM homeworks') == before
    assert sql('SELECT original_asset_id,download_asset_id FROM homeworks') == [(None, None)]
    assert sql('SELECT count(*) FROM file_assets') == [(0,)]
    alembic('downgrade', '689ceabc2b0c')
    assert sql('SELECT id,original_file_path,pdf_file_path FROM homeworks') == before
    alembic('upgrade', 'head')
    assert_schema(conf)


def test_t12_fk_and_metadata_downgrade_guard(database):
    conf, sql = database
    prior(sql)
    alembic('upgrade', 'head')
    sql("""INSERT INTO file_assets(id,backend,key,size,mime,sha256,display_name,state,uploader_user_id)
           VALUES(1,'local','homework/object',10,'application/pdf',repeat('a',64),'safe.pdf','ready',10)""")
    sql('UPDATE homeworks SET original_asset_id=1,download_asset_id=1')
    import pytest
    with pytest.raises(Exception, match='foreign key'):
        sql('DELETE FROM file_assets WHERE id=1')
    revision_before = sql("SELECT version_num FROM alembic_version")
    result = alembic('downgrade', '689ceabc2b0c', success=False)
    assert 'Refusing to discard file asset metadata' in result.stderr
    assert sql('SELECT version_num FROM alembic_version') == revision_before
    assert_schema(conf)
    assert sql('SELECT count(*) FROM file_assets') == [(1,)]


def test_t12_source_usage_survives_normalized_original_and_refuses_loss(database):
    conf, sql = database
    prior(sql)
    alembic('upgrade', 'head')
    sql("""INSERT INTO file_assets(id,backend,key,size,mime,sha256,display_name,state,uploader_user_id)
           VALUES(1,'local','homework/photo',10,'image/webp',repeat('a',64),'safe.webp','ready',10)""")
    sql("INSERT INTO homework_submissions(id,homework_id,attempt_number,status) VALUES(110,90,1,'draft')")
    sql('INSERT INTO homework_submission_files(submission_id,original_asset_id,download_asset_id,source_size) VALUES(110,1,1,1000)')
    result = alembic('downgrade', '4ffe7beb42f4', success=False)
    assert 'Refusing to lose source byte usage' in result.stderr
    assert sql('SELECT source_size FROM homework_submission_files') == [(1000,)]
    assert_schema(conf)


def test_t12_custom_quota_downgrade_guard(database):
    conf, sql = database
    prior(sql)
    alembic('upgrade','head')
    assert sql('SELECT DISTINCT file_quota_bytes FROM users')==[(1073741824,)]
    sql('UPDATE users SET file_quota_bytes=20971520 WHERE id=20')
    result=alembic('downgrade','5c844cca1bd6',success=False)
    assert 'Refusing to discard custom storage quotas' in result.stderr
    assert_schema(conf)
