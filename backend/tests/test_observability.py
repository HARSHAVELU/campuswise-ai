def test_response_includes_request_id_header(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 12


def test_request_ids_differ_across_requests(client):
    first = client.get("/api/v1/health").headers["X-Request-ID"]
    second = client.get("/api/v1/health").headers["X-Request-ID"]
    assert first != second


def test_unhandled_exception_returns_clean_json_not_a_traceback():
    from fastapi.testclient import TestClient

    from app.api.deps import get_db
    from app.main import app

    def broken_db():
        raise RuntimeError("simulated database outage")
        yield  # pragma: no cover - unreachable, keeps this a generator for the dependency override

    app.dependency_overrides[get_db] = broken_db
    try:
        # raise_server_exceptions=False: we want to inspect the actual HTTP
        # response our exception handler produces, not have the test client
        # re-raise the exception past it.
        with TestClient(app, raise_server_exceptions=False) as test_client:
            response = test_client.get("/api/v1/courses")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 500
    body = response.json()
    assert body["error_code"] == "internal_error"
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
