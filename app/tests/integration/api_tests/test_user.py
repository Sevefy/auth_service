from copy import copy

import pytest

from app.tests.integration.api_tests.conftest import BASE_URL_PUBLIC, USER_DATA, auth, register, register_and_auth


@pytest.mark.test_api
@pytest.mark.asyncio
async def test_register_ok(client):
    response = await register(client, USER_DATA)
    assert response.status_code == 201


@pytest.mark.test_api
@pytest.mark.asyncio
async def test_register_duplicate(client):
    # сначала регистрируем
    response = await register(client, USER_DATA)
    assert response.status_code == 201

    # дубликат
    response = await register(client, USER_DATA)
    assert response.status_code == 400


@pytest.mark.test_api
@pytest.mark.asyncio
async def test_auth_ok(client):
    # регистрация
    response = await register_and_auth(client, USER_DATA)

    assert response.status_code == 200
    assert response.cookies.get("sessionToken") is not None


@pytest.mark.test_api
@pytest.mark.asyncio
async def test_auth_not_found(client):

    response = await auth(client, USER_DATA)
    assert response.status_code == 400
    assert "UserNotFoundError" in response.text


@pytest.mark.test_api
@pytest.mark.asyncio
async def test_auth_wrong_password(client):

    # сначала регистрируем
    await register(client, USER_DATA)

    new_data = copy(USER_DATA)
    new_data["password"] = "12345"
    response = await client.post(url=BASE_URL_PUBLIC + "/auth", json=new_data)

    assert response.status_code == 400
    assert "PasswordNotValidError" in response.text


@pytest.mark.test_api
@pytest.mark.asyncio
async def test_logout(client):
    await register_and_auth(client, USER_DATA)
    # выходим
    response = await client.post(url=BASE_URL_PUBLIC + "/logout")
    assert response.status_code == 200
    assert response.cookies.get("sessionToken") is None


@pytest.mark.test_api
@pytest.mark.asyncio
async def test_logout_fail(client):
    # сначала регистрируем
    await register_and_auth(client, USER_DATA)

    client.cookies.delete("sessionToken")
    response = await client.post(url=BASE_URL_PUBLIC + "/logout")
    assert response.status_code == 404
