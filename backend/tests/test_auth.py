import pytest
from httpx import AsyncClient

# Make sure pytest marks tests as async
pytestmark = pytest.mark.asyncio


async def test_register_user_success(client: AsyncClient):
    """Test successful user registration."""
    payload = {
        "email": "user@example.com",
        "password": "strongpassword123",
        "full_name": "John Doe"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "John Doe"
    assert "id" in data
    assert data["is_verified"] is False


async def test_register_duplicate_email(client: AsyncClient):
    """Test duplicate registration returns conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "Original User"
    }
    # Register once
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201
    
    # Register twice
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "detail" in res2.json()


async def test_login_success(client: AsyncClient):
    """Test successful login and token retrieval."""
    # 1. Register User
    register_payload = {
        "email": "login@example.com",
        "password": "correctpassword",
        "full_name": "Login Tester"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    # 2. Login
    login_payload = {
        "email": "login@example.com",
        "password": "correctpassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with wrong password."""
    # 1. Register User
    register_payload = {
        "email": "wrong@example.com",
        "password": "secretpassword"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    # 2. Try bad login
    login_payload = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
