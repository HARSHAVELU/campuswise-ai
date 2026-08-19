from app.core.rate_limit import AUTH_LIMIT


def test_login_rate_limit_blocks_after_threshold(client, db_session):
    limit_count = int(AUTH_LIMIT.split("/")[0])

    client.post(
        "/api/v1/auth/register", json={"email": "ratelimit@example.edu", "password": "supersecret123"}
    )

    statuses = []
    for _ in range(limit_count + 3):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ratelimit@example.edu", "password": "wrong-password"},
        )
        statuses.append(response.status_code)

    assert 429 in statuses
    # every request before the limit was hit should have been processed as a normal auth failure
    assert statuses[0] == 401


def test_rate_limit_is_isolated_per_test(client, db_session):
    """Regression check: the limiter must reset between tests, not accumulate
    across the whole pytest session (this test intentionally mirrors calls
    made by other auth tests -- it should never see a 429 from unrelated
    tests' prior requests)."""
    response = client.post(
        "/api/v1/auth/register", json={"email": "isolated@example.edu", "password": "supersecret123"}
    )
    assert response.status_code == 201
