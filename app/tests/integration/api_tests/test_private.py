from uuid import uuid4

import pytest

from app.schemas.user import UserSession
from app.tests.integration.api_tests.conftest import BASE_URL_PRIVATE, USER_DATA, register_and_auth


@pytest.mark.test_private_api
@pytest.mark.asyncio
async def test_private_endpoint_valid_session(client):

    response = await register_and_auth(client, USER_DATA)
    assert response.status_code == 200

    response = await client.get(url=BASE_URL_PRIVATE + "/")
    assert response.status_code == 200

    user_schema = UserSession.model_validate_json(response.text)
    assert str(user_schema.token) == client.cookies.get("sessionToken")
    assert user_schema.username == USER_DATA.get("username")


@pytest.mark.test_private_api
@pytest.mark.asyncio
async def test_private_endpoint_no_cookie(client):

    response = await register_and_auth(client, USER_DATA)
    assert response.status_code == 200

    client.cookies.delete("sessionToken")
    response = await client.get(url=BASE_URL_PRIVATE + "/")

    assert response.status_code == 401


@pytest.mark.parametrize(
    "token", [
        "12345",
        str(uuid4())
    ]
)
@pytest.mark.test_private_api
@pytest.mark.asyncio
async def test_private_endpoint_invalid_cookie(client, token):
    # входим
    response = await register_and_auth(client, USER_DATA)
    assert response.status_code == 200

    client.cookies.set("sessionToken", str(token))
    response = await client.get(url=BASE_URL_PRIVATE + "/")

    assert response.status_code == 401
