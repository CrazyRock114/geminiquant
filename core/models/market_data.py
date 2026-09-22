"""
OmniQuant Market Data Models (QIFI Compatible)
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from core.models.types import AssetClass, OptionType, DataMode

class TickData(BaseModel):
    symbol: str
    asset_class: AssetClass
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_price: float
    volume: float = 0.0
    turnover: float = 0.0
    open_interest: float = 0.0  # 期货/期权持仓量
    bid_price_1: Optional[float] = None
    bid_volume_1: Optional[float] = None
    ask_price_1: Optional[float] = None
    ask_volume_1: Optional[float] = None
    upper_limit_price: Optional[float] = None  # 涨停板
    lower_limit_price: Optional[float] = None  # 跌停板
    data_mode: DataMode = DataMode.DEMO_FIXTURE
    data_source: str = "internal"
    quality_warning: Optional[str] = None
    extra: Dict[str, float] = Field(default_factory=dict)

class BarData(BaseModel):
    symbol: str
    asset_class: AssetClass
    timestamp: datetime
    interval: str = "1m"  # 1m, 5m, 15m, 1h, 1d
    open: float
    high: float
    low: float
    close: float
    volume: float
    turnover: float = 0.0
    open_interest: float = 0.0
    data_mode: DataMode = DataMode.HISTORICAL
    data_source: str = "internal"
    quality_warning: Optional[str] = None

class OrderBook(BaseModel):
    symbol: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bids: List[List[float]] = Field(default_factory=list, description="[[price, volume], ...]")
    asks: List[List[float]] = Field(default_factory=list, description="[[price, volume], ...]")

    @property
    def mid_price(self) -> float:
        if self.bids and self.asks:
            return (self.bids[0][0] + self.asks[0][0]) / 2.0
        return 0.0

    @property
    def orderbook_imbalance(self) -> float:
        """订单簿不平衡度 (OFI): (bid_vol - ask_vol) / (bid_vol + ask_vol)"""
        bid_vol = sum(v for _, v in self.bids[:5]) if self.bids else 0.0
        ask_vol = sum(v for _, v in self.asks[:5]) if self.asks else 0.0
        total = bid_vol + ask_vol
        return (bid_vol - ask_vol) / total if total > 0 else 0.0

class OptionContract(BaseModel):
    symbol: str
    underlying_symbol: str
    option_type: OptionType
    strike_price: float
    expiry_date: datetime
    multiplier: float = 10000.0  # e.g., 50ETF options is 10000
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    vega: Optional[float] = None
    theta: Optional[float] = None
    rho: Optional[float] = None

class OptionChain(BaseModel):
    underlying_symbol: str
    underlying_price: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    contracts: List[OptionContract] = Field(default_factory=list)
