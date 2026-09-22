"""
Unit Tests for OmniQuant Pre-Trade Risk Manager & Market Compliance Guards
"""
import unittest
from core.models.types import AssetClass, OrderSide
from core.models.order import OrderRequest, Position, AccountBalance
from core.models.market_data import TickData
from decision.schema import DecisionResult
from risk.risk_manager import risk_manager

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.account = AccountBalance(
            total_equity=1000000.0,
            available_cash=1000000.0,
            initial_equity=1000000.0,
            peak_equity=1000000.0,
            daily_start_equity=1000000.0
        )
        self.normal_decision = DecisionResult(
            action="BUY",
            urgency="PASSIVE_MAKER",
            confidence="HIGH",
            risk_passed=True,
            size_factor="HALF",
            latency_ms=1.5
        )

    def test_drawdown_circuit_breaker(self):
        # 模拟当日回撤达到 3.5% (超过 3.0% 限制)
        self.account.total_equity = 965000.0
        order = OrderRequest(
            symbol="BTC/USDT",
            asset_class=AssetClass.CRYPTO,
            side=OrderSide.BUY,
            price=60000.0,
            volume=0.1
        )
        passed, reason = risk_manager.check_pre_trade_risk(order, self.normal_decision, self.account)
        self.assertFalse(passed)
        self.assertIn("账户回撤熔断", reason)

    def test_ashare_t_plus_1_rejection(self):
        # 尝试卖出 A 股，但持仓可用数量为 0 (今日买入的 T+0 头寸)
        self.account.positions["600519.SH"] = Position(
            symbol="600519.SH",
            asset_class=AssetClass.EQUITY_CN,
            side=OrderSide.BUY,
            volume=100.0,
            available_volume=0.0, # T+0 未结算
            avg_open_price=1600.0,
            last_price=1620.0
        )
        sell_order = OrderRequest(
            symbol="600519.SH",
            asset_class=AssetClass.EQUITY_CN,
            side=OrderSide.SELL,
            price=1620.0,
            volume=100.0
        )
        passed, reason = risk_manager.check_pre_trade_risk(sell_order, self.normal_decision, self.account)
        self.assertFalse(passed)
        self.assertIn("A股 T+1 违规拦截", reason)

    def test_limit_up_buy_interception(self):
        # 模拟涨停板禁止挂买
        tick = TickData(
            symbol="600519.SH",
            asset_class=AssetClass.EQUITY_CN,
            last_price=1760.0,
            upper_limit_price=1760.0, # 触及涨停
            lower_limit_price=1440.0
        )
        buy_order = OrderRequest(
            symbol="600519.SH",
            asset_class=AssetClass.EQUITY_CN,
            side=OrderSide.BUY,
            price=1760.0,
            volume=100.0
        )
        passed, reason = risk_manager.check_pre_trade_risk(buy_order, self.normal_decision, self.account, tick)
        self.assertFalse(passed)
        self.assertIn("涨停板拦截", reason)

    def test_position_concentration_limit(self):
        # 拟买入单笔金额 300,000 元（占总资产 1,000,000 的 30%，超过 20% 限制）
        huge_order = OrderRequest(
            symbol="AAPL.US",
            asset_class=AssetClass.EQUITY_US_HK,
            side=OrderSide.BUY,
            price=300.0,
            volume=1000.0 # 300,000
        )
        passed, reason = risk_manager.check_pre_trade_risk(huge_order, self.normal_decision, self.account)
        self.assertFalse(passed)
        self.assertIn("集中度超限", reason)

if __name__ == "__main__":
    unittest.main()
