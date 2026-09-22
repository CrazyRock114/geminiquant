"""
OmniQuant - Industrial Multi-Asset Quantitative Trading Platform
Integrates System 2 TradingAgents, System 1 Laya, OpenBB Data, and System 0 Execution
"""
import asyncio
import argparse
import logging
import time
from typing import Dict, Any

from config.settings import settings
from core.models.types import AssetClass, OrderSide, OrderType
from core.models.order import OrderRequest
from data.domestic_feed import domestic_feed
from data.crypto_feed import crypto_feed
from data.feature_engine import feature_engine
from research.graph import research_graph
from research.memory import research_memory
from decision.state_builder import state_builder
from decision.fallback_engine import get_decision_engine
from risk.risk_manager import risk_manager
from execution.oms import oms

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("OmniQuant.Main")

class OmniQuantOrchestrator:
    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self.decision_engine = get_decision_engine()

    async def initialize(self):
        logger.info("=" * 60)
        logger.info("Initializing OmniQuant Trading Engine...")
        logger.info("Target Markets: A股, 港美股, Crypto, 黄金白银, 商品期货, 期权")
        logger.info(f"Decision Engine (System 1): {settings.decision_engine} (Device: {settings.laya_device})")
        logger.info(f"Research Engine (System 2): TradingAgents (Provider: {settings.llm_provider})")
        logger.info("=" * 60)
        await oms.initialize()

    async def run_single_asset_cycle(self, symbol: str, asset_class: AssetClass) -> Dict[str, Any]:
        """
        单次端到端交易循环：
        Tick 行情获取 -> 特征提取 -> 状态编译 -> Laya 决策 (<35ms) -> 双重风控 -> OMS 撮合
        """
        # 1. 采集实时/快照行情
        if asset_class == AssetClass.CRYPTO:
            tick = crypto_feed.fetch_ticker(symbol)
        elif asset_class in (AssetClass.COMMODITY_FUTURES, AssetClass.PRECIOUS_METALS):
            tick = domestic_feed.get_ctp_futures_snapshot(symbol)
        elif asset_class == AssetClass.EQUITY_CN:
            tick = domestic_feed.get_ashare_realtime_snapshot(symbol)
        else:
            tick = domestic_feed.get_ashare_realtime_snapshot(symbol)

        # 2. 特征工程计算
        import pandas as pd
        mock_series = pd.Series([tick.last_price * (1.0 + i * 0.002) for i in range(30)])
        rsi_val = feature_engine.calculate_rsi(mock_series)
        macd_res = feature_engine.calculate_macd(mock_series)
        bb_res = feature_engine.calculate_bollinger_bands(mock_series)

        features = {
            "rsi": rsi_val,
            "macd_hist": macd_res["hist"],
            "bb_bandwidth": bb_res["bandwidth"],
            "ofi": 0.35
        }

        # 3. 读取当前 System 2 宏观研报上下文
        macro_ctx = research_memory.get_latest_context()

        # 4. 获取账户状态
        account = oms.get_account_snapshot()

        # 5. 编译 Laya 输入状态槽
        state = state_builder.build_state(tick, features, macro_ctx, account)

        # 6. System 1 极速决策 (< 35ms)
        decision = self.decision_engine.evaluate(state)
        logger.info(
            f"[System 1 决策输出] 标的: {symbol} | 动作: {decision.action} | "
            f"置信度: {decision.confidence} | 紧迫度: {decision.urgency} | 耗时: {decision.latency_ms} ms"
        )

        # 7. 若决策需要动作，构造订单并触发前置风控拦截
        if decision.action in ("BUY", "STRONG_BUY", "SELL", "STRONG_SELL", "REDUCE"):
            side = OrderSide.BUY if "BUY" in decision.action else OrderSide.SELL
            # 基础仓位计算
            base_vol = 100.0 if asset_class == AssetClass.EQUITY_CN else (0.1 if asset_class == AssetClass.CRYPTO else 1.0)
            if decision.size_factor == "HALF":
                base_vol = max(1.0, base_vol * 0.5)

            order = OrderRequest(
                symbol=symbol,
                asset_class=asset_class,
                side=side,
                order_type=OrderType.LIMIT if decision.urgency == "PASSIVE_MAKER" else OrderType.MARKET,
                price=tick.last_price,
                volume=base_vol,
                reduce_only=(decision.action == "REDUCE")
            )

            # 前置风控双重拦截
            passed, reason = risk_manager.check_pre_trade_risk(order, decision, account, tick)
            if passed:
                report = await oms.submit_order(order)
                return {"decision": decision, "order": order, "report": report}
            else:
                logger.warning(f"[风控拦截生效] 订单已阻断: {reason}")
                return {"decision": decision, "order": order, "risk_blocked": reason}

        return {"decision": decision, "action": "HOLD"}

    async def benchmark_laya_latency(self, iterations: int = 50):
        """基准测试 Laya 极速决策引擎的延迟与分布"""
        logger.info(f"Running Laya Latency Benchmark ({iterations} iterations)...")
        tick = crypto_feed.fetch_ticker("BTC/USDT")
        features = {"rsi": 28.5, "macd_hist": 1.2, "bb_bandwidth": 0.045, "ofi": 0.42}
        macro_ctx = research_memory.get_latest_context()
        account = oms.get_account_snapshot()
        state = state_builder.build_state(tick, features, macro_ctx, account)

        latencies = []
        for i in range(iterations):
            t0 = time.perf_counter()
            _ = self.decision_engine.evaluate(state)
            dt = (time.perf_counter() - t0) * 1000.0
            latencies.append(dt)

        avg_lat = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]

        logger.info("=" * 60)
        logger.info(f"Laya Benchmark Results ({iterations} runs):")
        logger.info(f"Avg Latency : {avg_lat:.2f} ms")
        logger.info(f"Min Latency : {min_lat:.2f} ms")
        logger.info(f"P95 Latency : {p95_lat:.2f} ms")
        logger.info(f"Max Latency : {max_lat:.2f} ms")
        logger.info("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description="OmniQuant Trading Platform")
    parser.add_argument("--mode", type=str, default="demo", choices=["demo", "benchmark", "research", "paper"],
                        help="Operating mode")
    args = parser.parse_args()

    orchestrator = OmniQuantOrchestrator(paper_trading=True)
    await orchestrator.initialize()

    if args.mode == "benchmark":
        await orchestrator.benchmark_laya_latency(iterations=100)
    elif args.mode == "research":
        logger.info("Triggering System 2 TradingAgents Deliberation...")
        res = research_graph.run_committee_deliberation("AU2412", {})
        print("\n--- TradingAgents Investment Committee Report ---")
        import pprint
        pprint.pprint(res)
    elif args.mode in ("demo", "paper"):
        # 演示 6 大资产类别的端到端循环
        assets = [
            ("600519.SH (贵州茅台)", AssetClass.EQUITY_CN),
            ("AAPL.US (苹果)", AssetClass.EQUITY_US_HK),
            ("BTC/USDT", AssetClass.CRYPTO),
            ("AU2412 (沪金期货)", AssetClass.PRECIOUS_METALS),
            ("RB2501 (螺纹钢)", AssetClass.COMMODITY_FUTURES),
            ("10005101 (50ETF购10月2600)", AssetClass.OPTIONS)
        ]

        logger.info("\n>>> 正在执行全资产端到端决策与模拟撮合循环 <<<\n")
        for symbol, asset_class in assets:
            logger.info(f"\n--- Processing Asset: {symbol} [{asset_class.value}] ---")
            await orchestrator.run_single_asset_cycle(symbol, asset_class)
            await asyncio.sleep(0.1)

        # 打印账户资金快照
        acc = oms.get_account_snapshot()
        logger.info("\n" + "=" * 60)
        logger.info("--- OmniQuant 统一账户资金与持仓快照 ---")
        logger.info(f"动态总资产 : {acc.total_equity:.2f} {acc.currency}")
        logger.info(f"可用现金   : {acc.available_cash:.2f} {acc.currency}")
        logger.info(f"持仓数量   : {len(acc.positions)} 个品种")
        for sym, pos in acc.positions.items():
            logger.info(f"  - [{pos.asset_class.value}] {sym}: 持仓 {pos.volume} @ 均价 {pos.avg_open_price:.2f}")
        logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
