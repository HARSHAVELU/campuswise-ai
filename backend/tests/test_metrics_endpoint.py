def test_metrics_endpoint_exposes_prometheus_text_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "python_gc_objects_collected_total" in response.text


def test_metrics_endpoint_exposes_request_counters_after_traffic(client):
    client.get("/api/v1/health")
    client.get("/api/v1/health")
    response = client.get("/metrics")
    assert "http_requests_total" in response.text or "http_request_duration_seconds" in response.text


def test_metrics_endpoint_exposes_ai_fallback_counter_after_a_search(client, db_session):
    # No ANTHROPIC_API_KEY in the test environment, so this goes through the
    # rule-based fallback and should be visible on /metrics.
    client.post("/api/v1/ai/search", json={"query": "find me a python class"})
    response = client.get("/metrics")
    assert "campuswise_fallback_total" in response.text
    assert 'purpose="requirement_parsing"' in response.text
