"""
OmniQuant Market-Specific Compliance & Microstructure Guard
Enforces trading rules for A-Shares (T+1, Limit Up/Down), Commodity Futures, Crypto, and Options
"""
from typing import Tuple, Optional
import logging
from core.models.types import AssetClass, OrderSide
from core.models.order import OrderRequest, Position, AccountBalance
from core.models.market_data import TickData

logger = logging.getLogger("OmniQuant.MarketRulesGuard")

class MarketRulesGuard:
    @staticmethod
    def validate_ashare_t_plus_1(order: OrderRequest, position: Optional[Position]) -> Tuple[bool, str]:
        """A 股 T+1 卖出规则核验：只能卖出昨日及之前结算的可用持仓"""
        if order.asset_class != AssetClass.EQUITY_CN or order.side != OrderSide.SELL:
            return True, "Passed"

        if not position or position.available_volume < order.volume:
            avail = position.available_volume if position else 0.0
            msg = f"[A股 T+1 违规拦截] 试图卖出 {order.symbol} 数量 {order.volume}，但可用结算持仓仅为 {avail}"
            logger.warning(msg)
            return False, msg

        return True, "Passed"

    @staticmethod
    def validate_price_limits(order: OrderRequest, tick: TickData) -> Tuple[bool, str]:
        """A 股与国内期货涨跌停板挂单保护：涨停板禁止挂买单，跌停板禁止挂卖单"""
        if order.asset_class in (AssetClass.EQUITY_CN, AssetClass.COMMODITY_FUTURES):
            if tick.upper_limit_price and order.side == OrderSide.BUY and order.price >= tick.upper_limit_price:
                msg = f"[涨停板拦截] 标的 {order.symbol} 已触及涨停价 {tick.upper_limit_price}，禁止追高买入"
                logger.warning(msg)
                return False, msg

            if tick.lower_limit_price and order.side == OrderSide.SELL and order.price <= tick.lower_limit_price:
                msg = f"[跌停板拦截] 标的 {order.symbol} 已触及跌停价 {tick.lower_limit_price}，禁止无效挂单"
                logger.warning(msg)
                return False, msg

        return True, "Passed"

    @staticmethod
    def validate_crypto_leverage(order: OrderRequest, account: AccountBalance, max_leverage: float = 5.0) -> Tuple[bool, str]:
        """Crypto 合约杠杆与强平缓冲检查"""
        if order.asset_class == AssetClass.CRYPTO:
            order_nominal = order.price * order.volume
            projected_margin = account.margin_occupied + (order_nominal / max_leverage)
            if projected_margin > account.total_equity * 0.85:
                msg = f"[Crypto 杠杆超限] 拟开仓保证金超限，预估总占用达 {projected_margin:.2f} > 账户85%安全线"
                logger.warning(msg)
                return False, msg

        return True, "Passed"

    @staticmethod
    def validate_options_naked_short(order: OrderRequest, position: Optional[Position]) -> Tuple[bool, str]:
        """期权裸卖空严格禁止（严禁裸卖空看涨期权 Naked Short Call）"""
        if order.asset_class == AssetClass.OPTIONS and order.side == OrderSide.SELL:
            # 若不是以平仓为目的的卖出（例如无持仓或者反向做空）
            if not position or position.volume < order.volume:
                msg = f"[期权裸卖空拦截] 严禁对 {order.symbol} 进行裸卖空 (Naked Short Option)"
                logger.warning(msg)
                return False, msg

        return True, "Passed"

# Global singleton
market_rules_guard = MarketRulesGuard()
