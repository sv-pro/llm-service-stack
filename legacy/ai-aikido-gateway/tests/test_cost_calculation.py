"""
Tests for cost calculation logic in RequestHistoryPlugin
"""

import pytest
from src.core.costs import calculate_completion_cost as calculate_cost, get_completion_pricing as get_model_pricing


class TestCostCalculation:
    """Test cost calculation functions"""

    def test_get_model_pricing_gpt_3_5_turbo(self):
        """Test pricing lookup for GPT-3.5-Turbo"""
        pricing = get_model_pricing("gpt-3.5-turbo")
        assert pricing is not None
        assert pricing["input"] == 0.50
        assert pricing["output"] == 1.50

    def test_get_model_pricing_gpt_4(self):
        """Test pricing lookup for GPT-4"""
        pricing = get_model_pricing("gpt-4")
        assert pricing is not None
        assert pricing["input"] == 30.00
        assert pricing["output"] == 60.00

    def test_get_model_pricing_gpt_5(self):
        """Test pricing lookup for GPT-5"""
        pricing = get_model_pricing("gpt-5")
        assert pricing is not None
        assert pricing["input"] == 2.50
        assert pricing["output"] == 10.00

    def test_get_model_pricing_nonexistent_model(self):
        """Test pricing lookup for non-existent model"""
        pricing = get_model_pricing("nonexistent-model")
        assert pricing is None

    def test_calculate_cost_gpt_3_5_turbo(self):
        """Test cost calculation for GPT-3.5-Turbo"""
        # 100 input tokens, 50 output tokens
        # Cost = (100 / 1,000,000 * 0.50) + (50 / 1,000,000 * 1.50)
        # Cost = 0.00005 + 0.000075 = 0.000125
        cost = calculate_cost("gpt-3.5-turbo", 100, 50)
        assert cost == pytest.approx(0.000125, abs=1e-6)

    def test_calculate_cost_gpt_4(self):
        """Test cost calculation for GPT-4"""
        # 1000 input tokens, 500 output tokens
        # Cost = (1000 / 1,000,000 * 30.00) + (500 / 1,000,000 * 60.00)
        # Cost = 0.03 + 0.03 = 0.06
        cost = calculate_cost("gpt-4", 1000, 500)
        assert cost == pytest.approx(0.06, abs=1e-6)

    def test_calculate_cost_gpt_5(self):
        """Test cost calculation for GPT-5"""
        # 10000 input tokens, 5000 output tokens
        # Cost = (10000 / 1,000,000 * 2.50) + (5000 / 1,000,000 * 10.00)
        # Cost = 0.025 + 0.05 = 0.075
        cost = calculate_cost("gpt-5", 10000, 5000)
        assert cost == pytest.approx(0.075, abs=1e-6)

    def test_calculate_cost_large_request(self):
        """Test cost calculation for large request with GPT-4"""
        # 100,000 input tokens, 50,000 output tokens
        # Cost = (100000 / 1,000,000 * 30.00) + (50000 / 1,000,000 * 60.00)
        # Cost = 3.0 + 3.0 = 6.0
        cost = calculate_cost("gpt-4", 100000, 50000)
        assert cost == pytest.approx(6.0, abs=1e-6)

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        cost = calculate_cost("gpt-4", 0, 0)
        assert cost == 0.0

    def test_calculate_cost_none_prompt_tokens(self):
        """Test cost calculation with None prompt tokens"""
        cost = calculate_cost("gpt-4", None, 100)
        assert cost == 0.0

    def test_calculate_cost_none_completion_tokens(self):
        """Test cost calculation with None completion tokens"""
        cost = calculate_cost("gpt-4", 100, None)
        assert cost == 0.0

    def test_calculate_cost_nonexistent_model(self):
        """Test cost calculation for non-existent model"""
        cost = calculate_cost("nonexistent-model", 100, 50)
        assert cost == 0.0

    def test_calculate_cost_rounding(self):
        """Test cost calculation rounding to 6 decimal places"""
        # 1 input token, 1 output token for GPT-3.5-Turbo
        # Cost = (1 / 1,000,000 * 0.50) + (1 / 1,000,000 * 1.50)
        # Cost = 0.0000005 + 0.0000015 = 0.000002
        cost = calculate_cost("gpt-3.5-turbo", 1, 1)
        assert cost == 0.000002

    def test_calculate_cost_all_models(self):
        """Test that cost calculation works for all GPT models"""
        models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
        for model in models:
            cost = calculate_cost(model, 1000, 500)
            assert cost > 0, f"Cost should be positive for {model}"

    def test_cost_comparison_models(self):
        """Test that GPT-5 models are cheaper than GPT-4"""
        cost_gpt4 = calculate_cost("gpt-4", 10000, 10000)
        cost_gpt5 = calculate_cost("gpt-5", 10000, 10000)
        cost_gpt5_mini = calculate_cost("gpt-5-mini", 10000, 10000)
        cost_gpt5_nano = calculate_cost("gpt-5-nano", 10000, 10000)

        # GPT-5 should be significantly cheaper than GPT-4
        assert cost_gpt5 < cost_gpt4

        # GPT-5 variants should be progressively cheaper
        assert cost_gpt5_nano < cost_gpt5_mini < cost_gpt5
