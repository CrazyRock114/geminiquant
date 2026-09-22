"""
Unit tests for CryptoBacktester and Strategies
"""
import unittest
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from backtest.crypto_backtester import CryptoBacktester
from backtest.strategies import StrategyRegistry, LayaMomentumStrategy, DualEMAStrategy, BollingerBandsStrategy

class TestCryptoBacktester(unittest.TestCase):
    def setUp(self):
        # 构造 100 根基准行情序列
        np.random.seed(42)
        base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        prices = [80000.0]
        for r in np.random.normal(0.0005, 0.015, 99):
            prices.append(prices[-1] * (1 + r))

        records = []
        for i, p in enumerate(prices):
            records.append({
                "timestamp": base_time + timedelta(days=i),
                "open": p * 0.998,
                "high": p * 1.01,
                "low": p * 0.99,
                "close": p,
                "volume": 1200.0,
                "turnover": 1200.0 * p
            })
        self.df = pd.DataFrame(records)

    def test_strategy_registry(self):
        strategies = StrategyRegistry.list_strategies()
        self.assertGreaterEqual(len(strategies), 3)
        strat_laya = StrategyRegistry.get_strategy("laya_momentum")
        self.assertIsInstance(strat_laya, LayaMomentumStrategy)

    def test_laya_backtest_execution(self):
        backtester = CryptoBacktester(
            strategy=LayaMomentumStrategy(),
            initial_capital=100000.0,
            leverage=2.0
        )
        res = backtester.run(self.df, symbol="BTC/USDT")
        self.assertEqual(res["symbol"], "BTC/USDT")
        metrics = res["metrics"]

        self.assertIn("total_return_pct", metrics)
        self.assertIn("max_drawdown_pct", metrics)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("win_rate_pct", metrics)
        self.assertIn("profit_factor", metrics)

        # 验证净值曲线数据点有效性
        self.assertGreater(len(res["equity_curve"]), 0)
        first_point = res["equity_curve"][0]
        self.assertIn("strategy_equity", first_point)
        self.assertIn("benchmark_equity", first_point)

    def test_dual_ema_backtest(self):
        backtester = CryptoBacktester(
            strategy=DualEMAStrategy(),
            initial_capital=50000.0,
            leverage=1.0
        )
        res = backtester.run(self.df, symbol="ETH/USDT")
        self.assertGreater(res["metrics"]["final_equity"], 0)

    def test_bollinger_backtest(self):
        backtester = CryptoBacktester(
            strategy=BollingerBandsStrategy(),
            initial_capital=100000.0,
            leverage=1.0
        )
        res = backtester.run(self.df, symbol="SOL/USDT")
        self.assertIn("metrics", res)

if __name__ == "__main__":
    unittest.main()
