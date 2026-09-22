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

class DataMode(str, Enum):
    LIVE_FEED = "LIVE_FEED"               # 交易所实时生产行情 (直连 WebSocket / CTP 柜台)
    HISTORICAL = "HISTORICAL"             # 历史盘后日K/分钟K线 (交易所已定盘收盘数据)
    SIMULATED = "SIMULATED"               # 模拟撮合/仿真环境数据 (如 SimNow / 测试网)
    DEMO_FIXTURE = "DEMO_FIXTURE"         # 演示测试样板 (离线沙盘调试，严禁直接用于真金白银实盘)

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
