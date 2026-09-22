"""
OmniQuant Central Order Management System (OMS)
Routes multi-asset orders to designated brokers, maintains order state machines, and audits execution.
"""
from typing import Dict
import logging
from core.models.types import AssetClass
from core.models.order import OrderRequest, OrderReport, AccountBalance
from execution.base_broker import BaseBroker
from execution.simulated_broker import SimulatedBroker
from execution.crypto_broker import CryptoBroker
from execution.ctp_broker import CTPBroker

logger = logging.getLogger("OmniQuant.OMS")

class OrderManagementSystem:
    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self.sim_broker = SimulatedBroker()
        self.crypto_broker = CryptoBroker()
        self.ctp_broker = CTPBroker()

        self.orders: Dict[str, OrderReport] = {}
        self.account = self.sim_broker.account

    async def initialize(self):
        await self.sim_broker.connect()
        if not self.paper_trading:
            await self.crypto_broker.connect()
            await self.ctp_broker.connect()
        logger.info(f"OMS initialized (PaperTrading: {self.paper_trading}).")

    def _select_broker(self, asset_class: AssetClass) -> BaseBroker:
        """根据资产类型与交易模式路由经纪商通道"""
        if self.paper_trading:
            return self.sim_broker

        if asset_class == AssetClass.CRYPTO:
            return self.crypto_broker
        elif asset_class in (AssetClass.COMMODITY_FUTURES, AssetClass.OPTIONS):
            return self.ctp_broker
        return self.sim_broker

    async def submit_order(self, order: OrderRequest) -> OrderReport:
        broker = self._select_broker(order.asset_class)
        logger.info(f"[OMS Router] Routing order {order.order_id} ({order.symbol}) to {broker.__class__.__name__}")
        report = await broker.send_order(order)
        self.orders[order.order_id] = report
        # 刷新账户
        self.account = await broker.query_account()
        return report

    async def cancel_order(self, order_id: str, asset_class: AssetClass) -> bool:
        broker = self._select_broker(asset_class)
        return await broker.cancel_order(order_id)

    def get_account_snapshot(self) -> AccountBalance:
        return self.account

# Global singleton
oms = OrderManagementSystem()
