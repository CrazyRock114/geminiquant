"""
Unit tests for CustomStrategyValidator
Validates stop loss requirements, indicator limits, health score, and suggestions.
"""
import unittest
from backtest.custom_strategy_validator import CustomStrategyValidator

class TestCustomStrategyValidator(unittest.TestCase):

    def test_missing_stop_loss_rejected(self):
        """测试未设置止损线必须被强制拦截拒绝"""
        bad_config = {
            "name": "裸奔策略",
            "strategy_type": "TREND",
            "indicators": {
                "rsi": {"period": 14, "oversold": 30, "overbought": 70}
            },
            "entry_rules": {
                "long_condition": "RSI_OVERSOLD"
            },
            "risk_management": {
                "stop_loss_pct": 0.0, # 缺失止损
                "leverage": 1.0
            }
        }
        res = CustomStrategyValidator.validate(bad_config)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("强制风控拦截" in err for err in res["errors"]))
        self.assertLess(res["score"], 70)

    def test_inverted_ema_rejected(self):
        """测试快线周期大于等于慢线周期必须被逻辑拦截"""
        bad_config = {
            "name": "倒错均线",
            "indicators": {
                "ema": {"fast_period": 30, "slow_period": 10} # 快线 > 慢线
            },
            "entry_rules": {
                "long_condition": "EMA_GOLDEN_CROSS"
            },
            "risk_management": {
                "stop_loss_pct": 3.0,
                "leverage": 1.0
            }
        }
        res = CustomStrategyValidator.validate(bad_config)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("快线周期" in err for err in res["errors"]))

    def test_excessive_leverage_rejected(self):
        """测试杠杆超过5x必须被熔断拦截"""
        bad_config = {
            "name": "高杠杆赌徒",
            "indicators": {
                "rsi": {"period": 14, "oversold": 30, "overbought": 70}
            },
            "entry_rules": {
                "long_condition": "RSI_OVERSOLD"
            },
            "risk_management": {
                "stop_loss_pct": 2.0,
                "leverage": 20.0 # 超高杠杆
            }
        }
        res = CustomStrategyValidator.validate(bad_config)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("杠杆熔断" in err for err in res["errors"]))

    def test_valid_strategy_passes_with_high_score(self):
        """测试合规自定义策略通过并获得高评分"""
        good_config = {
            "name": "稳健双均线动量策略",
            "strategy_type": "TREND",
            "indicators": {
                "ema": {"fast_period": 12, "slow_period": 26},
                "rsi": {"period": 14, "oversold": 30.0, "overbought": 70.0}
            },
            "entry_rules": {
                "long_condition": "COMPOSITE_EMA_RSI",
                "short_condition": "COMPOSITE_EMA_RSI"
            },
            "risk_management": {
                "stop_loss_pct": 3.0,
                "take_profit_pct": 6.0, # 盈亏比 2:1
                "leverage": 2.0
            }
        }
        res = CustomStrategyValidator.validate(good_config)
        self.assertTrue(res["is_valid"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertGreaterEqual(res["score"], 80)
        self.assertIn("A+", res["grade"])
        self.assertTrue(any("符合量化正期望特征" in s for s in res["suggestions"]))

if __name__ == "__main__":
    unittest.main()
