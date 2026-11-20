def test_register_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "username": "newuser",
        "full_name": "New User",
        "password": "Password123"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data


def test_register_duplicate_username(client):
    # First registration
    client.post("/api/v1/auth/register", json={
        "email": "firstuser@example.com",
        "username": "duplicate_check_user",
        "full_name": "First User",
        "password": "Password123"
    })
    # Duplicate username registration attempt
    res = client.post("/api/v1/auth/register", json={
        "email": "seconduser@example.com",
        "username": "duplicate_check_user",
        "full_name": "Duplicate User",
        "password": "Password123"
    })
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"]


def test_login_success(client):
    # Register user first so test is independent
    client.post("/api/v1/auth/register", json={
        "email": "logintest@example.com",
        "username": "login_test_user",
        "full_name": "Login Test User",
        "password": "Password123"
    })
    res = client.post("/api/v1/auth/login", json={
        "username": "login_test_user",
        "password": "Password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    # Register user first so test is independent
    client.post("/api/v1/auth/register", json={
        "email": "wrongpass@example.com",
        "username": "wrong_pass_user",
        "full_name": "Wrong Pass User",
        "password": "CorrectPassword123"
    })
    res = client.post("/api/v1/auth/login", json={
        "username": "wrong_pass_user",
        "password": "WrongPassword"
    })
    assert res.status_code == 401


def test_get_me_authenticated(client, auth_headers):
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "fitwarrior"


def test_get_me_unauthenticated(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
