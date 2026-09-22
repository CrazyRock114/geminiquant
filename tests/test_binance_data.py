"""
Unit tests for BinanceDataClient
"""
import unittest
import pandas as pd
from data.binance_data import BinanceDataClient

class TestBinanceDataClient(unittest.TestCase):
    def test_clean_symbol(self):
        self.assertEqual(BinanceDataClient.clean_symbol("BTC/USDT"), "BTCUSDT")
        self.assertEqual(BinanceDataClient.clean_symbol("eth/usdt"), "ETHUSDT")
        self.assertEqual(BinanceDataClient.clean_symbol("SOL"), "SOLUSDT")
        self.assertEqual(BinanceDataClient.clean_symbol("ZEC-USDT"), "ZECUSDT")

    def test_fetch_klines_structure(self):
        # 拉取 10 根测试日K线
        df = BinanceDataClient.fetch_klines("BTC/USDT", interval="1d", limit=10)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreaterEqual(len(df), 10)
        for col in ["timestamp", "open", "high", "low", "close", "volume"]:
            self.assertIn(col, df.columns)
        # 验证数值合理性
        self.assertGreater(df["close"].iloc[-1], 1000.0)
        self.assertGreater(df["high"].iloc[-1], df["low"].iloc[-1])

    def test_fallback_generation(self):
        df = BinanceDataClient._generate_fallback_klines("ZECUSDT", "1h", 25)
        self.assertEqual(len(df), 25)
        self.assertIn("close", df.columns)
        self.assertTrue((df["high"] >= df["low"]).all())

if __name__ == "__main__":
    unittest.main()
