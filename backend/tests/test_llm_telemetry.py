from app.core.llm_telemetry import record_fallback, track_llm_call
from app.core.metrics import FALLBACK_TOTAL, LLM_CALL_DURATION_SECONDS, LLM_CALLS_TOTAL, LLM_TOKENS_TOTAL


def _counter_value(counter, **labels) -> float:
    return counter.labels(**labels)._value.get()


def _histogram_sum(histogram, **labels) -> float:
    return histogram.labels(**labels)._sum.get()


def test_track_llm_call_records_success_counter_and_tokens():
    before = _counter_value(LLM_CALLS_TOTAL, provider="anthropic", purpose="test_success", outcome="success")

    with track_llm_call("anthropic", "test_success", "claude-sonnet-5") as rec:
        rec.input_tokens = 100
        rec.output_tokens = 25

    after = _counter_value(LLM_CALLS_TOTAL, provider="anthropic", purpose="test_success", outcome="success")
    assert after == before + 1

    input_tokens = _counter_value(
        LLM_TOKENS_TOTAL, provider="anthropic", purpose="test_success", direction="input"
    )
    output_tokens = _counter_value(
        LLM_TOKENS_TOTAL, provider="anthropic", purpose="test_success", direction="output"
    )
    assert input_tokens >= 100
    assert output_tokens >= 25


def test_track_llm_call_records_error_outcome_and_reraises():
    before = _counter_value(LLM_CALLS_TOTAL, provider="anthropic", purpose="test_error", outcome="error")

    raised = False
    try:
        with track_llm_call("anthropic", "test_error", "claude-sonnet-5") as rec:
            rec.input_tokens = 10
            raise RuntimeError("simulated provider failure")
    except RuntimeError:
        raised = True

    assert raised is True
    after = _counter_value(LLM_CALLS_TOTAL, provider="anthropic", purpose="test_error", outcome="error")
    assert after == before + 1


def test_track_llm_call_records_duration():
    before_sum = _histogram_sum(LLM_CALL_DURATION_SECONDS, provider="voyage", purpose="test_duration")

    with track_llm_call("voyage", "test_duration", "voyage-3-lite") as rec:
        rec.input_tokens = 5

    after_sum = _histogram_sum(LLM_CALL_DURATION_SECONDS, provider="voyage", purpose="test_duration")
    assert after_sum > before_sum  # a real (non-zero) duration was observed


def test_track_llm_call_without_setting_tokens_does_not_increment_token_counters():
    before_in = _counter_value(LLM_TOKENS_TOTAL, provider="anthropic", purpose="test_no_tokens", direction="input")

    with track_llm_call("anthropic", "test_no_tokens", "claude-sonnet-5"):
        pass  # never set rec.input_tokens / output_tokens

    after_in = _counter_value(LLM_TOKENS_TOTAL, provider="anthropic", purpose="test_no_tokens", direction="input")
    assert after_in == before_in  # unset tokens must not increment by None/0 spuriously


def test_record_fallback_increments_counter():
    before = _counter_value(FALLBACK_TOTAL, purpose="test_purpose", reason="no_api_key")
    record_fallback("test_purpose", "no_api_key")
    after = _counter_value(FALLBACK_TOTAL, purpose="test_purpose", reason="no_api_key")
    assert after == before + 1
