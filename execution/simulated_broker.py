"""
OmniQuant High-Fidelity Simulated Broker Matching Engine
Supports Multi-Asset Paper Trading, Backtesting, Slippage, and Commission Calculation
"""
from datetime import datetime, timezone
from typing import Dict
import logging
from core.models.types import AssetClass, OrderSide, OrderStatus
from core.models.order import OrderRequest, OrderReport, Position, AccountBalance
from execution.base_broker import BaseBroker

logger = logging.getLogger("OmniQuant.SimulatedBroker")

class SimulatedBroker(BaseBroker):
    def __init__(self, initial_cash: float = 1000000.0, slippage_bps: float = 5.0):
        self.account = AccountBalance(
            total_equity=initial_cash,
            available_cash=initial_cash,
            initial_equity=initial_cash,
            peak_equity=initial_cash,
            daily_start_equity=initial_cash
        )
        self.orders: Dict[str, OrderReport] = {}
        self.slippage_bps = slippage_bps # 5 bps = 0.05%
        self._connected = True

    async def connect(self) -> bool:
        self._connected = True
        logger.info("[SimBroker] Connected to simulation matching engine.")
        return True

    async def disconnect(self):
        self._connected = False
        logger.info("[SimBroker] Disconnected.")

    def _calculate_commission(self, order: OrderRequest, filled_nominal: float) -> float:
        """根据不同资产类型核算手续费与印花税"""
        if order.asset_class == AssetClass.EQUITY_CN:
            # 佣金 万2.5 + 卖方印花税 万5
            comm = filled_nominal * 0.00025
            if order.side == OrderSide.SELL:
                comm += filled_nominal * 0.0005
            return round(comm, 2)
        elif order.asset_class == AssetClass.CRYPTO:
            # Taker 费率 万5 (0.05%)
            return round(filled_nominal * 0.0005, 4)
        elif order.asset_class in (AssetClass.COMMODITY_FUTURES, AssetClass.PRECIOUS_METALS):
            # 期货万分之0.5
            return round(filled_nominal * 0.00005, 2)
        elif order.asset_class == AssetClass.OPTIONS:
            # 期权固定单张 3 元
            return round(order.volume * 3.0, 2)
        return round(filled_nominal * 0.0002, 2)

    async def send_order(self, order: OrderRequest) -> OrderReport:
        """撮合成交并实时更新账户与双向持仓"""
        slippage_mult = (1.0 + self.slippage_bps / 10000.0) if order.side == OrderSide.BUY else (1.0 - self.slippage_bps / 10000.0)
        filled_price = round(order.price * slippage_mult, 4)
        filled_nominal = filled_price * order.volume
        commission = self._calculate_commission(order, filled_nominal)

        pos = self.account.positions.get(order.symbol)
        if order.side == OrderSide.BUY:
            if not pos:
                # 建立多头新持仓
                pos = Position(
                    symbol=order.symbol,
                    asset_class=order.asset_class,
                    side=OrderSide.BUY,
                    volume=order.volume,
                    available_volume=0.0 if order.asset_class == AssetClass.EQUITY_CN else order.volume, # A股 T+1
                    avg_open_price=filled_price,
                    last_price=filled_price
                )
                self.account.positions[order.symbol] = pos
                self.account.available_cash -= (filled_nominal + commission)
            elif pos.side == OrderSide.BUY:
                # 加多仓
                total_vol = pos.volume + order.volume
                pos.avg_open_price = (pos.volume * pos.avg_open_price + filled_nominal) / total_vol
                pos.volume = total_vol
                if order.asset_class != AssetClass.EQUITY_CN:
                    pos.available_volume += order.volume
                pos.last_price = filled_price
                self.account.available_cash -= (filled_nominal + commission)
            else:
                # 平空仓 (Cover Short)
                cover_vol = min(pos.volume, order.volume)
                pnl = (pos.avg_open_price - filled_price) * cover_vol
                pos.volume -= cover_vol
                pos.realized_pnl += pnl
                self.account.available_cash += (pnl - commission)
                if pos.volume <= 0:
                    del self.account.positions[order.symbol]
        else: # SELL
            if not pos:
                # 无持仓卖出：在支持做空的市场（期货/Crypto/美股）建立空头头寸
                if order.asset_class in (AssetClass.CRYPTO, AssetClass.COMMODITY_FUTURES, AssetClass.PRECIOUS_METALS, AssetClass.EQUITY_US_HK):
                    pos = Position(
                        symbol=order.symbol,
                        asset_class=order.asset_class,
                        side=OrderSide.SELL,
                        volume=order.volume,
                        available_volume=order.volume,
                        avg_open_price=filled_price,
                        last_price=filled_price,
                        margin_occupied=filled_nominal * 0.20 # 预估 20% 保证金
                    )
                    self.account.positions[order.symbol] = pos
                    self.account.available_cash -= commission
            elif pos.side == OrderSide.BUY:
                # 平多仓
                close_vol = min(pos.volume, order.volume)
                pnl = (filled_price - pos.avg_open_price) * close_vol
                pos.volume -= close_vol
                pos.available_volume = max(0.0, pos.available_volume - close_vol)
                pos.realized_pnl += pnl
                self.account.available_cash += (filled_nominal - commission)
                if pos.volume <= 0:
                    del self.account.positions[order.symbol]
            else:
                # 加空仓
                total_vol = pos.volume + order.volume
                pos.avg_open_price = (pos.volume * pos.avg_open_price + filled_nominal) / total_vol
                pos.volume = total_vol
                pos.last_price = filled_price
                self.account.available_cash -= commission

        # 重新核算全账户总动态权益
        long_val = sum(p.volume * p.last_price for p in self.account.positions.values() if p.side == OrderSide.BUY)
        short_unrealized = sum((p.avg_open_price - p.last_price) * p.volume for p in self.account.positions.values() if p.side == OrderSide.SELL)
        self.account.total_equity = self.account.available_cash + long_val + short_unrealized
        self.account.peak_equity = max(self.account.peak_equity, self.account.total_equity)

        report = OrderReport(
            order_id=order.order_id,
            broker_order_id=f"SIM_{order.order_id}",
            symbol=order.symbol,
            asset_class=order.asset_class,
            side=order.side,
            status=OrderStatus.FILLED,
            requested_price=order.price,
            requested_volume=order.volume,
            filled_price=filled_price,
            filled_volume=order.volume,
            commission=commission,
            timestamp=datetime.now(timezone.utc)
        )
        self.orders[order.order_id] = report
        logger.info(f"[SimBroker 撮合成交] {order.symbol} {order.side} {order.volume}@{filled_price} (手续费: {commission}) 剩余可用: {self.account.available_cash:.2f}")
        return report

    async def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False

    async def query_positions(self) -> Dict[str, Position]:
        return self.account.positions

    async def query_account(self) -> AccountBalance:
        return self.account
