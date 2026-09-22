"""
Unit tests for OmniQuant MatrixBacktester
Tests multi-asset x multi-strategy batch execution, leaderboard ranking, and champions generation.
"""
import unittest
import pandas as pd
import numpy as np

from backtest.matrix_backtester import MatrixBacktester
from backtest.strategies import StrategyRegistry

class TestMatrixBacktester(unittest.TestCase):
    """测试多标的多策略矩阵回测引擎"""

    def test_matrix_small_run(self):
        """测试小规模 2 标的 x 3 策略矩阵回测"""
        res = MatrixBacktester.run_matrix(
            symbols=["BTC/USDT", "ETH/USDT"],
            strategy_ids=["dual_ma", "macd_cross", "bollinger_bands"],
            interval="1d",
            limit=50
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["summary"]["total_runs"], 6)
        self.assertEqual(len(res["symbols"]), 2)
        self.assertEqual(len(res["strategies"]), 3)
        self.assertIn("BTC/USDT", res["matrix"]["dual_ema"]["results"])
        self.assertIn("ETH/USDT", res["matrix"]["dual_ema"]["results"])
        self.assertEqual(len(res["leaderboard"]), 3)
        self.assertIn("BTC/USDT", res["summary"]["symbol_champions"])
        self.assertIn("ETH/USDT", res["summary"]["symbol_champions"])
        self.assertTrue(len(res["insights"]) >= 1)

    def test_matrix_full_run_4_symbols_all_strategies(self):
        """测试全量 4 标的 (BTC, ETH, SOL, ZEC) x 12 款策略 1 年历史回测"""
        res = MatrixBacktester.run_matrix(
            symbols=["BTC/USDT", "ETH/USDT", "SOL/USDT", "ZEC/USDT"],
            strategy_ids=None, # 全部 12 款策略
            interval="1d",
            limit=365
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["summary"]["symbols_count"], 4)
        self.assertEqual(res["summary"]["strategies_count"], 12)
        self.assertEqual(res["summary"]["total_runs"], 48)

        # 验证排行榜
        lb = res["leaderboard"]
        self.assertEqual(len(lb), 12)
        self.assertEqual(lb[0]["rank"], 1)
        self.assertEqual(lb[-1]["rank"], 12)
        self.assertGreaterEqual(lb[0]["composite_score"], lb[-1]["composite_score"])

        # 验证单标的冠军
        champs = res["summary"]["symbol_champions"]
        self.assertIn("BTC/USDT", champs)
        self.assertIn("ETH/USDT", champs)
        self.assertIn("SOL/USDT", champs)
        self.assertIn("ZEC/USDT", champs)

        # 验证执行速度
        self.assertLess(res["summary"]["execution_time_seconds"], 10.0)

    def test_invalid_symbol_graceful_handling(self):
        """测试包含异常标的时系统优雅容错"""
        res = MatrixBacktester.run_matrix(
            symbols=["BTC/USDT", "NON_EXISTENT_COIN_XYZ/USDT"],
            strategy_ids=["dual_ma"],
            interval="1d",
            limit=30
        )
        # BTC/USDT 仍可正常成功计算，系统不崩溃
        self.assertTrue(res["success"])
        self.assertIn("BTC/USDT", res["symbols"])

if __name__ == "__main__":
    unittest.main()
