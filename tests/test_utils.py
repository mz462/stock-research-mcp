"""Tests for utility functions."""

import pytest
from stock_research.utils.calculations import (
    calculate_support_resistance,
    calculate_pivot_points,
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bbands,
)


class TestSupportResistance:
    """Tests for support/resistance calculations."""

    def test_calculate_with_clear_levels(self):
        """Test with data that has clear support/resistance levels."""
        # Create price data with clear pivot points
        prices = []

        # Add a clear support level around 100
        for i in range(5):
            prices.append({
                "date": f"2026-01-{20-i:02d}",
                "high": 105,
                "low": 100,
                "close": 102,
            })

        # Add a clear resistance level around 110
        for i in range(5):
            prices.append({
                "date": f"2026-01-{15-i:02d}",
                "high": 110,
                "low": 105,
                "close": 108,
            })

        # Add some middle data
        for i in range(10):
            prices.append({
                "date": f"2026-01-{10-i:02d}" if i < 10 else f"2025-12-{31-i+10:02d}",
                "high": 107,
                "low": 103,
                "close": 105,
            })

        support, resistance = calculate_support_resistance(prices)

        # Should find some levels
        assert isinstance(support, list)
        assert isinstance(resistance, list)

    def test_calculate_with_empty_data(self):
        """Test with empty price data."""
        support, resistance = calculate_support_resistance([])

        assert support == []
        assert resistance == []

    def test_calculate_with_minimal_data(self):
        """Test with minimal price data (less than 5 points)."""
        prices = [
            {"date": "2026-01-03", "high": 150, "low": 148, "close": 149},
            {"date": "2026-01-02", "high": 149, "low": 147, "close": 148},
        ]

        support, resistance = calculate_support_resistance(prices)

        # Should return empty lists for insufficient data
        assert isinstance(support, list)
        assert isinstance(resistance, list)


class TestPivotPoints:
    """Tests for pivot point calculations."""

    def test_classic_pivot_points(self):
        """Test classic pivot point calculation."""
        result = calculate_pivot_points(high=155.0, low=145.0, close=150.0)

        assert "pivot" in result
        assert "r1" in result
        assert "r2" in result
        assert "r3" in result
        assert "s1" in result
        assert "s2" in result
        assert "s3" in result

        # Verify pivot calculation: (H + L + C) / 3
        expected_pivot = (155.0 + 145.0 + 150.0) / 3
        assert result["pivot"] == round(expected_pivot, 2)

        # Verify R1: 2 * P - L
        expected_r1 = 2 * expected_pivot - 145.0
        assert result["r1"] == round(expected_r1, 2)

        # Verify S1: 2 * P - H
        expected_s1 = 2 * expected_pivot - 155.0
        assert result["s1"] == round(expected_s1, 2)

    def test_pivot_points_symmetry(self):
        """Test that pivot points maintain expected relationships."""
        result = calculate_pivot_points(high=100.0, low=90.0, close=95.0)

        # R levels should be above pivot
        assert result["r1"] > result["pivot"]
        assert result["r2"] > result["r1"]
        assert result["r3"] > result["r2"]

        # S levels should be below pivot
        assert result["s1"] < result["pivot"]
        assert result["s2"] < result["s1"]
        assert result["s3"] < result["s2"]


class TestClusterLevels:
    """Tests for level clustering logic."""

    def test_clustering_nearby_levels(self):
        """Test that nearby levels are clustered together."""
        # Create prices with multiple touches at similar levels
        prices = []

        # Multiple touches around 100 (should cluster)
        for i in range(20):
            # Alternate between touching support and bouncing
            if i % 4 == 0:
                prices.append({
                    "date": f"2026-01-{20-i:02d}" if i < 20 else f"2025-12-{40-i:02d}",
                    "high": 105,
                    "low": 99.5 + (i % 3) * 0.3,  # Varies between 99.5 and 100.1
                    "close": 103,
                })
            else:
                prices.append({
                    "date": f"2026-01-{20-i:02d}" if i < 20 else f"2025-12-{40-i:02d}",
                    "high": 108,
                    "low": 102,
                    "close": 106,
                })

        support, resistance = calculate_support_resistance(prices, threshold=0.02)

        # Should cluster nearby support levels into fewer distinct levels
        assert len(support) <= len(prices) // 2


class TestTechnicalIndicators:
    """Tests for technical indicator calculations."""

    def test_calculate_sma(self):
        """Test SMA calculation."""
        prices = [100, 102, 104, 103, 101, 99, 98, 100, 102, 104]  # Most recent first

        sma_5 = calculate_sma(prices, 5)
        expected = (100 + 102 + 104 + 103 + 101) / 5
        assert sma_5 == round(expected, 2)

        sma_10 = calculate_sma(prices, 10)
        expected = sum(prices) / 10
        assert sma_10 == round(expected, 2)

        # Insufficient data
        assert calculate_sma(prices[:3], 5) is None

    def test_calculate_ema(self):
        """Test EMA calculation."""
        prices = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90]  # Trending down

        ema_5 = calculate_ema(prices, 5)
        assert ema_5 is not None
        # EMA should be close to but possibly different from SMA
        sma_5 = calculate_sma(prices, 5)
        assert abs(ema_5 - sma_5) <= 2  # Within reasonable range

        # Insufficient data
        assert calculate_ema(prices[:3], 5) is None

    def test_calculate_rsi(self):
        """Test RSI calculation."""
        # Create an uptrending price series
        prices = [100 + i for i in range(20)]  # 100, 101, 102, ... 119
        prices.reverse()  # Most recent first: 119, 118, ... 100

        rsi = calculate_rsi(prices, 14)
        assert rsi is not None
        # In a consistent uptrend, RSI should be high (but not necessarily 100)
        assert rsi > 50

        # Create a downtrending price series
        prices_down = [100 - i for i in range(20)]  # 100, 99, 98, ... 81
        prices_down.reverse()  # Most recent first

        rsi_down = calculate_rsi(prices_down, 14)
        assert rsi_down is not None
        # In a consistent downtrend, RSI should be low
        assert rsi_down < 50

        # Insufficient data
        assert calculate_rsi(prices[:10], 14) is None

    def test_calculate_macd(self):
        """Test MACD calculation."""
        # Need at least slow_period + signal_period = 35 data points
        prices = [100 + (i % 10) for i in range(50)]  # Oscillating prices
        prices.reverse()

        macd = calculate_macd(prices)
        assert "macd" in macd
        assert "signal" in macd
        assert "histogram" in macd
        assert macd["macd"] is not None
        assert macd["signal"] is not None
        assert macd["histogram"] is not None

        # Histogram = MACD - Signal
        assert abs(macd["histogram"] - (macd["macd"] - macd["signal"])) < 0.001

        # Insufficient data
        short_macd = calculate_macd(prices[:20])
        assert short_macd["macd"] is None

    def test_calculate_bbands(self):
        """Test Bollinger Bands calculation."""
        prices = [100, 102, 98, 101, 99, 100, 103, 97, 102, 100,
                  101, 99, 100, 102, 98, 101, 99, 100, 103, 97]

        bbands = calculate_bbands(prices, period=20)
        assert "upper" in bbands
        assert "middle" in bbands
        assert "lower" in bbands
        assert bbands["middle"] is not None

        # Upper > Middle > Lower
        assert bbands["upper"] > bbands["middle"]
        assert bbands["middle"] > bbands["lower"]

        # Middle should be the SMA
        expected_middle = sum(prices[:20]) / 20
        assert bbands["middle"] == round(expected_middle, 2)

        # Insufficient data
        short_bbands = calculate_bbands(prices[:10], period=20)
        assert short_bbands["middle"] is None
