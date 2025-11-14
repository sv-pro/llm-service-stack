"""Tests for normalization pipeline and rules."""

import pytest
from pydantic import BaseModel
from typing import List, Optional

from src.core.normalization import (
    CanonicalizeToolPayloadRule,
    NormalizationPipeline,
    NormalizeTemperatureRule,
    StandardizeWhitespaceRule,
    TrimSystemPromptRule,
)


# Mock message and request models for testing
class MockMessage(BaseModel):
    role: str
    content: str


class MockRequest(BaseModel):
    messages: List[MockMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[dict]] = None
    tool_choice: Optional[str] = None


class TestTrimSystemPromptRule:
    """Tests for TrimSystemPromptRule."""

    def test_trim_system_message(self):
        """Test that system messages are trimmed."""
        rule = TrimSystemPromptRule()
        request = MockRequest(
            messages=[
                MockMessage(role="system", content="  System prompt  "),
                MockMessage(role="user", content="  User message  ")
            ]
        )

        result = rule.apply(request)

        assert result.messages[0].content == "System prompt"
        assert result.messages[1].content == "  User message  "  # User not trimmed

    def test_no_system_message(self):
        """Test with no system messages."""
        rule = TrimSystemPromptRule()
        request = MockRequest(
            messages=[
                MockMessage(role="user", content="Test")
            ]
        )

        result = rule.apply(request)

        assert result.messages[0].content == "Test"


class TestStandardizeWhitespaceRule:
    """Tests for StandardizeWhitespaceRule."""

    def test_collapse_spaces(self):
        """Test that multiple spaces are collapsed."""
        rule = StandardizeWhitespaceRule()
        request = MockRequest(
            messages=[
                MockMessage(role="user", content="Hello    world")
            ]
        )

        result = rule.apply(request)

        assert result.messages[0].content == "Hello world"

    def test_normalize_line_endings(self):
        """Test that line endings are normalized."""
        rule = StandardizeWhitespaceRule()
        request = MockRequest(
            messages=[
                MockMessage(role="user", content="Line1\r\nLine2\nLine3")
            ]
        )

        result = rule.apply(request)

        assert "\r\n" not in result.messages[0].content
        assert "Line1\nLine2\nLine3" == result.messages[0].content

    def test_remove_trailing_spaces(self):
        """Test that trailing spaces are removed."""
        rule = StandardizeWhitespaceRule()
        request = MockRequest(
            messages=[
                MockMessage(role="user", content="Line1  \nLine2  ")
            ]
        )

        result = rule.apply(request)

        assert result.messages[0].content == "Line1\nLine2"

    def test_trim_overall(self):
        """Test that overall content is trimmed."""
        rule = StandardizeWhitespaceRule()
        request = MockRequest(
            messages=[
                MockMessage(role="user", content="  \n  Content  \n  ")
            ]
        )

        result = rule.apply(request)

        assert result.messages[0].content == "Content"


class TestNormalizeTemperatureRule:
    """Tests for NormalizeTemperatureRule."""

    def test_round_temperature(self):
        """Test that temperature is rounded."""
        rule = NormalizeTemperatureRule()
        request = MockRequest(
            messages=[MockMessage(role="user", content="Test")],
            temperature=0.7654321
        )

        result = rule.apply(request)

        assert result.temperature == 0.77

    def test_very_small_temperature(self):
        """Test that very small temperatures become 0."""
        rule = NormalizeTemperatureRule()
        request = MockRequest(
            messages=[MockMessage(role="user", content="Test")],
            temperature=0.005
        )

        result = rule.apply(request)

        assert result.temperature == 0.0

    def test_round_top_p(self):
        """Test that top_p is rounded."""
        rule = NormalizeTemperatureRule()
        request = MockRequest(
            messages=[MockMessage(role="user", content="Test")],
            top_p=0.9123456
        )

        result = rule.apply(request)

        assert result.top_p == 0.91

    def test_normalize_max_tokens(self):
        """Test that max_tokens is converted to int if somehow passed as float."""
        rule = NormalizeTemperatureRule()
        # Create request with valid data first
        request = MockRequest(
            messages=[MockMessage(role="user", content="Test")],
            max_tokens=100
        )

        # Simulate a scenario where max_tokens gets set to float somehow
        # (e.g., from unvalidated API input or calculation)
        request.max_tokens = 100.7

        result = rule.apply(request)

        assert result.max_tokens == 100
        assert isinstance(result.max_tokens, int)

    def test_none_values(self):
        """Test that None values are handled."""
        rule = NormalizeTemperatureRule()
        request = MockRequest(
            messages=[MockMessage(role="user", content="Test")],
            temperature=None,
            top_p=None
        )

        result = rule.apply(request)

        assert result.temperature is None
        assert result.top_p is None


class TestCanonicalizeToolPayloadRule:
    """Tests for CanonicalizeToolPayloadRule."""

    def test_sort_tools(self):
        """Test that tools are sorted by name."""
        rule = CanonicalizeToolPayloadRule()
        request = MockRequest(
            messages=[MockMessage(role="user", content="Test")],
            tools=[
                {"function": {"name": "z_tool"}},
                {"function": {"name": "a_tool"}},
                {"function": {"name": "m_tool"}},
            ]
        )

        result = rule.apply(request)

        assert result.tools[0]["function"]["name"] == "a_tool"
        assert result.tools[1]["function"]["name"] == "m_tool"
        assert result.tools[2]["function"]["name"] == "z_tool"

    def test_normalize_tool_choice_auto(self):
        """Test that tool_choice is normalized to 'auto'."""
        rule = CanonicalizeToolPayloadRule()

        for value in [None, "auto", "none"]:
            request = MockRequest(
                messages=[MockMessage(role="user", content="Test")],
                tool_choice=value
            )

            result = rule.apply(request)

            assert result.tool_choice == "auto"

    def test_preserve_specific_tool_choice(self):
        """Test that specific tool_choice is preserved."""
        rule = CanonicalizeToolPayloadRule()
        request = MockRequest(
            messages=[MockMessage(role="user", content="Test")],
            tool_choice="required"
        )

        result = rule.apply(request)

        assert result.tool_choice == "required"


class TestNormalizationPipeline:
    """Tests for NormalizationPipeline."""

    def test_apply_all_rules(self):
        """Test that all rules are applied in sequence."""
        pipeline = NormalizationPipeline()
        request = MockRequest(
            messages=[
                MockMessage(role="system", content="  System  "),
                MockMessage(role="user", content="Hello    world  ")
            ],
            temperature=0.7654
        )

        result = pipeline.normalize(request)

        # Check each rule was applied
        assert result.messages[0].content == "System"  # Trimmed
        assert result.messages[1].content == "Hello world"  # Whitespace normalized
        assert result.temperature == 0.77  # Rounded

    def test_disabled_pipeline(self):
        """Test that disabled pipeline returns original."""
        pipeline = NormalizationPipeline(enabled=False)
        original = MockRequest(
            messages=[MockMessage(role="user", content="  Test  ")],
            temperature=0.7654
        )

        result = pipeline.normalize(original)

        # Should be unchanged
        assert result.messages[0].content == "  Test  "
        assert result.temperature == 0.7654

    def test_custom_rules(self):
        """Test pipeline with custom rules."""
        pipeline = NormalizationPipeline(
            rules=[TrimSystemPromptRule()]  # Only one rule
        )
        request = MockRequest(
            messages=[
                MockMessage(role="system", content="  System  "),
                MockMessage(role="user", content="  User  ")
            ]
        )

        result = pipeline.normalize(request)

        # Only system trimming should be applied
        assert result.messages[0].content == "System"
        assert result.messages[1].content == "  User  "  # User not affected

    def test_add_rule(self):
        """Test adding a rule to the pipeline."""
        pipeline = NormalizationPipeline(rules=[])
        assert len(pipeline.rules) == 0

        pipeline.add_rule(TrimSystemPromptRule())
        assert len(pipeline.rules) == 1

    def test_remove_rule(self):
        """Test removing a rule from the pipeline."""
        pipeline = NormalizationPipeline()
        initial_count = len(pipeline.rules)

        pipeline.remove_rule(TrimSystemPromptRule)
        assert len(pipeline.rules) == initial_count - 1

    def test_deep_copy(self):
        """Test that pipeline creates a deep copy."""
        pipeline = NormalizationPipeline()
        original = MockRequest(
            messages=[MockMessage(role="user", content="  Test  ")],
            temperature=0.7654
        )

        result = pipeline.normalize(original)

        # Verify original is unchanged
        assert original.messages[0].content == "  Test  "
        assert original.temperature == 0.7654

        # Verify result is modified
        assert result.messages[0].content == "Test"
        assert result.temperature == 0.77

    def test_error_handling(self):
        """Test that errors in one rule don't break the pipeline."""
        class FaultyRule:
            def apply(self, request):
                raise ValueError("Test error")

        pipeline = NormalizationPipeline(
            rules=[
                TrimSystemPromptRule(),
                FaultyRule(),  # This will fail
                StandardizeWhitespaceRule()  # This should still run
            ]
        )

        request = MockRequest(
            messages=[
                MockMessage(role="system", content="  Test  ")
            ]
        )

        # Should not raise, should continue with other rules
        result = pipeline.normalize(request)

        # First rule should have been applied
        assert result.messages[0].content.strip() == "Test"
