"""
OmniQuant Core Enums and Type Definitions
"""
from enum import Enum

class AssetClass(str, Enum):
    EQUITY_CN = "EQUITY_CN"               # A股
    EQUITY_US_HK = "EQUITY_US_HK"         # 港美股
    CRYPTO = "CRYPTO"                     # 加密货币
    COMMODITY_FUTURES = "COMMODITY_FUTURES" # 商品期货
    PRECIOUS_METALS = "PRECIOUS_METALS"   # 黄金白银/贵金属
    OPTIONS = "OPTIONS"                   # 期权 (ETF期权、商品期权、美股期权)

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderStatus(str, Enum):
    PENDING_SUBMIT = "PENDING_SUBMIT"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"

class MarketRegime(str, Enum):
    BULL_EXPANSION = "BULL_EXPANSION"     # 强多头扩张
    BEAR_CONTRACTION = "BEAR_CONTRACTION" # 空头收缩
    RANGE_BOUND = "RANGE_BOUND"           # 震荡洗盘
    HIGH_VOLATILITY = "HIGH_VOLATILITY"   # 剧烈高波
    DEFENSIVE = "DEFENSIVE"               # 防御避险

class ActionType(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    STRONG_SELL = "STRONG_SELL"
    CANCEL_ALL = "CANCEL_ALL"

class UrgencyLevel(str, Enum):
    PASSIVE_MAKER = "PASSIVE_MAKER"
    AGGRESSIVE_TAKER = "AGGRESSIVE_TAKER"
    SCHEDULED_TWAP = "SCHEDULED_TWAP"
