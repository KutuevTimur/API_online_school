"""Admin storage uses course ownership, never the identity of the uploader."""
import pytest
from sqlalchemy import update
from src.modules.courses.models import Course
from src.modules.lessons.models import Lesson
from src.modules.lectures.models import Lecture
from src.modules.homeworks.models import Homework
from src.modules.homework_submissions.models import HomeworkSubmissionFile
from src.modules.files.models import FileAsset
from src.modules.users.models import User
from tests.modules.auth.test_t06_permissions import world, auth


@pytest.mark.asyncio
async def test_teacher_storage_course_scope_archive_and_distinct_assets(client_for_tests, world, session_db):
    assets = []
    for index, size in enumerate([100, 200, 900]):
        asset = FileAsset(backend='local', key=f'objects/teacher-storage-{index}', size=size,
                          mime='application/pdf', sha256=str(index) * 64,
                          display_name='synthetic.pdf', state='ready',
                          uploader_user_id=world['accounts']['s1'][0].id)
        session_db.add(asset)
        await session_db.flush()
        assets.append(asset.id)
    # Same asset as original/download, and across two material kinds: count once.
    for model, key in [(Lecture, 'lectures'), (Homework, 'homeworks')]:
        await session_db.execute(update(model).where(model.id == world[key][0].id).values(
            original_asset_id=assets[0], download_asset_id=assets[0]))
    await session_db.execute(update(HomeworkSubmissionFile).where(
        HomeworkSubmissionFile.id == world['files'][0].id).values(
        original_asset_id=assets[1], download_asset_id=assets[1]))
    await session_db.execute(update(Lecture).where(Lecture.id == world['lectures'][1].id).values(
        original_asset_id=assets[2], download_asset_id=assets[2]))
    await session_db.execute(update(Course).where(Course.id == world['courses'][0].id).values(is_deleted=True))
    # A blocked teacher's files remain visible to the administrator.
    await session_db.execute(update(User).where(User.id == world['accounts']['t1'][0].id).values(is_active=False))
    await session_db.commit()
    admin = auth(world['accounts']['admin'][1])
    for key, index, size in [('t1', 0, 300), ('t2', 1, 900)]:
        user_id = world['accounts'][key][0].id
        response = await client_for_tests.get(f'/admin/users/{user_id}/course-storage', headers=admin)
        assert response.status_code == 200, response.text
        assert response.json() == {'user_id': user_id, 'used_bytes': size,
            'courses': [{'course_id': world['courses'][index].id,
                         'course_name': world['courses'][index].name, 'bytes': size}]}
        assert 'limit_bytes' not in response.json()
    # The pupil still has one global budget across both teachers, including archive.
    student_id = world['accounts']['s1'][0].id
    response = await client_for_tests.get(f'/users/{student_id}/storage', headers=admin)
    assert response.json()['used_bytes'] == 1200

    # Several courses for one teacher: total is independent of the grouped row.
    await session_db.execute(update(Course).where(Course.id == world['courses'][1].id).values(
        teacher_id=world['teachers'][0].id))
    await session_db.execute(update(Lesson).where(Lesson.id == world['lessons'][1].id).values(
        teacher_id=world['teachers'][0].id))
    await session_db.commit()
    path = f"/admin/users/{world['accounts']['t1'][0].id}/course-storage"
    response = await client_for_tests.get(path, headers=admin)
    assert response.json()['used_bytes'] == 1200
    assert [course['bytes'] for course in response.json()['courses']] == [300, 900]
    # A shared registered object counts once in the total, even across courses.
    await session_db.execute(update(Lecture).where(Lecture.id == world['lectures'][1].id).values(
        original_asset_id=assets[0], download_asset_id=assets[0]))
    await session_db.commit()
    response = await client_for_tests.get(path, headers=admin)
    assert response.json()['used_bytes'] == 300
    assert [course['bytes'] for course in response.json()['courses']] == [300, 100]


@pytest.mark.asyncio
async def test_teacher_storage_empty_wrong_target_and_role_denials(client_for_tests, world):
    teacher_id = world['accounts']['t1'][0].id
    path = f'/admin/users/{teacher_id}/course-storage'
    admin = auth(world['accounts']['admin'][1])
    response = await client_for_tests.get(path, headers=admin)
    assert response.status_code == 200
    assert response.json() == {'user_id': teacher_id, 'used_bytes': 0, 'courses': []}
    for key in ['t1', 't2', 's1', 's2']:
        assert (await client_for_tests.get(path, headers=auth(world['accounts'][key][1]))).status_code == 403
    for key in ['s1', 'admin']:
        target = world['accounts'][key][0].id
        assert (await client_for_tests.get(f'/admin/users/{target}/course-storage', headers=admin)).status_code == 404
    assert (await client_for_tests.get('/admin/users/99999999/course-storage', headers=admin)).status_code == 404
