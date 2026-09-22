"""
OmniQuant Central Pre-Trade Risk Manager
Implements Dual-Gate Verification:
1. Fast AI Gating (Laya Probability Risk Check)
2. Hard-coded Deterministic Boundary Check (Drawdown, Margin, Position limits, Slippage)
"""
from typing import Tuple, Optional
import logging
from core.models.types import OrderSide
from core.models.order import OrderRequest, AccountBalance
from core.models.market_data import TickData
from decision.schema import DecisionResult
from risk.market_rules_guard import market_rules_guard
from config.settings import settings

logger = logging.getLogger("OmniQuant.RiskManager")

class RiskManager:
    def __init__(self):
        self.limits = settings.risk
        logger.info(f"Risk Manager initialized with max_daily_dd={self.limits.max_account_drawdown_pct}%, max_pos={self.limits.max_position_ratio_pct}%")

    def check_pre_trade_risk(
        self,
        order: OrderRequest,
        decision: DecisionResult,
        account: AccountBalance,
        tick: Optional[TickData] = None
    ) -> Tuple[bool, str]:
        """
        前置硬核风控全项核验：任何一项未通过即刻熔断并返回拒绝原因
        """
        # 1. 第一道防线：Laya 极速概率决策初筛
        if not decision.risk_passed:
            msg = f"[Laya风控否决] 决策引擎判定 risk_passed=False (Confidence: {decision.confidence})"
            logger.warning(msg)
            return False, msg

        # 2. 第二道防线：账户日内最大回撤物理熔断 (Circuit Breaker)
        if account.daily_drawdown_pct >= self.limits.max_account_drawdown_pct:
            # 此时仅允许平仓单 (reduce_only)，严禁开新仓
            if not order.reduce_only:
                msg = f"[账户回撤熔断] 当日回撤已达 {account.daily_drawdown_pct:.2f}% >= {self.limits.max_account_drawdown_pct}%, 强制触发熔断锁死，禁止任何开仓"
                logger.critical(msg)
                return False, msg

        # 3. 单个标的持仓权重集中度检查 (仅对买入加仓生效)
        order_nominal_value = order.price * order.volume
        current_pos = account.positions.get(order.symbol)
        current_pos_value = current_pos.market_value if current_pos else 0.0

        if order.side == OrderSide.BUY and not order.reduce_only and account.total_equity > 0:
            projected_pos_value = current_pos_value + order_nominal_value
            projected_weight_pct = (projected_pos_value / account.total_equity) * 100.0
            if projected_weight_pct > self.limits.max_position_ratio_pct:
                msg = f"[集中度超限] 标的 {order.symbol} 预计仓位占比 {projected_weight_pct:.1f}% 超过上限 {self.limits.max_position_ratio_pct}%"
                logger.warning(msg)
                return False, msg

        # 4. 可用资金是否充足检查 (仅对买入加仓生效)
        if order.side == OrderSide.BUY and not order.reduce_only and order_nominal_value > account.available_cash:
            msg = f"[资金不足] 拟下单金额 {order_nominal_value:.2f} > 可用资金 {account.available_cash:.2f}"
            logger.warning(msg)
            return False, msg

        # 5. 特化市场规则核验（T+1、涨跌停、期权裸空）
        if tick is not None:
            passed, err = market_rules_guard.validate_price_limits(order, tick)
            if not passed:
                return False, err

        passed, err = market_rules_guard.validate_ashare_t_plus_1(order, current_pos)
        if not passed:
            return False, err

        passed, err = market_rules_guard.validate_options_naked_short(order, current_pos)
        if not passed:
            return False, err

        passed, err = market_rules_guard.validate_crypto_leverage(order, account, self.limits.max_leverage)
        if not passed:
            return False, err

        # 全项通过
        logger.info(f"[风控放行] 订单 {order.order_id} ({order.symbol} {order.side} {order.volume}@{order.price}) 全项指标通过")
        return True, "PASSED"

# Global singleton
risk_manager = RiskManager()
