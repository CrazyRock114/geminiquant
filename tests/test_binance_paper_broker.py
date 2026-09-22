"""
Unit tests for BinancePaperBroker
"""
import unittest
from execution.binance_paper_broker import BinancePaperBroker

class TestBinancePaperBroker(unittest.TestCase):
    def setUp(self):
        self.broker = BinancePaperBroker(initial_cash=100000.0)

    def test_initial_snapshot(self):
        snap = self.broker.get_account_snapshot()
        self.assertEqual(snap["initial_cash"], 100000.0)
        self.assertEqual(snap["available_cash"], 100000.0)
        self.assertEqual(snap["positions_count"], 0)

    def test_place_order_and_margin(self):
        # 模拟开多 0.2 BTC, 2x 杠杆
        res = self.broker.place_order(symbol="BTC/USDT", side="BUY", volume=0.2, leverage=2.0)
        self.assertTrue(res["success"])
        self.assertIn("order_id", res)

        snap = self.broker.get_account_snapshot()
        self.assertEqual(snap["positions_count"], 1)
        self.assertLess(snap["available_cash"], 100000.0)
        self.assertGreater(snap["margin_used"], 0.0)

        pos = snap["positions"][0]
        self.assertEqual(pos["side"], "LONG")
        self.assertEqual(pos["volume"], 0.2)
        self.assertGreater(pos["liquidation_price"], 0.0)

    def test_close_position(self):
        self.broker.place_order(symbol="ETH/USDT", side="SELL", volume=1.0, leverage=2.0)
        snap = self.broker.get_account_snapshot()
        pos_id = snap["positions"][0]["position_id"]

        close_res = self.broker.close_position(pos_id)
        self.assertTrue(close_res["success"])

        snap_after = self.broker.get_account_snapshot()
        self.assertEqual(snap_after["positions_count"], 0)
        self.assertIn("realized_pnl", snap_after)

    def test_insufficient_margin(self):
        # 尝试开仓 1000 BTC（保证金超限）
        res = self.broker.place_order(symbol="BTC/USDT", side="BUY", volume=1000.0, leverage=1.0)
        self.assertFalse(res["success"])
        self.assertIn("可用保证金不足", res["error"])

    def test_account_reset(self):
        self.broker.place_order(symbol="SOL/USDT", side="BUY", volume=10.0)
        self.broker.reset_account(initial_cash=50000.0)
        snap = self.broker.get_account_snapshot()
        self.assertEqual(snap["available_cash"], 50000.0)
        self.assertEqual(snap["positions_count"], 0)

    def test_auto_trade_step(self):
        step_res = self.broker.auto_trade_step(symbol="BTC/USDT")
        self.assertIn("laya_action", step_res)
        self.assertIn("price", step_res)
        self.assertIn("rsi", step_res)

if __name__ == "__main__":
    unittest.main()
