"""
Unit tests for all 12 quantitative strategies + CustomRuleStrategy
Validates signal bounds, absence of NaN, and execution through CryptoBacktester.
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest.strategies import StrategyRegistry, BaseStrategy
from backtest.crypto_backtester import CryptoBacktester

class TestAllStrategies(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 构造基准合成价格序列 (含明显趋势与震荡)
        np.random.seed(42)
        n = 120
        base_time = datetime(2026, 1, 1)
        times = [base_time + timedelta(hours=i) for i in range(n)]

        # 构造带有上涨波段与反弹波段的价格序列
        returns = np.random.normal(0.001, 0.015, n)
        returns[20:50] += 0.008  # 上涨阶段
        returns[60:85] -= 0.009  # 下跌阶段
        close = 50000.0 * np.exp(np.cumsum(returns))
        high = close * (1.0 + np.abs(np.random.normal(0.002, 0.005, n)))
        low = close * (1.0 - np.abs(np.random.normal(0.002, 0.005, n)))
        open_p = close.copy()
        open_p[1:] = close[:-1]
        volume = np.random.uniform(500.0, 3000.0, n)

        cls.df = pd.DataFrame({
            "timestamp": times,
            "open": open_p,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })

    def test_all_12_strategies_signal_integrity(self):
        """测试全量 12 款策略信号完整性：取值必须在 {-1, 0, 1}，无 NaN"""
        strat_keys = [
            "laya_momentum", "dual_ema", "macd_cross", "supertrend",
            "donchian_breakout", "bollinger", "rsi_mean_reversion",
            "keltner_channel", "stoch_rsi", "volatility_squeeze",
            "dual_thrust", "mfi_divergence"
        ]

        for key in strat_keys:
            with self.subTest(strategy=key):
                strat = StrategyRegistry.get_strategy(key)
                signals = strat.generate_signals(self.df)
                self.assertEqual(len(signals), len(self.df))
                self.assertFalse(signals.isna().any(), f"策略 {key} 信号存在 NaN")
                unique_vals = set(signals.unique())
                self.assertTrue(unique_vals.issubset({-1, 0, 1}), f"策略 {key} 存在非法信号取值: {unique_vals}")

    def test_all_strategies_backtest_execution(self):
        """测试全量策略均可在 CryptoBacktester 中顺畅执行回测并输出指标"""
        strat_keys = [
            "laya_momentum", "dual_ema", "macd_cross", "supertrend",
            "donchian_breakout", "bollinger", "rsi_mean_reversion",
            "keltner_channel", "stoch_rsi", "volatility_squeeze",
            "dual_thrust", "mfi_divergence"
        ]

        for key in strat_keys:
            with self.subTest(strategy=key):
                strat = StrategyRegistry.get_strategy(key)
                backtester = CryptoBacktester(strategy=strat, initial_capital=100000.0, leverage=1.0)
                res = backtester.run(self.df, symbol="BTC/USDT")
                self.assertIn("metrics", res)
                self.assertIn("total_return_pct", res["metrics"])
                self.assertIn("max_drawdown_pct", res["metrics"])
                self.assertIn("equity_curve", res)
                self.assertGreater(len(res["equity_curve"]), 0)

    def test_custom_rule_strategy_execution(self):
        """测试自定义规则策略引擎正常生成信号并回测"""
        custom_params = {
            "indicators": {
                "ema": {"fast_period": 10, "slow_period": 25},
                "rsi": {"period": 14, "oversold": 30.0, "overbought": 70.0}
            },
            "entry_rules": {
                "long_condition": "COMPOSITE_EMA_RSI",
                "short_condition": "COMPOSITE_EMA_RSI"
            },
            "risk_management": {
                "stop_loss_pct": 3.0,
                "take_profit_pct": 6.0,
                "leverage": 2.0
            }
        }
        strat = StrategyRegistry.get_strategy("custom_strategy", custom_params)
        signals = strat.generate_signals(self.df)
        self.assertEqual(len(signals), len(self.df))
        self.assertFalse(signals.isna().any())

        backtester = CryptoBacktester(strategy=strat, initial_capital=100000.0, leverage=2.0)
        res = backtester.run(self.df, symbol="BTC/USDT")
        self.assertIn("metrics", res)
        self.assertGreater(res["metrics"]["final_equity"], 0)

if __name__ == "__main__":
    unittest.main()
