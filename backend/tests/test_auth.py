def test_register_and_login(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "student@example.edu", "password": "supersecret123", "full_name": "Ada"},
    )
    assert register_response.status_code == 201
    body = register_response.json()
    assert body["email"] == "student@example.edu"
    assert body["role"] == "student"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.edu", "password": "supersecret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token

    me_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "student@example.edu"


def test_duplicate_registration_rejected(client):
    payload = {"email": "dup@example.edu", "password": "supersecret123"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_wrong_password_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@example.edu", "password": "supersecret123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.edu", "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
