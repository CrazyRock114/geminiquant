"""
Unit Tests for OmniQuant Laya Decision Engine (System 1)
"""
import unittest
from decision.laya_engine import LayaDecisionEngine
from decision.schema import DecisionResult

class TestLayaDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = LayaDecisionEngine(preload=False)
        self.sample_state = {
            "market_snapshot": "Symbol: BTC/USDT, Asset: CRYPTO, Last: 64250.0, Spread_Bps: 2.3",
            "technical_indicators": "RSI=28.5, MACD_Hist=1.25, BB_Bandwidth=0.035, OFI_Imbalance=0.45",
            "system2_research": "Macro_Regime=BULL_EXPANSION, Debate_Winner=BULL, Sentiment_Score=0.75",
            "portfolio_risk": "Daily_Drawdown=0.50%, Peak_Drawdown=1.20%, Margin_Ratio=25.0%, Available_Cash=850000"
        }

    def test_evaluate_returns_valid_typed_decision(self):
        decision = self.engine.evaluate(self.sample_state)
        self.assertIsInstance(decision, DecisionResult)
        self.assertIn(decision.action, ["STRONG_BUY", "BUY", "HOLD", "REDUCE", "STRONG_SELL"])
        self.assertIn(decision.urgency, ["PASSIVE_MAKER", "AGGRESSIVE_TAKER", "CANCEL_ALL"])
        self.assertIn(decision.confidence, ["HIGH", "MEDIUM", "LOW"])
        self.assertIsInstance(decision.risk_passed, bool)
        self.assertLess(decision.latency_ms, 50.0) # 延迟必须在 50ms 以内

    def test_high_drawdown_triggers_risk_rejection(self):
        # 构造高回撤状态
        high_risk_state = dict(self.sample_state)
        high_risk_state["portfolio_risk"] = "Daily_Drawdown=4.20%, Peak_Drawdown=5.50%, Margin_Ratio=85.0%, Available_Cash=50000"
        decision = self.engine.evaluate(high_risk_state)
        self.assertFalse(decision.risk_passed)
        self.assertIn(decision.action, ("REDUCE", "STRONG_SELL", "HOLD"))

if __name__ == "__main__":
    unittest.main()
