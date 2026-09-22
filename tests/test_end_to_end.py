"""
End-to-End Multi-Asset Integration Test for OmniQuant
Tests Tick -> Feature Engine -> State Builder -> Laya Gating -> Risk Manager -> OMS Execution
"""
import unittest
from main import OmniQuantOrchestrator
from core.models.types import AssetClass, OrderStatus

class TestOmniQuantEndToEnd(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.orchestrator = OmniQuantOrchestrator(paper_trading=True)
        await self.orchestrator.initialize()

    async def test_multi_asset_trading_cycles(self):
        test_assets = [
            ("BTC/USDT", AssetClass.CRYPTO),
            ("AU2412", AssetClass.PRECIOUS_METALS),
            ("RB2501", AssetClass.COMMODITY_FUTURES),
            ("600519.SH", AssetClass.EQUITY_CN),
            ("AAPL.US", AssetClass.EQUITY_US_HK),
            ("10005101", AssetClass.OPTIONS)
        ]

        for symbol, asset_class in test_assets:
            with self.subTest(symbol=symbol, asset_class=asset_class):
                result = await self.orchestrator.run_single_asset_cycle(symbol, asset_class)
                self.assertIn("decision", result)
                decision = result["decision"]
                self.assertIsNotNone(decision.action)
                self.assertLess(decision.latency_ms, 50.0)

                # 如果有报单生成，验证风控或撮合报告
                if "report" in result:
                    report = result["report"]
                    self.assertEqual(report.status, OrderStatus.FILLED)
                    self.assertGreater(report.filled_price, 0.0)
                    self.assertGreater(report.commission, 0.0)

    async def test_laya_benchmark_execution(self):
        # 运行小规模基准测试验证统计逻辑
        await self.orchestrator.benchmark_laya_latency(iterations=10)

if __name__ == "__main__":
    unittest.main()
