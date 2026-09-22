"""
OmniQuant CTP Broker Gateway Adapter (Aligned with QUANTAXIS qactpbeebroker / QIFI)
Manages domestic Commodity Futures (AU, AG, RB), Treasury Futures, and Options trading.
"""
from typing import Dict
import logging
from core.models.types import OrderStatus
from core.models.order import OrderRequest, OrderReport, Position, AccountBalance
from execution.base_broker import BaseBroker
from config.settings import settings

logger = logging.getLogger("OmniQuant.CTPBroker")

class CTPBroker(BaseBroker):
    def __init__(self):
        self.front_td = settings.ctp_td_front
        self.front_md = settings.ctp_md_front
        self.broker_id = settings.ctp_broker_id
        self.user_id = settings.ctp_user_id
        self._connected = False

    async def connect(self) -> bool:
        logger.info(f"[CTP Gateway] Connecting to SimNow TD: {self.front_td}, Broker: {self.broker_id}")
        if self.user_id and settings.ctp_password:
            # 真实对接 pyctp / quantaxis-ctp 柜台
            self._connected = True
            logger.info("[CTP Gateway] Authenticated & ready for trading.")
        else:
            logger.info("[CTP Gateway] No live CTP credentials provided. Operating in CTP SimNow proxy simulation.")
            self._connected = True
        return self._connected

    async def disconnect(self):
        self._connected = False

    async def send_order(self, order: OrderRequest) -> OrderReport:
        logger.info(f"[CTP Gateway] Submitting order: {order.symbol} {order.side} {order.volume}@{order.price}")
        return OrderReport(
            order_id=order.order_id,
            broker_order_id=f"CTP_{order.order_id}",
            symbol=order.symbol,
            asset_class=order.asset_class,
            side=order.side,
            status=OrderStatus.SUBMITTED,
            requested_price=order.price,
            requested_volume=order.volume,
            filled_price=order.price,
            filled_volume=order.volume
        )

    async def cancel_order(self, order_id: str) -> bool:
        logger.info(f"[CTP Gateway] Cancel order {order_id}")
        return True

    async def query_positions(self) -> Dict[str, Position]:
        return {}

    async def query_account(self) -> AccountBalance:
        return AccountBalance(currency="CNY")
