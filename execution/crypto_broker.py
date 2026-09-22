"""
OmniQuant Live Crypto Execution Broker (CCXT)
"""
import ccxt
from typing import Dict
import logging
from core.models.types import OrderSide, OrderType, OrderStatus
from core.models.order import OrderRequest, OrderReport, Position, AccountBalance
from execution.base_broker import BaseBroker
from config.settings import settings

logger = logging.getLogger("OmniQuant.CryptoBroker")

class CryptoBroker(BaseBroker):
    def __init__(self):
        self.exchange = None
        self._connected = False

    async def connect(self) -> bool:
        try:
            exchange_class = getattr(ccxt, settings.crypto_exchange)
            self.exchange = exchange_class({
                "apiKey": settings.crypto_api_key or "",
                "secret": settings.crypto_secret or "",
                "enableRateLimit": True,
            })
            if settings.crypto_testnet and hasattr(self.exchange, "set_sandbox_mode"):
                self.exchange.set_sandbox_mode(True)
            self._connected = True
            logger.info(f"[CryptoBroker] Connected to {settings.crypto_exchange} (Testnet: {settings.crypto_testnet})")
            return True
        except Exception as e:
            logger.error(f"[CryptoBroker] Connection error: {e}")
            return False

    async def disconnect(self):
        self._connected = False

    async def send_order(self, order: OrderRequest) -> OrderReport:
        if not self.exchange or not settings.crypto_api_key:
            logger.warning("[CryptoBroker] Live credentials not set, simulating order submission.")
            return OrderReport(
                order_id=order.order_id,
                broker_order_id=f"CRYPTO_SIM_{order.order_id}",
                symbol=order.symbol,
                asset_class=order.asset_class,
                side=order.side,
                status=OrderStatus.FILLED,
                requested_price=order.price,
                requested_volume=order.volume,
                filled_price=order.price,
                filled_volume=order.volume
            )

        try:
            side_str = "buy" if order.side == OrderSide.BUY else "sell"
            type_str = "limit" if order.order_type == OrderType.LIMIT else "market"
            ccxt_order = self.exchange.create_order(
                symbol=order.symbol,
                type=type_str,
                side=side_str,
                amount=order.volume,
                price=order.price
            )
            return OrderReport(
                order_id=order.order_id,
                broker_order_id=str(ccxt_order.get("id")),
                symbol=order.symbol,
                asset_class=order.asset_class,
                side=order.side,
                status=OrderStatus.SUBMITTED,
                requested_price=order.price,
                requested_volume=order.volume
            )
        except Exception as e:
            logger.error(f"[CryptoBroker] Order error: {e}")
            return OrderReport(
                order_id=order.order_id,
                symbol=order.symbol,
                asset_class=order.asset_class,
                side=order.side,
                status=OrderStatus.REJECTED,
                requested_price=order.price,
                requested_volume=order.volume,
                error_message=str(e)
            )

    async def cancel_order(self, order_id: str) -> bool:
        return True

    async def query_positions(self) -> Dict[str, Position]:
        return {}

    async def query_account(self) -> AccountBalance:
        return AccountBalance(currency="USDT")
