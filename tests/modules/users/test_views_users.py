import io
import pytest
from PIL import Image
from sqlalchemy import select

from helpers.functions import comparison_models
from src.modules.path_builder import PathBuilder
from src.modules.students.models import Students
from src.modules.teachers.models import Teachers
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


def _generate_test_image_bytes(format_: str = "PNG", size: tuple[int, int] = (800, 600)) -> bytes:
    img = Image.new("RGB", size, color="teal")
    buf = io.BytesIO()
    img.save(buf, format=format_)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_get_me(client_for_tests, create_user_fixture):
    user, accesses_token = await create_user_fixture()

    response = await client_for_tests.get(
        "/users/me",
        headers={"Authorization": f"Bearer {accesses_token}"}
    )

    assert response.status_code == 200
    assert comparison_models(user, response.json())


@pytest.mark.asyncio
async def test_update_avatar_by_self_student(
    client_for_tests,
    create_user_fixture,
    session_db,
    config_fix,
):
    student, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.STUDENT)
    )

    image_bytes = _generate_test_image_bytes("PNG", (1000, 800))
    response = await client_for_tests.patch(
        f"/users/{student.id}/avatar",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"avatar": ("photo.png", io.BytesIO(image_bytes), "image/png")},
    )

    assert response.status_code == 200
    assert response.content == image_bytes
    assert response.headers.get("content-type") == "image/png"
    assert response.headers.get("content-disposition") == 'inline; filename="photo.png"'

    # Проверяем сохраненный файл на диске
    avatar_file = PathBuilder(config=config_fix).get_avatar_user(student.id)
    assert avatar_file.is_file()
    with Image.open(avatar_file) as img:
        assert img.format == "WEBP"
        assert img.size[0] <= 512 and img.size[1] <= 512

    # Проверяем запись в БД
    result_db = await session_db.execute(select(Students).where(Students.user_id == student.id))
    student_db = result_db.scalar_one_or_none()
    assert student_db is not None
    assert student_db.avatar_path == str(avatar_file)


@pytest.mark.asyncio
async def test_update_avatar_by_teacher_for_student(
    client_for_tests,
    create_user_fixture,
    session_db,
    config_fix,
):
    teacher, teacher_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.TEACHER)
    )
    student, _ = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.STUDENT)
    )

    image_bytes = _generate_test_image_bytes("JPEG", (600, 600))
    response = await client_for_tests.patch(
        f"/users/{student.id}/avatar",
        headers={"Authorization": f"Bearer {teacher_token}"},
        files={"avatar": ("avatar.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.content == image_bytes
    assert response.headers.get("content-type") == "image/jpeg"
    assert response.headers.get("content-disposition") == 'inline; filename="avatar.jpg"'

    # Проверяем сохраненный файл и БД
    avatar_file = PathBuilder(config=config_fix).get_avatar_user(student.id)
    assert avatar_file.is_file()

    result_db = await session_db.execute(select(Students).where(Students.user_id == student.id))
    student_db = result_db.scalar_one_or_none()
    assert student_db is not None
    assert student_db.avatar_path == str(avatar_file)


@pytest.mark.asyncio
async def test_update_avatar_replaces_existing_avatar(
    client_for_tests,
    create_user_fixture,
    session_db,
    config_fix,
):
    teacher, token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.TEACHER)
    )

    # Первая загрузка
    first_bytes = _generate_test_image_bytes("PNG", (300, 300))
    response_1 = await client_for_tests.patch(
        f"/users/{teacher.id}/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": ("first.png", io.BytesIO(first_bytes), "image/png")},
    )
    assert response_1.status_code == 200

    avatar_file = PathBuilder(config=config_fix).get_avatar_user(teacher.id)
    assert avatar_file.is_file()

    # Вторая загрузка (замена)
    second_bytes = _generate_test_image_bytes("JPEG", (400, 400))
    response_2 = await client_for_tests.patch(
        f"/users/{teacher.id}/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": ("second.jpg", io.BytesIO(second_bytes), "image/jpeg")},
    )
    assert response_2.status_code == 200
    assert response_2.content == second_bytes
    assert avatar_file.is_file()

    result_db = await session_db.execute(select(Teachers).where(Teachers.user_id == teacher.id))
    teacher_db = result_db.scalar_one_or_none()
    assert teacher_db is not None
    assert teacher_db.avatar_path == str(avatar_file)


@pytest.mark.asyncio
async def test_update_avatar_forbidden_for_other_student(
    client_for_tests,
    create_user_fixture,
):
    student_1, token_1 = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.STUDENT)
    )
    student_2, _ = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.STUDENT)
    )

    image_bytes = _generate_test_image_bytes("PNG")
    response = await client_for_tests.patch(
        f"/users/{student_2.id}/avatar",
        headers={"Authorization": f"Bearer {token_1}"},
        files={"avatar": ("photo.png", io.BytesIO(image_bytes), "image/png")},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not permission"}


@pytest.mark.asyncio
async def test_update_avatar_invalid_format(
    client_for_tests,
    create_user_fixture,
):
    user, token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.STUDENT)
    )

    response = await client_for_tests.patch(
        f"/users/{user.id}/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": ("document.txt", io.BytesIO(b"hello world"), "text/plain")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_avatar_unauthorized(client_for_tests):
    image_bytes = _generate_test_image_bytes("PNG")
    response = await client_for_tests.patch(
        "/users/1/avatar",
        files={"avatar": ("photo.png", io.BytesIO(image_bytes), "image/png")},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_avatar_user_not_found(
    client_for_tests,
    create_user_fixture,
):
    teacher, teacher_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(role=UserRole.TEACHER)
    )

    image_bytes = _generate_test_image_bytes("PNG")
    response = await client_for_tests.patch(
        "/users/99999/avatar",
        headers={"Authorization": f"Bearer {teacher_token}"},
        files={"avatar": ("photo.png", io.BytesIO(image_bytes), "image/png")},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found data"}
