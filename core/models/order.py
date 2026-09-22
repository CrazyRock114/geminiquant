"""
OmniQuant Order, Position, and Account Models (QIFI Compatible)
"""
from datetime import datetime, timezone
from typing import Optional, Dict
import uuid
from pydantic import BaseModel, Field
from core.models.types import AssetClass, OrderSide, OrderType, OrderStatus

class OrderRequest(BaseModel):
    order_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str
    asset_class: AssetClass
    side: OrderSide
    order_type: OrderType = OrderType.LIMIT
    price: float
    volume: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tag: str = "laya_signal"
    reduce_only: bool = False

class OrderReport(BaseModel):
    order_id: str
    broker_order_id: Optional[str] = None
    symbol: str
    asset_class: AssetClass
    side: OrderSide
    status: OrderStatus
    requested_price: float
    requested_volume: float
    filled_price: float = 0.0
    filled_volume: float = 0.0
    commission: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None

class Position(BaseModel):
    symbol: str
    asset_class: AssetClass
    side: OrderSide  # BUY for Long, SELL for Short
    volume: float = 0.0
    available_volume: float = 0.0  # T+1 可用头寸
    avg_open_price: float = 0.0
    last_price: float = 0.0
    margin_occupied: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    delta: float = 0.0  # 期权 Delta 敞口

    @property
    def market_value(self) -> float:
        return self.volume * self.last_price

class AccountBalance(BaseModel):
    account_id: str = "default_account"
    currency: str = "CNY"  # or USD / USDT
    total_equity: float = 1000000.0  # 初始或当前动态总资产
    available_cash: float = 1000000.0
    margin_occupied: float = 0.0
    initial_equity: float = 1000000.0
    peak_equity: float = 1000000.0
    daily_start_equity: float = 1000000.0
    positions: Dict[str, Position] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current_drawdown_pct(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, (self.peak_equity - self.total_equity) / self.peak_equity * 100.0)

    @property
    def daily_drawdown_pct(self) -> float:
        if self.daily_start_equity <= 0:
            return 0.0
        return max(0.0, (self.daily_start_equity - self.total_equity) / self.daily_start_equity * 100.0)

    @property
    def margin_ratio(self) -> float:
        if self.total_equity <= 0:
            return 1.0
        return self.margin_occupied / self.total_equity
