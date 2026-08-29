import pytest

from helpers.functions import comparison_models


@pytest.mark.asyncio
async def test_get_me(client_for_tests, create_user_fixture):
    user, accesses_token = await create_user_fixture()

    response = await client_for_tests.get(
        "/users/me",
        headers={"Authorization": f"Bearer {accesses_token}"}
    )

    assert response.status_code == 200
    assert comparison_models(user, response.json())

