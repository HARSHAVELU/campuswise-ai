from unittest.mock import MagicMock, patch

import pytest

from app.agents.llm_parser import LLMParserError, parse_requirement_with_llm


def test_raises_when_no_api_key_configured():
    with patch("app.agents.llm_parser.get_settings") as mock_settings:
        mock_settings.return_value.anthropic_api_key = None
        with pytest.raises(LLMParserError, match="not configured"):
            parse_requirement_with_llm("find me a python class")


def test_parses_valid_tool_use_response():
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {
        "topic": "python",
        "hard_constraints": {"delivery_modes": ["online"]},
        "soft_preferences": {"prefer_higher_rated_professor": True},
        "unsupported_notes": [],
    }
    mock_response = MagicMock()
    mock_response.content = [tool_block]
    mock_response.usage.input_tokens = 120
    mock_response.usage.output_tokens = 45

    with patch("app.agents.llm_parser.get_settings") as mock_settings, patch(
        "app.agents.llm_parser.anthropic.Anthropic"
    ) as mock_anthropic_cls:
        mock_settings.return_value.anthropic_api_key = "fake-key"
        mock_settings.return_value.anthropic_model = "claude-sonnet-5"
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        parsed = parse_requirement_with_llm("find me an online python class")

    assert parsed.topic == "python"
    assert parsed.hard_constraints.delivery_modes == ["online"]
    assert parsed.soft_preferences.prefer_higher_rated_professor is True
    assert parsed.parser_source == "llm"


def test_raises_when_no_tool_use_block_returned():
    text_block = MagicMock()
    text_block.type = "text"
    mock_response = MagicMock()
    mock_response.content = [text_block]
    mock_response.usage.input_tokens = 80
    mock_response.usage.output_tokens = 10

    with patch("app.agents.llm_parser.get_settings") as mock_settings, patch(
        "app.agents.llm_parser.anthropic.Anthropic"
    ) as mock_anthropic_cls:
        mock_settings.return_value.anthropic_api_key = "fake-key"
        mock_settings.return_value.anthropic_model = "claude-sonnet-5"
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        with pytest.raises(LLMParserError, match="did not return a tool_use block"):
            parse_requirement_with_llm("find me a python class")


def test_requirement_parser_falls_back_when_llm_fails():
    from app.agents.requirement_parser import parse_requirement

    with patch("app.agents.requirement_parser.get_settings") as mock_settings, patch(
        "app.agents.requirement_parser.parse_requirement_with_llm"
    ) as mock_llm_parse:
        mock_settings.return_value.anthropic_api_key = "fake-key"
        mock_llm_parse.side_effect = LLMParserError("boom")

        parsed = parse_requirement("Find me a Python class.")

    assert parsed.parser_source == "rule_based"
    assert parsed.topic == "python"
