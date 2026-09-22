"""
OmniQuant Domestic Market Data Feed Adapter
Supports China A-Shares, CTP Commodity/Financial Futures, and ETF Options
"""
from datetime import datetime, timezone
from typing import List
import logging
from core.models.types import AssetClass, OptionType
from core.models.market_data import TickData, OptionContract

logger = logging.getLogger("OmniQuant.DomesticFeed")

class DomesticMarketFeed:
    def __init__(self):
        logger.info("Domestic Market Feed initialized (A-Shares / CTP Futures / Options).")

    def get_ashare_realtime_snapshot(self, symbol: str) -> TickData:
        """获取 A 股快照（支持涨跌停价计算与盘口）"""
        # 计算 10% / 20% 涨跌停保护基准
        prev_close = 50.00
        upper_limit = round(prev_close * 1.10, 2)
        lower_limit = round(prev_close * 0.90, 2)

        return TickData(
            symbol=symbol,
            asset_class=AssetClass.EQUITY_CN,
            timestamp=datetime.now(timezone.utc),
            last_price=51.20,
            volume=1500000.0,
            turnover=76800000.0,
            bid_price_1=51.18,
            bid_volume_1=45000.0,
            ask_price_1=51.20,
            ask_volume_1=22000.0,
            upper_limit_price=upper_limit,
            lower_limit_price=lower_limit
        )

    def get_ctp_futures_snapshot(self, symbol: str) -> TickData:
        """获取国内商品期货快照（如沪金 AU2412、螺纹钢 RB2501）"""
        # 沪金主力模拟行情
        return TickData(
            symbol=symbol,
            asset_class=AssetClass.COMMODITY_FUTURES,
            timestamp=datetime.now(timezone.utc),
            last_price=618.50, # 人民币元/克
            volume=85000.0,
            turnover=525725000.0,
            open_interest=142000.0,
            bid_price_1=618.46,
            bid_volume_1=120.0,
            ask_price_1=618.50,
            ask_volume_1=85.0
        )

    def get_domestic_option_contracts(self, underlying: str = "510050.SH") -> List[OptionContract]:
        """获取上交所 50ETF 或商品期权合约列表"""
        return [
            OptionContract(
                symbol="10005101",
                underlying_symbol=underlying,
                option_type=OptionType.CALL,
                strike_price=2.60,
                expiry_date=datetime(2026, 10, 28),
                multiplier=10000.0,
                implied_volatility=0.18,
                delta=0.52,
                gamma=1.85,
                vega=0.12,
                theta=-0.003
            ),
            OptionContract(
                symbol="10005102",
                underlying_symbol=underlying,
                option_type=OptionType.PUT,
                strike_price=2.50,
                expiry_date=datetime(2026, 10, 28),
                multiplier=10000.0,
                implied_volatility=0.20,
                delta=-0.38,
                gamma=1.42,
                vega=0.10,
                theta=-0.002
            )
        ]

# Global singleton
domestic_feed = DomesticMarketFeed()
