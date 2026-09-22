"""
Unit Tests for OmniQuant Feature Engine & Black-Scholes Greeks
"""
import unittest
import pandas as pd
import numpy as np
from data.feature_engine import feature_engine
from core.models.types import OptionType

class TestFeatureEngine(unittest.TestCase):
    def setUp(self):
        # 构造上行趋势价格序列
        prices = [100.0 + i * 1.5 + np.sin(i) for i in range(50)]
        self.series = pd.Series(prices)

    def test_rsi_calculation(self):
        rsi = feature_engine.calculate_rsi(self.series, period=14)
        self.assertIsInstance(rsi, float)
        self.assertGreaterEqual(rsi, 0.0)
        self.assertLessEqual(rsi, 100.0)

    def test_macd_calculation(self):
        macd = feature_engine.calculate_macd(self.series)
        self.assertIn("macd", macd)
        self.assertIn("signal", macd)
        self.assertIn("hist", macd)

    def test_bollinger_bands(self):
        bb = feature_engine.calculate_bollinger_bands(self.series, window=20)
        self.assertGreaterEqual(bb["upper"], bb["middle"])
        self.assertGreaterEqual(bb["middle"], bb["lower"])
        self.assertGreater(bb["bandwidth"], 0.0)

    def test_black_scholes_call_greeks(self):
        # 50ETF 期权测试：S=2.60, K=2.60, T=30/365, r=2%, sigma=20%
        greeks = feature_engine.calculate_black_scholes_greeks(
            S=2.60, K=2.60, T=30.0 / 365.0, r=0.02, sigma=0.20, option_type=OptionType.CALL
        )
        self.assertGreater(greeks["price"], 0.0)
        # 平值 Call 的 Delta 应当在 0.45 ~ 0.55 之间
        self.assertAlmostEqual(greeks["delta"], 0.51, delta=0.08)
        self.assertGreater(greeks["gamma"], 0.0)
        self.assertGreater(greeks["vega"], 0.0)
        self.assertLess(greeks["theta"], 0.0) # 时间价值衰减为负

    def test_black_scholes_put_greeks(self):
        greeks = feature_engine.calculate_black_scholes_greeks(
            S=2.60, K=2.60, T=30.0 / 365.0, r=0.02, sigma=0.20, option_type=OptionType.PUT
        )
        self.assertGreater(greeks["price"], 0.0)
        # 平值 Put 的 Delta 应当在 -0.55 ~ -0.45 之间
        self.assertAlmostEqual(greeks["delta"], -0.49, delta=0.08)

if __name__ == "__main__":
    unittest.main()
