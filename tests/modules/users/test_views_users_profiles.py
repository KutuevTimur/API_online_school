import pytest
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


@pytest.mark.asyncio
async def test_get_students(client_for_tests, create_user_fixture):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student1, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT, username="st1", email="st1@mail.com"))
    student2, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT, username="st2", email="st2@mail.com"))
    
    response = await client_for_tests.get(
        "/users/students",
        headers={"Authorization": f"Bearer {t_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    items = data["items"]
    roles = [i["role"] for i in items]
    assert all(r == UserRole.STUDENT.value for r in roles)


@pytest.mark.asyncio
async def test_get_students_forbidden_for_student(client_for_tests, create_user_fixture):
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    response = await client_for_tests.get(
        "/users/students",
        headers={"Authorization": f"Bearer {s_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_teachers(client_for_tests, create_user_fixture):
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    teacher1, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER, username="t1", email="t1@mail.com"))
    teacher2, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER, username="t2", email="t2@mail.com"))
    
    response = await client_for_tests.get(
        "/users/teachers",
        headers={"Authorization": f"Bearer {s_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    items = data["items"]
    roles = [i["role"] for i in items]
    assert all(r == UserRole.TEACHER.value for r in roles)


@pytest.mark.asyncio
async def test_get_public_profile(client_for_tests, create_user_fixture):
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    teacher, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER, username="t3", email="t3@mail.com"))
    
    response = await client_for_tests.get(
        f"/users/{teacher.id}",
        headers={"Authorization": f"Bearer {s_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == teacher.id
    assert data["role"] == UserRole.TEACHER.value
    assert "teacher" in data


@pytest.mark.asyncio
async def test_get_public_profile_not_found(client_for_tests, create_user_fixture):
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    response = await client_for_tests.get(
        "/users/99999",
        headers={"Authorization": f"Bearer {s_token}"}
    )
    assert response.status_code == 404
